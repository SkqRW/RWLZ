"""
LLVM Code Generator for RWLZ Language
Generates LLVM IR from the AST.

Responsibility: Convert AST nodes into LLVM IR instructions.
Does NOT handle compilation to machine code or executable generation.
"""

from llvmlite import ir
from llvmlite import binding as llvm
from typing import Dict, Optional, Any
from Utils.model import *
from Utils.errors import error
from Semantic.typesys import BaseType, RWLZType, TypeSystem
from Semantic.symtab import SymbolTable
from LLVM.builtins import BuiltInFunctions


class LLVMCodeGenerator:
    """
    Generates LLVM IR code from the AST.
    
    Responsibilities:
    - Convert AST nodes to LLVM IR instructions
    - Manage LLVM module, functions, and basic blocks
    - Handle type mapping between RWLZ and LLVM types
    - Generate code for expressions, statements, and declarations
    
    Does NOT handle:
    - Compilation to object files
    - Linking to executables
    - Platform-specific build configurations
    """
    
    def __init__(self, symtab: Optional[SymbolTable] = None):
        # Initialize LLVM native target and assembly printer
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        
        # Create LLVM module
        self.module = ir.Module(name="rwlz_module")
        self.module.triple = llvm.get_default_triple()
        
        # IR builder for generating instructions
        self.builder: Optional[ir.IRBuilder] = None
        
        # Maps variable names to their LLVM alloca instructions
        self.variables: Dict[str, ir.AllocaInstr] = {}
        
        # Current function being generated
        self.current_function: Optional[ir.Function] = None

        self.symtab = symtab
        self.type_map = {
            BaseType.INT: ir.IntType(32),
            BaseType.FLOAT: ir.DoubleType(), 
            BaseType.BOOL: ir.IntType(1),
            BaseType.CHAR: ir.IntType(8),
            BaseType.VOID: ir.VoidType(),
            # STRING is represented as i8* (pointer to char array)
            BaseType.STRING: ir.IntType(8).as_pointer()
        }
        
        # Stack to track loop blocks for break/continue statements
        # Each entry is a tuple: (continue_block, break_block)
        self.loop_stack: list = []
        
        # Initialize built-in runtime functions
        self.builtins = BuiltInFunctions(self.module)
    
    def _get_llvm_type(self, rwlz_type) -> ir.Type:
        """
        Convert RWLZ type to LLVM type.
        
        Args:
            rwlz_type: Either a RWLZType object or a Type AST node
            
        Returns:
            Corresponding LLVM IR type
            
        Leverages TypeSystem.parse_type_name() for consistency with semantic analysis.
        """
        if isinstance(rwlz_type, RWLZType):
            base_type = rwlz_type.base_type
        else:
            # Use TypeSystem to parse the type name (reuses existing logic)
            parsed_type = TypeSystem.parse_type_name(rwlz_type.name)
            base_type = parsed_type.base_type
        
        return self.type_map.get(base_type, ir.IntType(32))
    
    def generate(self, ast: Program) -> str:
        """
        Main entry point for code generation.
        
        Args:
            ast: The root Program node of the AST
            
        Returns:
            The generated LLVM IR as a string
        """
        self.visit(ast)
        return str(self.module)
    
    def get_module(self) -> ir.Module:
        """
        Get the LLVM module for further processing.
        
        Returns:
            The generated LLVM IR module
        """
        return self.module
    
    def visit(self, node: Node) -> Any:
        """
        Generic visit method using the visitor pattern.
        Dispatches to appropriate visit_<NodeType> method.
        
        Args:
            node: AST node to visit
            
        Returns:
            Result from the specific visitor method
        """
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: Node):
        """
        Default visitor for unhandled node types.
        Raises NotImplementedError if no specific visitor exists.
        """
        raise NotImplementedError(f"No visitor for {node.__class__.__name__}")
    
    # =========================================================================
    # PROGRAM
    # =========================================================================
    
    def visit_Program(self, node: Program):
        """
        Visit program node and generate code for all top-level declarations.
        Currently only handles function declarations.
        """
        # Generate code for each function in the program
        for func in node.functions:
            self.visit(func)
    
    # =========================================================================
    # FUNCTIONS
    # =========================================================================
    
    def visit_NormalFunction(self, node: NormalFunction):
        """
        Generate LLVM IR for a function definition.
        
        Creates function signature, entry block, parameter allocations,
        and generates code for the function body.
        """
        # Get LLVM type for return value
        return_type = self._get_llvm_type(node.return_type)
        
        # Get LLVM types for all parameters
        param_types = [self._get_llvm_type(param.param_type) for param in node.params]
        
        # Create function type signature
        func_type = ir.FunctionType(return_type, param_types)
        
        # Create function in the module
        func = ir.Function(self.module, func_type, name=node.name)
        self.current_function = func
        
        # Create entry basic block
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        
        # Clear variable map for new function scope
        self.variables = {}
        
        # Allocate stack space for parameters and store their initial values
        for i, param in enumerate(node.params):
            param_alloca = self.builder.alloca(param_types[i], name=param.name)
            self.builder.store(func.args[i], param_alloca)
            self.variables[param.name] = param_alloca
        
        # Generate code for function body
        self.visit(node.body)
        
        # Add default return if function doesn't end with explicit return
        if not self.builder.block.is_terminated:
            if isinstance(return_type, ir.VoidType):
                self.builder.ret_void()
            else:
                # Return zero/default value for non-void functions
                self.builder.ret(ir.Constant(return_type, 0))
        
        # Clean up function-level state
        self.current_function = None
        self.builder = None
    
    # =========================================================================
    # STATEMENTS
    # =========================================================================
    
    def visit_Block(self, node: Block):
        """
        Visit a block of statements.
        Stops generating code if a terminator (return/branch) is encountered.
        """
        for stmt in node.statements:
            if self.builder.block.is_terminated:
                break  # Don't generate unreachable code after return/branch
            self.visit(stmt)
    
    def visit_VarDecl(self, node: VarDecl):
        """
        Generate code for variable declaration.
        Allocates stack space and optionally stores initial value.
        """
        # Try to get type from symbol table first (more accurate after semantic analysis)
        var_type = None
        if self.symtab:
            symbol = self.symtab.lookup_symbol(node.name)
            if symbol:
                var_type = self._get_llvm_type(symbol.symbol_type)
        
        # Fallback to AST type if symbol table lookup fails
        if var_type is None:
            var_type = self._get_llvm_type(node.var_type)
        
        # Allocate stack space for the variable
        var_alloca = self.builder.alloca(var_type, name=node.name)
        self.variables[node.name] = var_alloca
        
        # Store initial value if provided
        if node.value:
            init_value = self.visit(node.value)
            # Convert value type to match variable type if needed
            init_value = self._convert_type(init_value, var_type)
            self.builder.store(init_value, var_alloca)
    
    def visit_ArrayDecl(self, node: ArrayDecl):
        """
        Generate code for static array declaration.
        Allocates stack space for array and optionally initializes elements.
        """
        # Get element type
        element_type = self._get_llvm_type(node.var_type)
        
        # Determine array size
        if node.size:
            # Size specified explicitly
            if isinstance(node.size, Integer):
                array_size = node.size.value
            else:
                # Size is an expression, evaluate it
                size_value = self.visit(node.size)
                # For now, we only support constant sizes
                if isinstance(size_value, ir.Constant):
                    array_size = size_value.constant
                else:
                    raise Exception(f"Array size must be a constant value")
        elif node.values:
            # Size inferred from initializer list
            array_size = len(node.values)
        else:
            raise Exception(f"Array '{node.name}' must have either size or initial values")
        
        # Create array type
        array_type = ir.ArrayType(element_type, array_size)
        
        # Allocate stack space for the array
        array_alloca = self.builder.alloca(array_type, name=node.name)
        self.variables[node.name] = array_alloca
        
        # Initialize array elements if values provided
        if node.values:
            for i, value_expr in enumerate(node.values):
                if i >= array_size:
                    break  # Don't exceed array bounds
                
                # Evaluate the initializer expression
                value = self.visit(value_expr)
                
                # Get pointer to array element using GEP (GetElementPtr)
                indices = [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), i)]
                element_ptr = self.builder.gep(array_alloca, indices, name=f"{node.name}_elem_{i}")
                
                # Store value in array element
                self.builder.store(value, element_ptr)
    
    def visit_Assignment(self, node: Assignment):
        """
        Generate code for assignment operations.
        Handles simple assignment (=), compound assignments (+=, -=, etc.),
        and increment/decrement operators (++, --).
        Supports both variable and array element assignments.
        """
        # Handle variable assignment
        if isinstance(node.target, VarLocation):
            var_name = node.target.name
            
            if var_name not in self.variables:
                raise Exception(f"Variable '{var_name}' not declared")
            
            var_ptr = self.variables[var_name]
            
            # Handle compound assignments (+=, -=, *=, /=)
            if node.operator in ['+=', '-=', '*=', '/=']:
                # Load current value from memory
                current_val = self.builder.load(var_ptr, name=var_name)
                
                # Evaluate right-hand side expression
                rhs = self.visit(node.value)
                
                # Perform the corresponding arithmetic operation
                op = node.operator[0]  # Extract operator: +, -, *, /
                if op == '+':
                    new_val = self.builder.add(current_val, rhs, name="addtmp")
                elif op == '-':
                    new_val = self.builder.sub(current_val, rhs, name="subtmp")
                elif op == '*':
                    new_val = self.builder.mul(current_val, rhs, name="multmp")
                elif op == '/':
                    new_val = self.builder.sdiv(current_val, rhs, name="divtmp")
                
                # Store result back to variable
                self.builder.store(new_val, var_ptr)
            
            # Handle simple assignment (=)
            elif node.operator == '=':
                value = self.visit(node.value)
                # Get the target variable type and convert if needed
                var_type = var_ptr.type.pointee
                value = self._convert_type(value, var_type)
                self.builder.store(value, var_ptr)
            
            # Handle increment and decrement (++, --)
            elif node.operator in ['++', '--']:
                current_val = self.builder.load(var_ptr, name=var_name)
                one = ir.Constant(current_val.type, 1)
                
                if node.operator == '++':
                    new_val = self.builder.add(current_val, one, name="inctmp")
                else:
                    new_val = self.builder.sub(current_val, one, name="dectmp")
                
                self.builder.store(new_val, var_ptr)
        
        # Handle array element assignment
        elif isinstance(node.target, ArrayLocation):
            array_name = node.target.name
            
            if array_name not in self.variables:
                raise Exception(f"Array '{array_name}' not declared")
            
            array_ptr = self.variables[array_name]
            
            # Evaluate index expression
            index = self.visit(node.target.index)
            
            # Get pointer to array element using GEP
            indices = [ir.Constant(ir.IntType(32), 0), index]
            element_ptr = self.builder.gep(array_ptr, indices, name=f"{array_name}_elem_ptr")
            
            # Handle different assignment operators
            if node.operator in ['+=', '-=', '*=', '/=']:
                # Load current value
                current_val = self.builder.load(element_ptr, name=f"{array_name}_elem")
                
                # Evaluate right-hand side
                rhs = self.visit(node.value)
                
                # Perform operation
                op = node.operator[0]
                if op == '+':
                    new_val = self.builder.add(current_val, rhs, name="addtmp")
                elif op == '-':
                    new_val = self.builder.sub(current_val, rhs, name="subtmp")
                elif op == '*':
                    new_val = self.builder.mul(current_val, rhs, name="multmp")
                elif op == '/':
                    new_val = self.builder.sdiv(current_val, rhs, name="divtmp")
                
                # Store result
                self.builder.store(new_val, element_ptr)
            
            elif node.operator == '=':
                value = self.visit(node.value)
                # Get the element type and convert if needed
                element_type = element_ptr.type.pointee
                value = self._convert_type(value, element_type)
                self.builder.store(value, element_ptr)
            
            elif node.operator in ['++', '--']:
                current_val = self.builder.load(element_ptr, name=f"{array_name}_elem")
                one = ir.Constant(current_val.type, 1)
                
                if node.operator == '++':
                    new_val = self.builder.add(current_val, one, name="inctmp")
                else:
                    new_val = self.builder.sub(current_val, one, name="dectmp")
                
                self.builder.store(new_val, element_ptr)
    
    def visit_PrintStatement(self, node: PrintStatement):
        """
        Generate code for print statement.
        Creates a format string based on the expression type and calls printf.
        """
        # Evaluate the expression to print
        value = self.visit(node.expression)
        
        # Determine format string based on LLVM type
        if isinstance(value.type, ir.IntType):
            if value.type.width == 32:  # int
                fmt = "%d\n\0"
            elif value.type.width == 1:  # bool
                fmt = "%d\n\0"
            else:  # char (8-bit)
                fmt = "%c\n\0"
        elif isinstance(value.type, ir.DoubleType):
            fmt = "%f\n\0"
        elif isinstance(value.type, ir.PointerType):
            # Check if it's a string (i8*)
            if isinstance(value.type.pointee, ir.IntType) and value.type.pointee.width == 8:
                fmt = "%s\n\0"
            else:
                fmt = "%p\n\0"  # other pointer types
        else:
            fmt = "%p\n\0"  # fallback for unknown types
        
        # Create global constant string for format
        fmt_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt)),
                              bytearray(fmt.encode("utf8")))
        global_fmt = ir.GlobalVariable(self.module, fmt_str.type, 
                                       name=self.module.get_unique_name("fmt"))
        global_fmt.linkage = 'internal'
        global_fmt.global_constant = True
        global_fmt.initializer = fmt_str
        
        # Get pointer to format string (cast to i8*)
        fmt_ptr = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        
        # Call printf with format string and value
        printf_func = self.builtins.get_function("printf")
        self.builder.call(printf_func, [fmt_ptr, value])
    
    def visit_ReturnStatement(self, node: ReturnStatement):
        """
        Generate code for return statement.
        Handles both void returns and value returns.
        """
        if node.value:
            ret_val = self.visit(node.value)
            self.builder.ret(ret_val)
        else:
            self.builder.ret_void()
    
    def visit_IfStatement(self, node: IfStatement):
        """
        Generate code for if-else statement.
        Creates basic blocks for then, else, and merge points.
        """
        # Evaluate condition expression
        cond = self.visit(node.condition)
        
        # Convert condition to i1 (boolean) if needed
        cond_bool = self._to_bool(cond)
        
        # Create basic blocks for control flow
        then_block = self.current_function.append_basic_block("if.then")
        else_block = self.current_function.append_basic_block("if.else")
        merge_block = self.current_function.append_basic_block("if.merge")
        
        # Conditional branch based on condition
        self.builder.cbranch(cond_bool, then_block, else_block)
        
        # Generate code for then branch
        self.builder.position_at_end(then_block)
        self.visit(node.then_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Generate code for else branch
        self.builder.position_at_end(else_block)
        if node.else_block:
            self.visit(node.else_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_block)
        
        # Continue code generation at merge point
        self.builder.position_at_end(merge_block)
    
    def visit_WhileStatement(self, node: WhileStatement):
        """
        Generate code for while loop.
        Creates basic blocks for condition check, loop body, and exit.
        Supports break and continue statements.
        """
        # Create basic blocks for loop structure
        cond_block = self.current_function.append_basic_block("while.cond")
        body_block = self.current_function.append_basic_block("while.body")
        end_block = self.current_function.append_basic_block("while.end")
        
        # Push loop blocks onto stack for break/continue
        # continue jumps to cond_block, break jumps to end_block
        self.loop_stack.append((cond_block, end_block))
        
        # Jump to condition check
        self.builder.branch(cond_block)
        
        # Generate condition checking block
        self.builder.position_at_end(cond_block)
        cond = self.visit(node.condition)
        cond_bool = self._to_bool(cond)  # Convert to i1
        self.builder.cbranch(cond_bool, body_block, end_block)
        
        # Generate loop body
        self.builder.position_at_end(body_block)
        self.visit(node.body)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)  # Loop back to condition
        
        # Pop loop from stack
        self.loop_stack.pop()
        
        # Continue after loop
        self.builder.position_at_end(end_block)
    
    def visit_ForStatement(self, node: ForStatement):
        """
        Generate code for for loop.
        
        Structure:
            for (init; condition; update) { body }
        
        Translates to:
            init
            while (condition) {
                body
                update
            }
        
        Supports break and continue statements.
        """
        # Execute initialization (if present)
        if node.init:
            self.visit(node.init)
        
        # Create basic blocks for loop structure
        cond_block = self.current_function.append_basic_block("for.cond")
        body_block = self.current_function.append_basic_block("for.body")
        update_block = self.current_function.append_basic_block("for.update")
        end_block = self.current_function.append_basic_block("for.end")
        
        # Push loop blocks onto stack for break/continue
        # continue jumps to update_block, break jumps to end_block
        self.loop_stack.append((update_block, end_block))
        
        # Jump to condition check
        self.builder.branch(cond_block)
        
        # Generate condition checking block
        self.builder.position_at_end(cond_block)
        if node.condition:
            cond = self.visit(node.condition)
            cond_bool = self._to_bool(cond)  # Convert to i1
            self.builder.cbranch(cond_bool, body_block, end_block)
        else:
            # No condition means infinite loop (like for(;;))
            self.builder.branch(body_block)
        
        # Generate loop body
        self.builder.position_at_end(body_block)
        self.visit(node.body)
        if not self.builder.block.is_terminated:
            self.builder.branch(update_block)
        
        # Generate update block
        self.builder.position_at_end(update_block)
        if node.update:
            self.visit(node.update)
        if not self.builder.block.is_terminated:
            self.builder.branch(cond_block)  # Loop back to condition
        
        # Pop loop from stack
        self.loop_stack.pop()
        
        # Continue after loop
        self.builder.position_at_end(end_block)
    
    def visit_BreakStatement(self, node: BreakStatement):
        """
        Generate code for break statement.
        Jumps to the end of the current loop.
        """
        if not self.loop_stack:
            raise Exception("'break' statement outside of loop")
        
        # Get the break target (end block) from the loop stack
        _, break_block = self.loop_stack[-1]
        self.builder.branch(break_block)
    
    def visit_ContinueStatement(self, node: ContinueStatement):
        """
        Generate code for continue statement.
        Jumps to the continuation point of the current loop.
        
        For while loops: jumps to condition check
        For for loops: jumps to update block
        """
        if not self.loop_stack:
            raise Exception("'continue' statement outside of loop")
        
        # Get the continue target from the loop stack
        continue_block, _ = self.loop_stack[-1]
        self.builder.branch(continue_block)
    
    # =========================================================================
    # EXPRESSIONS
    # =========================================================================
    
    def visit_BinOper(self, node: BinOper) -> ir.Value:
        """
        Generate code for binary operations.
        Handles arithmetic, comparison, logical operators, and string operations.
        Supports both integer, floating-point, and string operations.
        """
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        # Check if we're dealing with strings (i8* pointers)
        is_left_string = (isinstance(left.type, ir.PointerType) and 
                         isinstance(left.type.pointee, ir.IntType) and 
                         left.type.pointee.width == 8)
        is_right_string = (isinstance(right.type, ir.PointerType) and 
                          isinstance(right.type.pointee, ir.IntType) and 
                          right.type.pointee.width == 8)
        
        # String concatenation with +
        if node.operator == '+' and (is_left_string or is_right_string):
            # Convert non-strings to strings
            if not is_left_string:
                left = self._to_string(left)
            if not is_right_string:
                right = self._to_string(right)
            return self._concat_strings(left, right)
        
        # String comparison
        if node.operator in ['==', '!='] and is_left_string and is_right_string:
            return self._compare_strings(left, right, node.operator)
        
        # Arithmetic operations
        if node.operator == '+':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fadd(left, right, name="faddtmp")
            return self.builder.add(left, right, name="addtmp")
        
        elif node.operator == '-':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fsub(left, right, name="fsubtmp")
            return self.builder.sub(left, right, name="subtmp")
        
        elif node.operator == '*':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fmul(left, right, name="fmultmp")
            return self.builder.mul(left, right, name="multmp")
        
        elif node.operator == '/':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fdiv(left, right, name="fdivtmp")
            return self.builder.sdiv(left, right, name="divtmp")
        
        elif node.operator == '%':
            return self.builder.srem(left, right, name="modtmp")
        
        # Comparison operations
        elif node.operator == '==':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fcmp_ordered('==', left, right, name="eqtmp")
            return self.builder.icmp_signed('==', left, right, name="eqtmp")
        
        elif node.operator == '!=':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fcmp_ordered('!=', left, right, name="netmp")
            return self.builder.icmp_signed('!=', left, right, name="netmp")
        
        elif node.operator == '<':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fcmp_ordered('<', left, right, name="lttmp")
            return self.builder.icmp_signed('<', left, right, name="lttmp")
        
        elif node.operator == '<=':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fcmp_ordered('<=', left, right, name="letmp")
            return self.builder.icmp_signed('<=', left, right, name="letmp")
        
        elif node.operator == '>':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fcmp_ordered('>', left, right, name="gttmp")
            return self.builder.icmp_signed('>', left, right, name="gttmp")
        
        elif node.operator == '>=':
            if isinstance(left.type, ir.DoubleType):
                return self.builder.fcmp_ordered('>=', left, right, name="getmp")
            return self.builder.icmp_signed('>=', left, right, name="getmp")
        
        # Logical operations (&&, ||)
        # These are short-circuit logical operators, but LLVM IR doesn't have built-in
        # short-circuit evaluation, so we implement them as eager evaluation with
        # boolean conversion
        elif node.operator == '&&':
            # Convert both operands to boolean (i1) first
            left_bool = self._to_bool(left)
            right_bool = self._to_bool(right)
            # Then do logical AND
            return self.builder.and_(left_bool, right_bool, name="andtmp")
        
        elif node.operator == '||':
            # Convert both operands to boolean (i1) first
            left_bool = self._to_bool(left)
            right_bool = self._to_bool(right)
            # Then do logical OR
            return self.builder.or_(left_bool, right_bool, name="ortmp")
        
        else:
            raise Exception(f"Unknown binary operator: {node.operator}")
    
    def _to_string(self, value: ir.Value) -> ir.Value:
        """
        Convert an integer or float value to a string using sprintf.
        
        Args:
            value: LLVM value (i32, i64, double, etc.) to convert to string
            
        Returns:
            Pointer to string (i8*)
        """
        # Declare sprintf if not already declared
        if "sprintf" not in self.module.globals:
            sprintf_ty = ir.FunctionType(ir.IntType(32), [ir.IntType(8).as_pointer(), ir.IntType(8).as_pointer()], var_arg=True)
            ir.Function(self.module, sprintf_ty, name="sprintf")
        
        sprintf_func = self.module.get_global("sprintf")
        malloc_func = self.builtins.get_function("malloc")
        
        # Allocate buffer for the string (32 bytes should be enough for most numbers)
        buffer_size = ir.Constant(ir.IntType(64), 32)
        buffer = self.builder.call(malloc_func, [buffer_size], name="str_buffer")
        
        # Determine format string based on type
        if isinstance(value.type, ir.IntType):
            # Integer format: "%d"
            fmt_str = "%d\00"
            fmt_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_str)), bytearray(fmt_str.encode("utf8")))
            fmt_global = ir.GlobalVariable(self.module, fmt_const.type, name=self.module.get_unique_name("int_fmt"))
            fmt_global.linkage = 'internal'
            fmt_global.global_constant = True
            fmt_global.initializer = fmt_const
            fmt_ptr = self.builder.bitcast(fmt_global, ir.IntType(8).as_pointer())
            
            # Call sprintf(buffer, "%d", value)
            self.builder.call(sprintf_func, [buffer, fmt_ptr, value])
            
        elif isinstance(value.type, ir.DoubleType):
            # Float format: "%f"
            fmt_str = "%.2f\00"  # 2 decimal places
            fmt_const = ir.Constant(ir.ArrayType(ir.IntType(8), len(fmt_str)), bytearray(fmt_str.encode("utf8")))
            fmt_global = ir.GlobalVariable(self.module, fmt_const.type, name=self.module.get_unique_name("float_fmt"))
            fmt_global.linkage = 'internal'
            fmt_global.global_constant = True
            fmt_global.initializer = fmt_const
            fmt_ptr = self.builder.bitcast(fmt_global, ir.IntType(8).as_pointer())
            
            # Call sprintf(buffer, "%.2f", value)
            self.builder.call(sprintf_func, [buffer, fmt_ptr, value])
        else:
            raise Exception(f"Cannot convert type {value.type} to string")
        
        return buffer
    
    def _concat_strings(self, left: ir.Value, right: ir.Value) -> ir.Value:
        """
        Concatenate two strings using malloc, strcpy, and strcat.
        
        Args:
            left: First string (i8*)
            right: Second string (i8*)
            
        Returns:
            Pointer to new concatenated string (i8*)
        """
        strlen_func = self.builtins.get_function("strlen")
        malloc_func = self.builtins.get_function("malloc")
        strcpy_func = self.builtins.get_function("strcpy")
        strcat_func = self.builtins.get_function("strcat")
        
        # Get lengths of both strings
        len_left = self.builder.call(strlen_func, [left], name="len_left")
        len_right = self.builder.call(strlen_func, [right], name="len_right")
        
        # Calculate total length (left + right + 1 for null terminator)
        total_len = self.builder.add(len_left, len_right, name="total_len")
        total_len_plus_null = self.builder.add(total_len, ir.Constant(ir.IntType(64), 1), name="total_with_null")
        
        # Allocate memory for concatenated string
        new_str = self.builder.call(malloc_func, [total_len_plus_null], name="concat_str")
        
        # Copy first string
        self.builder.call(strcpy_func, [new_str, left])
        
        # Concatenate second string
        result = self.builder.call(strcat_func, [new_str, right], name="strcat_result")
        
        return result
    
    def _to_bool(self, value: ir.Value) -> ir.Value:
        """
        Convert a value to i1 (boolean) type for use in conditional branches.
        
        In C-like semantics:
        - For integers: 0 is false, non-zero is true
        - For floats: 0.0 is false, non-zero is true
        - For i1: already boolean, return as-is
        
        Args:
            value: LLVM value to convert to boolean
            
        Returns:
            i1 value suitable for conditional branches
        """
        # Already i1, no conversion needed
        if isinstance(value.type, ir.IntType) and value.type.width == 1:
            return value
        
        # Integer types: compare with 0
        if isinstance(value.type, ir.IntType):
            zero = ir.Constant(value.type, 0)
            return self.builder.icmp_signed('!=', value, zero, name="tobool")
        
        # Float types: compare with 0.0
        if isinstance(value.type, ir.DoubleType):
            zero = ir.Constant(value.type, 0.0)
            return self.builder.fcmp_ordered('!=', value, zero, name="tobool")
        
        # Pointers (like strings): compare with null
        if isinstance(value.type, ir.PointerType):
            null = ir.Constant(value.type, None)
            return self.builder.icmp_signed('!=', value, null, name="tobool")
        
        # Fallback: just return the value (might cause errors)
        return value
    
    def _convert_type(self, value: ir.Value, target_type: ir.Type) -> ir.Value:
        """
        Convert a value to a target type if necessary.
        Handles bool to int promotion and other common conversions.
        
        Args:
            value: LLVM value to convert
            target_type: Desired LLVM type
            
        Returns:
            Converted value or original if no conversion needed
        """
        # No conversion needed if types already match
        if value.type == target_type:
            return value
        
        # i1 to integer: zero-extend (false->0, true->1)
        if isinstance(value.type, ir.IntType) and value.type.width == 1:
            if isinstance(target_type, ir.IntType):
                return self.builder.zext(value, target_type, name="bool_to_int")
        
        # Integer to i1: compare with 0
        if isinstance(value.type, ir.IntType) and isinstance(target_type, ir.IntType):
            if target_type.width == 1:
                zero = ir.Constant(value.type, 0)
                return self.builder.icmp_signed('!=', value, zero, name="int_to_bool")
            # Int to int of different size
            if value.type.width < target_type.width:
                return self.builder.sext(value, target_type, name="sext")
            elif value.type.width > target_type.width:
                return self.builder.trunc(value, target_type, name="trunc")
        
        # Int to float
        if isinstance(value.type, ir.IntType) and isinstance(target_type, ir.DoubleType):
            return self.builder.sitofp(value, target_type, name="int_to_float")
        
        # Float to int
        if isinstance(value.type, ir.DoubleType) and isinstance(target_type, ir.IntType):
            return self.builder.fptosi(value, target_type, name="float_to_int")
        
        # No conversion available, return as-is (might cause error later)
        return value

    
    def _compare_strings(self, left: ir.Value, right: ir.Value, operator: str) -> ir.Value:
        """
        Compare two strings using strcmp.
        
        Args:
            left: First string (i8*)
            right: Second string (i8*)
            operator: '==' or '!='
            
        Returns:
            Boolean result (i1)
        """
        strcmp_func = self.builtins.get_function("strcmp")
        
        # Call strcmp (returns 0 if equal)
        cmp_result = self.builder.call(strcmp_func, [left, right], name="strcmp_result")
        
        # Compare result with 0
        zero = ir.Constant(ir.IntType(32), 0)
        
        if operator == '==':
            # Equal if strcmp returns 0
            return self.builder.icmp_signed('==', cmp_result, zero, name="streq")
        else:  # !=
            # Not equal if strcmp returns non-zero
            return self.builder.icmp_signed('!=', cmp_result, zero, name="strne")
    
    def visit_UnaryOper(self, node: UnaryOper) -> ir.Value:
        """
        Generate code for unary operations.
        Handles negation (-), unary plus (+), and logical not (!).
        """
        operand = self.visit(node.operand)
        
        if node.operator == '-':
            if isinstance(operand.type, ir.DoubleType):
                return self.builder.fmul(operand, ir.Constant(ir.DoubleType(), -1.0), name="fnegtmp")
            return self.builder.mul(operand, ir.Constant(operand.type, -1), name="negtmp")
        
        elif node.operator == '+':
            # Unary plus is a no-op, just return the operand
            return operand
        
        elif node.operator == '!':
            # Logical NOT: convert operand to bool, then invert
            # For integers: !x = (x == 0) ? 1 : 0
            # For floats: !x = (x == 0.0) ? 1 : 0
            
            if isinstance(operand.type, ir.IntType):
                # For integers (including i1)
                if operand.type.width == 1:
                    # Already i1, just invert with xor
                    return self.builder.xor(operand, ir.Constant(ir.IntType(1), 1), name="nottmp")
                else:
                    # Compare with 0 and return i1
                    zero = ir.Constant(operand.type, 0)
                    return self.builder.icmp_signed('==', operand, zero, name="nottmp")
            
            elif isinstance(operand.type, ir.DoubleType):
                # For floats, compare with 0.0
                zero = ir.Constant(operand.type, 0.0)
                return self.builder.fcmp_ordered('==', operand, zero, name="nottmp")
            
            else:
                # Fallback to bitwise NOT for other types
                return self.builder.not_(operand, name="nottmp")
        
        else:
            raise Exception(f"Unknown unary operator: {node.operator}")
    
    def visit_Variable(self, node: Variable) -> ir.Value:
        """
        Load and return the value of a variable.
        
        Args:
            node: Variable AST node
            
        Returns:
            LLVM value loaded from the variable's memory location
        """
        if node.name not in self.variables:
            # Provide helpful error message using symbol table if available
            if self.symtab and self.symtab.lookup_symbol(node.name):
                raise Exception(f"Variable '{node.name}' found in symbol table but not allocated in LLVM")
            raise Exception(f"Variable '{node.name}' not declared")
        
        var_ptr = self.variables[node.name]
        return self.builder.load(var_ptr, name=node.name)
    
    def visit_ArrayLocation(self, node: ArrayLocation) -> ir.Value:
        """
        Load and return the value of an array element.
        
        Args:
            node: ArrayLocation AST node (array[index])
            
        Returns:
            LLVM value loaded from the array element
        """
        if node.name not in self.variables:
            raise Exception(f"Array '{node.name}' not declared")
        
        array_ptr = self.variables[node.name]
        
        # Evaluate index expression
        index = self.visit(node.index)
        
        # Get pointer to array element using GEP (GetElementPtr)
        # First index (0) dereferences the pointer, second index accesses the element
        indices = [ir.Constant(ir.IntType(32), 0), index]
        element_ptr = self.builder.gep(array_ptr, indices, name=f"{node.name}_elem_ptr")
        
        # Load and return the element value
        return self.builder.load(element_ptr, name=f"{node.name}_elem")
    
    def visit_ArrayAccess(self, node: ArrayAccess) -> ir.Value:
        """
        Load and return the value of an array element.
        (ArrayAccess is similar to ArrayLocation)
        
        Args:
            node: ArrayAccess AST node (array[index])
            
        Returns:
            LLVM value loaded from the array element
        """
        if node.name not in self.variables:
            raise Exception(f"Array '{node.name}' not declared")
        
        array_ptr = self.variables[node.name]
        
        # Evaluate index expression
        index = self.visit(node.index)
        
        # Get pointer to array element using GEP (GetElementPtr)
        indices = [ir.Constant(ir.IntType(32), 0), index]
        element_ptr = self.builder.gep(array_ptr, indices, name=f"{node.name}_elem_ptr")
        
        # Load and return the element value
        return self.builder.load(element_ptr, name=f"{node.name}_elem")
    
    def visit_CallExpression(self, node: CallExpression) -> ir.Value:
        """
        Generate code for function call expression.
        
        Args:
            node: CallExpression AST node (func(arg1, arg2, ...))
            
        Returns:
            LLVM value returned by the function
        """
        # Look up the function in the module
        func = self.module.get_global(node.name)
        
        if func is None:
            raise Exception(f"Function '{node.name}' not declared")
        
        if not isinstance(func, ir.Function):
            raise Exception(f"'{node.name}' is not a function")
        
        # Evaluate all argument expressions
        args = []
        for i, arg_expr in enumerate(node.arguments):
            arg_value = self.visit(arg_expr)
            # Convert argument to expected type if needed
            if i < len(func.args):
                expected_type = func.args[i].type
                arg_value = self._convert_type(arg_value, expected_type)
            args.append(arg_value)
        
        # Check argument count matches
        if len(args) != len(func.args):
            raise Exception(
                f"Function '{node.name}' expects {len(func.args)} arguments, "
                f"but {len(args)} were provided"
            )
        
        # Generate the call instruction
        return self.builder.call(func, args, name=f"call_{node.name}")
    
    def visit_FunctionCallStmt(self, node: FunctionCallStmt):
        """
        Generate code for function call statement.
        Calls the function but discards the return value.
        """
        self.visit(node.call)
    
    # =========================================================================
    # LITERALS
    # =========================================================================
    
    def visit_Integer(self, node: Integer) -> ir.Constant:
        """Generate constant for integer literal"""
        return ir.Constant(ir.IntType(32), node.value)
    
    def visit_Float(self, node: Float) -> ir.Constant:
        """Generate constant for float literal"""
        return ir.Constant(ir.DoubleType(), node.value)
    
    def visit_Boolean(self, node: Boolean) -> ir.Constant:
        """Generate constant for boolean literal"""
        return ir.Constant(ir.IntType(1), 1 if node.value else 0)
    
    def visit_Char(self, node: Char) -> ir.Constant:
        """Generate constant for character literal"""
        return ir.Constant(ir.IntType(8), ord(node.value))
    
    def visit_String(self, node: String) -> ir.Value:
        """
        Generate constant global string and return pointer to it.
        
        Args:
            node: String AST node with the string value
            
        Returns:
            LLVM pointer (i8*) to the global constant string
        """
        # Process escape sequences properly
        string_value = node.value
        
        # Replace escape sequences with their actual characters
        escape_map = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            '\\\\': '\\',
            '\\"': '"',
            "\\'": "'",
            '\\0': '\0',
            '\\a': '\a',
            '\\b': '\b',
            '\\f': '\f',
            '\\v': '\v',
            '\\e': '\x1b'
        }
        
        for escape_seq, actual_char in escape_map.items():
            string_value = string_value.replace(escape_seq, actual_char)
        
        # Add null terminator
        string_bytes = (string_value + '\0').encode('utf-8')
        
        # Create constant array with the string bytes
        string_const = ir.Constant(
            ir.ArrayType(ir.IntType(8), len(string_bytes)),
            bytearray(string_bytes)
        )
        
        # Create global constant for the string
        global_string = ir.GlobalVariable(
            self.module, 
            string_const.type,
            name=self.module.get_unique_name("str")
        )
        global_string.linkage = 'internal'
        global_string.global_constant = True
        global_string.initializer = string_const
        
        # Return pointer to the string (cast to i8*)
        return self.builder.bitcast(global_string, ir.IntType(8).as_pointer())

