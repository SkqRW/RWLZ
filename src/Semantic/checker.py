"""
Semantic Checker for RWLZ Language
Performs semantic analysis including type checking, scope management, and error detection.
"""

from typing import Optional, List, Any
from Utils.model import *
from Utils.errors import error, warning
from .symtab import SymbolTable, Symbol, FunctionSymbol
from .typesys import TypeSystem, RWLZType, BaseType
from rich.table import Table
from rich.console import Console
from rich import print as rprint

class SemanticChecker:
    """
    Performs semantic analysis on the AST.
    Uses visitor pattern to traverse the AST and check for semantic errors.
    """
    
    def __init__(self):
        self.symtab = SymbolTable()
        self.type_system = TypeSystem()
        self.errors = 0
        self.warnings = 0
        
        # Context tracking
        self.current_function: Optional[FunctionSymbol] = None
        self.in_loop = False
        self.return_found = False
    
    def check(self, ast: Program) -> bool:
        """
        Main entry point for semantic checking.
        Returns True if no errors were found.
        """
        self.errors = 0
        self.warnings = 0
        
        try:
            self.visit(ast)
        except Exception as e:
            error(f"Internal error during semantic analysis: {e}")
            self.errors += 1
        
        return self.errors == 0
    
    def visit(self, node: Node, *args, **kwargs) -> Any:
        """Generic visit method that dispatches to specific visit methods"""
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node, *args, **kwargs)
    
    def generic_visit(self, node: Node, *args, **kwargs):
        """Default visitor for nodes without specific handlers"""
        error(f"No visitor method for node type: {node.__class__.__name__}")
        self.errors += 1
        return None
    
    # =========================================================================
    # PROGRAM AND METADATA
    # =========================================================================
    
    def visit_Program(self, node: Program) -> None:
        """Visit the program root node"""

        # Sad probably can't be implement with the update, broke the hooks D:
        if node.metadata:
            self.visit(node.metadata) 


        # First collect all function declarations and then visit their bodies blocks
        for func in node.functions:
            self._declare_function(func)
        
        for func in node.functions:
            self.visit(func)

    # Visit for a shameless ID
    def visit_Metadata(self, node: Metadata) -> None:
        """Visit metadata node - just validate it exists and is complete"""
        if not node.ID or not node.NAME or not node.VERSION:
            error("Metadata must have ID, NAME, and VERSION", node.lineno)
            self.errors += 1
    
    # =========================================================================
    # FUNCTION DECLARATIONS
    # =========================================================================
    
    def _declare_function(self, func: Function) -> None:
        """Register a function in the symbol table (first pass)"""
        # Parse return type
        return_type = self.type_system.parse_type_name(func.return_type.name)
        
        # Parse parameter types
        param_types = []
        param_names = []
        for param in func.params:
            param_type = self.type_system.parse_type_name(param.param_type.name)
            param_types.append(param_type)
            param_names.append(param.name)
        
        # Determine function kind, just be a normal person and ignore the other kinds
        function_kind = "normal"
        if isinstance(func, BaseFunction):
            function_kind = "base"
        elif isinstance(func, BreedFunction):
            function_kind = "breed"
        elif isinstance(func, HookFunction):
            function_kind = "hook"
        
        # Create function symbol
        func_symbol = FunctionSymbol(
            name=func.name,
            symbol_type=return_type,
            param_types=param_types,
            param_names=param_names,
            return_type=return_type,
            function_kind=function_kind,
            is_initialized=True,
            lineno=func.lineno
        )
        
        # Register in symbol table
        if not self.symtab.define_function(func_symbol):
            error(f"Function '{func.name}' is already defined", func.lineno)
            self.errors += 1
    
    def visit_NormalFunction(self, node: NormalFunction) -> None:
        """Visit a normal function definition"""
        self._visit_function(node, "normal")
    
    # Those probably will not be implemented in the future
    def visit_BaseFunction(self, node: BaseFunction) -> None:
        """Visit a base function definition"""
        self._visit_function(node, "base")
    
    def visit_BreedFunction(self, node: BreedFunction) -> None:
        """Visit a breed function definition"""
        self._visit_function(node, "breed")
    
    def visit_HookFunction(self, node: HookFunction) -> None:
        """Visit a hook function definition"""
        self._visit_function(node, "hook")
    
    def _visit_function(self, func: Function, kind: str) -> None:
        """Common function visiting logic"""
        # Look up the function symbol
        func_symbol = self.symtab.lookup_function(func.name)
        if not func_symbol:
            error(f"Function '{func.name}' not found in symbol table", func.lineno)
            self.errors += 1
            return
        
        # Set current function context
        old_function = self.current_function
        self.current_function = func_symbol
        self.return_found = False
        
        # Enter function scope
        self.symtab.enter_scope(f"function_{func.name}")
        
        # Add parameters to function scope
        for param in func.params:
            param_type = self.type_system.parse_type_name(param.param_type.name)
            param_symbol = Symbol(
                name=param.name,
                symbol_type=param_type,
                is_initialized=True,
                is_parameter=True,
                lineno=param.lineno
            )
            if not self.symtab.define_symbol(param_symbol):
                error(f"Parameter '{param.name}' is already defined", param.lineno)
                self.errors += 1
        
        # Visit function body
        self.visit(func.body)
        
        # Check if non-void function has return statement
        if func_symbol.return_type.base_type != BaseType.VOID and not self.return_found:
            warning(f"Function '{func.name}' should return a value of type '{func_symbol.return_type}'", func.lineno)
            self.warnings += 1
        
        # Exit function scope
        self.symtab.exit_scope()
        
        # Restore context
        self.current_function = old_function
    
    # =========================================================================
    # STATEMENTS
    # =========================================================================
    # Just search into the node and will be fine, a lot i have to say, 
    # Feel i mesh up with the arrays T_T
    
    def visit_Block(self, node: Block) -> None:
        """Visit a block of statements"""
        # Enter new scope for block
        self.symtab.enter_scope("block")
        
        for stmt in node.statements:
            self.visit(stmt)
        
        # Exit block scope
        self.symtab.exit_scope()
    
    def visit_VarDecl(self, node: VarDecl) -> None:
        """Visit a variable declaration"""
        var_type = self.type_system.parse_type_name(node.var_type.name)
        
        # Check if variable already exists in current scope
        existing = self.symtab.lookup_symbol(node.name, current_only=True)
        if existing:
            error(f"Variable '{node.name}' is already defined in this scope", node.lineno)
            self.errors += 1
            return
        
        # If it has an initializer, check type compatibility
        is_initialized = node.value is not None
        if is_initialized:
            init_type = self.visit(node.value)
            if init_type and not self.type_system.is_compatible(var_type, init_type):
                error(f"Cannot initialize variable '{node.name}' of type '{var_type}' with value of type '{init_type}'", node.lineno)
                self.errors += 1
        
        # Check const variables must be initialized
        if node.is_const and not is_initialized:
            error(f"Const variable '{node.name}' must be initialized", node.lineno)
            self.errors += 1
        
        # Add to symbol table
        symbol = Symbol(
            name=node.name,
            symbol_type=var_type,
            is_const=node.is_const,
            is_initialized=is_initialized,
            lineno=node.lineno
        )
        self.symtab.define_symbol(symbol)
    
    def visit_ArrayDecl(self, node: ArrayDecl) -> None:
        """Visit an array declaration"""
        element_type = self.type_system.parse_type_name(node.var_type.name)
        array_type = self.type_system.create_array_type(element_type)
        
        # Check if variable already exists
        existing = self.symtab.lookup_symbol(node.name, current_only=True)
        if existing:
            error(f"Array '{node.name}' is already defined in this scope", node.lineno)
            self.errors += 1
            return
        
        # Check size expression if present
        if node.size:
            size_type = self.visit(node.size)
            if size_type and not self.type_system.is_integer(size_type):
                error(f"Array size must be an integer, got '{size_type}'", node.lineno)
                self.errors += 1
        
        # Check initializer values if present
        is_initialized = node.values is not None
        if is_initialized and node.values:
            for i, val in enumerate(node.values):
                val_type = self.visit(val)
                if val_type and not self.type_system.is_compatible(element_type, val_type):
                    error(f"Array element {i} has incompatible type '{val_type}', expected '{element_type}'", node.lineno)
                    self.errors += 1
        
        # Check const arrays must be initialized
        if node.is_const and not is_initialized:
            error(f"Const array '{node.name}' must be initialized", node.lineno)
            self.errors += 1
        
        # Add to symbol table
        symbol = Symbol(
            name=node.name,
            symbol_type=array_type,
            is_const=node.is_const,
            is_initialized=is_initialized,
            lineno=node.lineno
        )
        self.symtab.define_symbol(symbol)
    
    def visit_Assignment(self, node: Assignment) -> None:
        """Visit an assignment statement"""
        # Get the target variable/location
        target_symbol = None
        target_type = None
        
        if isinstance(node.target, VarLocation):
            target_symbol = self.symtab.lookup_symbol(node.target.name)
            if not target_symbol:
                error(f"Variable '{node.target.name}' is not defined", node.lineno)
                self.errors += 1
                return
            # Mark variable as used
            target_symbol.is_used = True
            target_type = target_symbol.symbol_type
        
        elif isinstance(node.target, ArrayLocation):
            target_symbol = self.symtab.lookup_symbol(node.target.name)
            if not target_symbol:
                error(f"Array '{node.target.name}' is not defined", node.lineno)
                self.errors += 1
                return
            
            # Mark array as used
            target_symbol.is_used = True
            
            if not target_symbol.symbol_type.is_array:
                error(f"'{node.target.name}' is not an array", node.lineno)
                self.errors += 1
                return
            
            # Check index type
            index_type = self.visit(node.target.index)
            if index_type and not self.type_system.is_integer(index_type):
                error(f"Array index must be an integer, got '{index_type}'", node.lineno)
                self.errors += 1
            
            target_type = self.type_system.get_array_element_type(target_symbol.symbol_type)
        
        if not target_type:
            return
        
        # Check if target is const, too bad, you can't assign to it
        if target_symbol and target_symbol.is_const:
            error(f"Cannot assign to const variable '{node.target.name}'", node.lineno)
            self.errors += 1
            return
        
        # Handle increment/decrement operators
        if node.operator in ['++', '--']:
            if not self.type_system.check_increment_decrement(target_type):
                error(f"Cannot apply '{node.operator}' to type '{target_type}'", node.lineno)
                self.errors += 1
            return
        
        # Check value type for regular assignments
        if node.value:
            value_type = self.visit(node.value)
            if not value_type:
                return
            
            # Handle compound assignments
            if node.operator in ['+=', '-=', '*=', '/=']:
                base_op = node.operator[0]  # Get +, -, *, /
                result_type = self.type_system.check_arithmetic_operation(base_op, target_type, value_type)
                if not result_type:
                    error(f"Invalid operation '{target_type} {node.operator} {value_type}'", node.lineno)
                    self.errors += 1
                elif not self.type_system.is_compatible(target_type, result_type):
                    error(f"Cannot assign '{result_type}' to '{target_type}'", node.lineno)
                    self.errors += 1
            
            # Regular assignment
            elif node.operator == '=':
                if not self.type_system.is_compatible(target_type, value_type):
                    error(f"Cannot assign '{value_type}' to '{target_type}'", node.lineno)
                    self.errors += 1
        
        # Mark variable as initialized
        if target_symbol:
            target_symbol.is_initialized = True
    
    def visit_IfStatement(self, node: IfStatement) -> None:
        """Visit an if statement"""
        # Check condition type - accept boolean or numeric (like C: 0=false, non-zero=true)
        cond_type = self.visit(node.condition)
        if cond_type:
            is_valid = (self.type_system.is_boolean(cond_type) or 
                       self.type_system.is_numeric(cond_type)) and not cond_type.is_array
            if not is_valid:
                error(f"If condition must be boolean or numeric, got '{cond_type}'", node.lineno)
                self.errors += 1
        
        # Visit then block
        self.visit(node.then_block)
        
        # Visit else block if present
        if node.else_block:
            self.visit(node.else_block)
    
    def visit_WhileStatement(self, node: WhileStatement) -> None:
        """Visit a while loop"""
        # Check condition type - accept boolean or numeric (like C: 0=false, non-zero=true)
        cond_type = self.visit(node.condition)
        if cond_type:
            is_valid = (self.type_system.is_boolean(cond_type) or 
                       self.type_system.is_numeric(cond_type)) and not cond_type.is_array
            if not is_valid:
                error(f"While condition must be boolean or numeric, got '{cond_type}'", node.lineno)
                self.errors += 1
        
        # Visit body with loop context
        old_in_loop = self.in_loop
        self.in_loop = True
        self.visit(node.body)
        self.in_loop = old_in_loop
    
    def visit_ForStatement(self, node: ForStatement) -> None:
        """Visit a for loop"""
        # Enter scope for loop (init variable scope)
        self.symtab.enter_scope("for_loop")
        
        # Visit init
        if node.init:
            self.visit(node.init)
        
        # Check condition type - accept boolean or numeric (like C: 0=false, non-zero=true)
        if node.condition:
            cond_type = self.visit(node.condition)
            if cond_type:
                is_valid = (self.type_system.is_boolean(cond_type) or 
                           self.type_system.is_numeric(cond_type)) and not cond_type.is_array
                if not is_valid:
                    error(f"For loop condition must be boolean or numeric, got '{cond_type}'", node.lineno)
                    self.errors += 1
        
        # Visit update
        if node.update:
            self.visit(node.update)
        
        # Visit body with loop context
        old_in_loop = self.in_loop
        self.in_loop = True
        self.visit(node.body)
        self.in_loop = old_in_loop
        
        # Exit loop scope
        self.symtab.exit_scope()
    
    # REMEMBER ONLY IN LOOPS
    # A BREAK IN A FUNCTION NOT MEAND THAT GONA FINNISH, USE INSTEAD RETURN FOR THAT FELIPE!!!!!!
    def visit_BreakStatement(self, node: BreakStatement) -> None:
        """Visit a break statement"""
        if not self.in_loop:
            error("Break statement outside of loop", node.lineno)
            self.errors += 1
    
    def visit_ContinueStatement(self, node: ContinueStatement) -> None:
        """Visit a continue statement"""
        if not self.in_loop:
            error("Continue statement outside of loop", node.lineno)
            self.errors += 1
    
    def visit_ReturnStatement(self, node: ReturnStatement) -> None:
        """Visit a return statement"""
        if not self.current_function:
            error("Return statement outside of function", node.lineno)
            self.errors += 1
            return
        
        self.return_found = True
        
        expected_type = self.current_function.return_type
        
        # Check if return has a value
        if node.value:
            return_type = self.visit(node.value)
            
            # Void function should not return a value
            if expected_type.base_type == BaseType.VOID:
                error(f"Void function '{self.current_function.name}' should not return a value", node.lineno)
                self.errors += 1
            
            # Check type compatibility
            elif return_type and not self.type_system.is_compatible(expected_type, return_type):
                error(f"Return type '{return_type}' does not match function return type '{expected_type}'", node.lineno)
                self.errors += 1
        
        else:
            # Non-void function should return a value
            if expected_type.base_type != BaseType.VOID:
                error(f"Function '{self.current_function.name}' must return a value of type '{expected_type}'", node.lineno)
                self.errors += 1
    
    # :D
    def visit_PrintStatement(self, node: PrintStatement) -> None:
        """Visit a print statement"""
        self.visit(node.expression)
    
    def visit_FunctionCallStmt(self, node: FunctionCallStmt) -> None:
        """Visit a function call statement"""
        self.visit(node.call)
    
    # =========================================================================
    # EXPRESSIONS
    # =========================================================================
    
    def visit_BinOper(self, node: BinOper) -> Optional[RWLZType]:
        """Visit a binary operation"""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        if not left_type or not right_type:
            return RWLZType(base_type=BaseType.ERROR)
        
        # Arithmetic operations
        if node.operator in TypeSystem.ARITHMETIC_OPS:
            result_type = self.type_system.check_arithmetic_operation(node.operator, left_type, right_type)
            if not result_type:
                error(f"Invalid arithmetic operation '{left_type} {node.operator} {right_type}'", node.lineno)
                self.errors += 1
                return RWLZType(base_type=BaseType.ERROR)
            return result_type
        
        # Comparison operations
        elif node.operator in TypeSystem.COMPARISON_OPS:
            result_type = self.type_system.check_comparison_operation(node.operator, left_type, right_type)
            if not result_type:
                error(f"Invalid comparison operation '{left_type} {node.operator} {right_type}'", node.lineno)
                self.errors += 1
                return RWLZType(base_type=BaseType.ERROR)
            return result_type
        
        # Logical operations
        elif node.operator in TypeSystem.LOGICAL_OPS:
            result_type = self.type_system.check_logical_operation(node.operator, left_type, right_type)
            if not result_type:
                error(f"Invalid logical operation '{left_type} {node.operator} {right_type}'", node.lineno)
                self.errors += 1
                return RWLZType(base_type=BaseType.ERROR)
            return result_type
        
        else:
            error(f"Unknown binary operator '{node.operator}'", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
    
    def visit_UnaryOper(self, node: UnaryOper) -> Optional[RWLZType]:
        """Visit a unary operation"""
        operand_type = self.visit(node.operand)
        
        if not operand_type:
            return RWLZType(base_type=BaseType.ERROR)
        
        result_type = self.type_system.check_unary_operation(node.operator, operand_type)
        if not result_type:
            error(f"Invalid unary operation '{node.operator} {operand_type}'", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        return result_type
    
    def visit_IncrementExpression(self, node: IncrementExpression) -> Optional[RWLZType]:
        """Visit an increment/decrement expression"""
        # Look up the variable
        symbol = self.symtab.lookup_symbol(node.variable)
        if not symbol:
            error(f"Variable '{node.variable}' is not defined", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        # Check if const
        if symbol.is_const:
            error(f"Cannot modify const variable '{node.variable}'", node.lineno)
            self.errors += 1
        
        # Check if type supports increment/decrement
        if not self.type_system.check_increment_decrement(symbol.symbol_type):
            error(f"Cannot apply '{node.operator}' to type '{symbol.symbol_type}'", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        return symbol.symbol_type
    
    def visit_CallExpression(self, node: CallExpression) -> Optional[RWLZType]:
        """Visit a function call expression"""
        # Look up the function
        func_symbol = self.symtab.lookup_function(node.name)
        if not func_symbol:
            error(f"Function '{node.name}' is not defined", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        # Check number of arguments
        if len(node.arguments) != len(func_symbol.param_types):
            error(f"Function '{node.name}' expects {len(func_symbol.param_types)} arguments, got {len(node.arguments)}", node.lineno)
            self.errors += 1
            return func_symbol.return_type
        
        # Check argument types
        for i, (arg, expected_type) in enumerate(zip(node.arguments, func_symbol.param_types)):
            arg_type = self.visit(arg)
            if arg_type and not self.type_system.is_compatible(expected_type, arg_type):
                error(f"Argument {i+1} of function '{node.name}': expected '{expected_type}', got '{arg_type}'", node.lineno)
                self.errors += 1
        
        return func_symbol.return_type
    
    def visit_ArrayAccess(self, node: ArrayAccess) -> Optional[RWLZType]:
        """Visit an array access expression"""
        # Look up the array
        symbol = self.symtab.lookup_symbol(node.name)
        if not symbol:
            error(f"Array '{node.name}' is not defined", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        # Mark array as used
        symbol.is_used = True
        
        if not symbol.symbol_type.is_array:
            error(f"'{node.name}' is not an array", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        # Check index type
        index_type = self.visit(node.index)
        if index_type and not self.type_system.is_integer(index_type):
            error(f"Array index must be an integer, got '{index_type}'", node.lineno)
            self.errors += 1
        
        # Return element type
        return self.type_system.get_array_element_type(symbol.symbol_type)
    
    def visit_ArrayLiteral(self, node: ArrayLiteral) -> Optional[RWLZType]:
        """Visit an array literal"""
        if not node.elements:
            # Empty array - type cannot be determined
            return RWLZType(base_type=BaseType.ERROR)
        
        # Get type from first element
        first_type = self.visit(node.elements[0])
        if not first_type:
            return RWLZType(base_type=BaseType.ERROR)
        
        # Check all elements have the same type
        for i, elem in enumerate(node.elements[1:], 1):
            elem_type = self.visit(elem)
            if elem_type and not self.type_system.is_compatible(first_type, elem_type):
                error(f"Array element {i} has incompatible type '{elem_type}', expected '{first_type}'", node.lineno)
                self.errors += 1
        
        return self.type_system.create_array_type(first_type)
    
    def visit_Variable(self, node: Variable) -> Optional[RWLZType]:
        """Visit a variable reference"""
        symbol = self.symtab.lookup_symbol(node.name)
        if not symbol:
            error(f"Variable '{node.name}' is not defined", node.lineno)
            self.errors += 1
            return RWLZType(base_type=BaseType.ERROR)
        
        # Mark variable as used
        symbol.is_used = True
        
        if not symbol.is_initialized:
            warning(f"Variable '{node.name}' may not be initialized", node.lineno)
            self.warnings += 1
        
        return symbol.symbol_type
    
    # =========================================================================
    # LITERALS
    # =========================================================================
    # case for solitary nodes somehow
    
    def visit_Integer(self, node: Integer) -> RWLZType:
        """Visit an integer literal"""
        return RWLZType(base_type=BaseType.INT)
    
    def visit_Float(self, node: Float) -> RWLZType:
        """Visit a float literal"""
        return RWLZType(base_type=BaseType.FLOAT)
    
    def visit_String(self, node: String) -> RWLZType:
        """Visit a string literal"""
        return RWLZType(base_type=BaseType.STRING)
    
    def visit_Char(self, node: Char) -> RWLZType:
        """Visit a char literal"""
        return RWLZType(base_type=BaseType.CHAR)
    
    def visit_Boolean(self, node: Boolean) -> RWLZType:
        """Visit a boolean literal"""
        return RWLZType(base_type=BaseType.BOOL)
    
    # =========================================================================
    # SPECIAL EXPRESSIONS, DEPRECATED FEATURES
    # =========================================================================
    
    def visit_PropExpression(self, node: PropExpression) -> Optional[RWLZType]:
        """Visit a <prop>() expression"""
        # For now, just visit the inner expression
        # This is a special BepInEx feature that would need game-specific type info
        warning("<prop>() expressions are not fully type-checked", node.lineno)
        self.warnings += 1
        return RWLZType(base_type=BaseType.AUTO)
    
    def visit_BaseExpression(self, node: BaseExpression) -> Optional[RWLZType]:
        """Visit a <base>() expression"""
        # Special expression for base class calls
        warning("<base>() expressions are not fully type-checked", node.lineno)
        self.warnings += 1
        return self.visit(node.expression)
    
    def visit_BreedExpression(self, node: BreedExpression) -> Optional[RWLZType]:
        """Visit a <breed>() expression"""
        # Special expression for breed operations
        warning("<breed>() expressions are not fully type-checked", node.lineno)
        self.warnings += 1
        return self.visit(node.expression)
    
    def visit_HookExpression(self, node: HookExpression) -> Optional[RWLZType]:
        """Visit a <hook>() expression"""
        # Special expression for hook operations
        warning("<hook>() expressions are not fully type-checked", node.lineno)
        self.warnings += 1
        return self.visit(node.expression)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_statistics(self) -> dict:
        """Get statistics about the semantic analysis"""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "success": self.errors == 0
        }
    
    def print_symbol_table(self):
        """Print the symbol table for debugging"""
        printer = SymbolTablePrinter(self.symtab)
        printer.print()



# =============================================================================
# SYMBOL TABLE PRINTER
# =============================================================================

class SymbolTablePrinter:
    """
    Handles formatting and printing of symbol tables.
    Separates presentation logic from semantic analysis.
    """
    
    def __init__(self, symtab: SymbolTable):
        self.symtab = symtab
        self.console = Console()
    
    def print(self, format: str = "rich"):
        """
        Print symbol table in specified format.
        
        Args:
            format: Output format ("rich", "plain", "json")
        """
        if format == "rich":
            self._print_rich()
        elif format == "plain":
            self._print_plain()
        else:
            self._print_rich()
    
    def _print_rich(self):
        """Print symbol table using Rich formatting with enhanced output"""
        rprint("\n[bold cyan]" + "="*80 + "[/bold cyan]")
        rprint("[bold cyan]" + " "*25 + "SYMBOL TABLE DUMP" + "[/bold cyan]")
        rprint("[bold cyan]" + "="*80 + "[/bold cyan]\n")
        self._print_scope(self.symtab.global_scope)
        rprint("[bold cyan]" + "="*80 + "[/bold cyan]\n")
    
    def _print_plain(self):
        """Print symbol table in plain text format"""
        print("\n" + "="*80)
        print(" "*25 + "SYMBOL TABLE DUMP")
        print("="*80 + "\n")
        self._print_scope_plain(self.symtab.global_scope)
        print("="*80 + "\n")
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_array_size_str(self, symbol_type: RWLZType) -> str:
        """Extract array size string if available"""
        if symbol_type.is_array:
            # Try to get size from array type if available
            type_str = str(symbol_type)
            if '[' in type_str and ']' in type_str:
                return type_str
            return f"{symbol_type.element_type}[]"
        return str(symbol_type)
    
    def _get_symbol_type_label(self, symbol: Symbol) -> str:
        """Get descriptive label for symbol type"""
        if isinstance(symbol, FunctionSymbol):
            if symbol.is_builtin:
                return "builtin function"
            return "user function"
        
        if symbol.is_parameter:
            return "parameter"
        
        if symbol.symbol_type.is_array:
            if symbol.is_const:
                return "const array variable"
            return "array variable"
        
        if symbol.is_const:
            return "const variable"
        
        return "variable"
    
    def _format_symbol_value(self, symbol: Symbol) -> str:
        """Format the value column for a symbol"""
        if isinstance(symbol, FunctionSymbol):
            params = ", ".join(f"{pt} {pn}" for pt, pn in 
                              zip(symbol.param_types, symbol.param_names))
            func_type = "builtin function" if symbol.is_builtin else "user function"
            return f"[green]{func_type}[/green]: ({params}) -> {symbol.return_type}"
        
        # Regular variables
        type_label = self._get_symbol_type_label(symbol)
        type_str = self._get_array_size_str(symbol.symbol_type)
        init_str = "[green]✓[/green]" if symbol.is_initialized else "[red]✗[/red]"
        used_str = "[green]✓[/green]" if symbol.is_used else "[red]✗[/red]"
        
        color = "magenta" if symbol.is_const else "bright_blue"
        return f"[{color}]{type_label}[/{color}]: [bright_green]{type_str}[/bright_green] [init: {init_str}, used: {used_str}]"
    
    def _collect_all_block_symbols(self, scope):
        """Recursively collect all symbols from blocks and nested scopes (excluding parameters)"""
        all_symbols = {}
        
        # Add symbols from current scope (excluding parameters)
        for name, symbol in scope.symbols.items():
            if not isinstance(symbol, FunctionSymbol) and not symbol.is_parameter:
                all_symbols[name] = symbol
        
        # Recursively collect from children
        for child in scope.children:
            if child.name in ["block", "for_loop"]:
                child_symbols = self._collect_all_block_symbols(child)
                all_symbols.update(child_symbols)
        
        return all_symbols
    
    # =========================================================================
    # RICH FORMATTING
    # =========================================================================
    
    def _print_scope(self, scope, level: int = 0):
        """Print scope using Rich formatting"""
        indent = "  " * level
        
        # Check if this is a function scope
        is_function_scope = scope.name.startswith("function_")
        
        if is_function_scope:
            self._print_function_scope(scope, indent)
        else:
            self._print_global_scope(scope, indent)
    
    def _print_function_scope(self, scope, indent: str):
        """Print a function scope with Rich formatting"""
        func_name = scope.name.replace("function_", "")
        
        # Get function symbol from parent (global) scope
        func_symbol = self.symtab.lookup_function(func_name)
        
        # Build title with location
        title = f"[bold cyan]symbol table: {func_name}[/bold cyan]"
        if func_symbol and func_symbol.lineno > 0:
            location = f" (defined at line {func_symbol.lineno}"
            location += ")"
            title += f" [dim]{location}[/dim]"
        
        rprint(f"\n{indent}{title}")
        
        # Show parent scope
        parent_name = scope.parent.name if scope.parent else "None"
        rprint(f"{indent}  [dim]parent: {parent_name}[/dim]")
        
        # Show return type
        if func_symbol:
            rprint(f"{indent}  [dim]return type: [bright_green]{func_symbol.return_type}[/bright_green][/dim]")
        
        # Get parameters
        params = {name: symbol for name, symbol in scope.symbols.items()
                  if not isinstance(symbol, FunctionSymbol) and symbol.is_parameter}
        
        # Print parameters section
        if params:
            self._print_parameters_table(params, indent)
        
        # Collect and print block symbols
        block_symbols = self._collect_all_block_symbols(scope)
        if block_symbols:
            self._print_block_table(block_symbols, indent)
        
        self.console.print()  # Empty line after function
    
    def _print_global_scope(self, scope, indent: str):
        """Print global scope with Rich formatting"""
        title = f"{indent}symbol table: {scope.name}"
        parent_name = scope.parent.name if scope.parent else "None"
        
        rprint(f"\n[bold cyan]{title}[/bold cyan]")
        rprint(f"[dim](parent: {parent_name})[/dim]")
        rprint(f"[dim](symbols listed in declaration order)[/dim]")
        
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="bright_black"
        )
        
        table.add_column("key", style="cyan", no_wrap=True, width=30)
        table.add_column("value", style="yellow")
        
        if not scope.symbols:
            table.add_row("(empty)", "no symbols")
        else:
            for name, symbol in scope.symbols.items():
                value = self._format_symbol_value(symbol)
                table.add_row(name, value)
        
        self.console.print(table)
        self.console.print()  # Empty line
        
        # Recursively print children (functions)
        for child in scope.children:
            self._print_scope(child, len(indent) // 2 + 1)
    
    def _print_parameters_table(self, params: dict, indent: str):
        """Print parameters table"""
        rprint(f"{indent}  [bold yellow]parameters:[/bold yellow]")
        rprint(f"{indent}    [dim](symbols listed in declaration order)[/dim]")
        param_table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="bright_black",
            padding=(0, 1)
        )
        param_table.add_column("key", style="cyan", no_wrap=True, width=28)
        param_table.add_column("value", style="yellow")
        
        for name, symbol in params.items():
            type_str = self._get_array_size_str(symbol.symbol_type)
            init_str = "[green]✓[/green]" if symbol.is_initialized else "[red]✗[/red]"
            used_str = "[green]✓[/green]" if symbol.is_used else "[red]✗[/red]"
            value = f"[bright_green]{type_str}[/bright_green] [init: {init_str}, used: {used_str}]"
            param_table.add_row(name, value)
        
        self.console.print(f"{indent}  ", param_table)
    
    def _print_block_table(self, block_symbols: dict, indent: str):
        """Print block variables table"""
        rprint(f"{indent}  [bold yellow]block:[/bold yellow]")
        rprint(f"{indent}    [dim](symbols listed in declaration order)[/dim]")
        block_table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="bright_black",
            padding=(0, 1)
        )
        block_table.add_column("key", style="cyan", no_wrap=True, width=28)
        block_table.add_column("value", style="yellow")
        
        for name, symbol in block_symbols.items():
            value = self._format_symbol_value(symbol)
            block_table.add_row(name, value)
        
        self.console.print(f"{indent}    ", block_table)
    
    # =========================================================================
    # PLAIN TEXT FORMATTING
    # =========================================================================
    
    def _print_scope_plain(self, scope, level: int = 0):
        """Print scope in plain text format"""
        indent = "  " * level
        print(f"\n{indent}Symbol Table: {scope.name}")
        print(f"{indent}{'Key':<30} | {'Value'}")
        print(f"{indent}{'-'*30}-+-{'-'*50}")
        
        if not scope.symbols:
            print(f"{indent}{'(empty)':<30} | {'no symbols'}")
        else:
            for name, symbol in scope.symbols.items():
                value = self._format_symbol_value_plain(symbol)
                print(f"{indent}{name:<30} | {value}")
        
        # Recursively print children
        for child in scope.children:
            self._print_scope_plain(child, level + 1)
    
    def _format_symbol_value_plain(self, symbol: Symbol) -> str:
        """Format symbol value for plain text output"""
        if isinstance(symbol, FunctionSymbol):
            params = ", ".join(f"{pt} {pn}" for pt, pn in 
                              zip(symbol.param_types, symbol.param_names))
            func_type = "builtin" if symbol.is_builtin else "user"
            return f"{func_type} function: ({params}) -> {symbol.return_type}"
        
        type_label = self._get_symbol_type_label(symbol)
        type_str = self._get_array_size_str(symbol.symbol_type)
        init_str = "✓" if symbol.is_initialized else "✗"
        used_str = "✓" if symbol.is_used else "✗"
        
        return f"{type_label}: {type_str} [init: {init_str}, used: {used_str}]"
