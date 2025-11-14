"""
Built-in Runtime Functions for RWLZ Language
Declares and manages built-in functions that are provided by the C standard library.

Responsibility: Declare built-in library functions (printf, scanf, etc.)
Does NOT handle: Code generation for user-defined functions
"""

from llvmlite import ir
from typing import Dict


class BuiltInFunctions:
    """
    Manages built-in runtime functions that will be linked from the C standard library.
    
    Responsibilities:
    - Declare function signatures for built-in functions (printf, etc.)
    - Provide access to built-in function references
    - Maintain a registry of available built-in functions
    
    Usage:
        builtins = BuiltInFunctions(module)
        printf_func = builtins.get_function("printf")
    """
    
    def __init__(self, module: ir.Module):
        """
        Initialize built-in functions for the given LLVM module.
        
        Args:
            module: The LLVM module where functions will be declared
        """
        self.module = module
        self.functions: Dict[str, ir.Function] = {}
        
        # Declare all built-in functions
        self._declare_all()
    
    def _declare_all(self):
        """
        Declare all built-in runtime functions.
        Add new built-in functions here as needed.
        """
        self._declare_printf()
        self._declare_strlen()
        self._declare_strcpy()
        self._declare_strcmp()
        self._declare_strcat()
        self._declare_malloc()
        # Future built-ins can be added here:
        # self._declare_scanf()
        # self._declare_free()
    
    def _declare_printf(self):
        """
        Declare printf function from C standard library.
        
        Signature: int printf(const char *format, ...)
        
        - First parameter: pointer to format string (i8*)
        - Returns: number of characters printed (i32)
        - Variable arguments: accepts any number of additional arguments
        """
        # i8* for the format string (char* in C)
        char_ptr_ty = ir.IntType(8).as_pointer()
        
        # int printf(char*, ...) - variadic function
        printf_ty = ir.FunctionType(
            ir.IntType(32),      # return type: int (i32)
            [char_ptr_ty],       # first parameter: char* (i8*)
            var_arg=True         # accepts variable arguments
        )
        
        # Create function declaration
        printf_func = ir.Function(self.module, printf_ty, name="printf")
        
        # Store in registry
        self.functions["printf"] = printf_func
    
    def _declare_strlen(self):
        """
        Declare strlen function from C standard library.
        
        Signature: size_t strlen(const char *str)
        
        - Parameter: pointer to string (i8*)
        - Returns: length of string (i64)
        """
        char_ptr_ty = ir.IntType(8).as_pointer()
        strlen_ty = ir.FunctionType(ir.IntType(64), [char_ptr_ty])
        strlen_func = ir.Function(self.module, strlen_ty, name="strlen")
        self.functions["strlen"] = strlen_func
    
    def _declare_strcpy(self):
        """
        Declare strcpy function from C standard library.
        
        Signature: char* strcpy(char *dest, const char *src)
        
        - Parameters: destination pointer (i8*), source pointer (i8*)
        - Returns: destination pointer (i8*)
        """
        char_ptr_ty = ir.IntType(8).as_pointer()
        strcpy_ty = ir.FunctionType(char_ptr_ty, [char_ptr_ty, char_ptr_ty])
        strcpy_func = ir.Function(self.module, strcpy_ty, name="strcpy")
        self.functions["strcpy"] = strcpy_func
    
    def _declare_strcmp(self):
        """
        Declare strcmp function from C standard library.
        
        Signature: int strcmp(const char *str1, const char *str2)
        
        - Parameters: two string pointers (i8*, i8*)
        - Returns: 0 if equal, <0 if str1 < str2, >0 if str1 > str2 (i32)
        """
        char_ptr_ty = ir.IntType(8).as_pointer()
        strcmp_ty = ir.FunctionType(ir.IntType(32), [char_ptr_ty, char_ptr_ty])
        strcmp_func = ir.Function(self.module, strcmp_ty, name="strcmp")
        self.functions["strcmp"] = strcmp_func
    
    def _declare_strcat(self):
        """
        Declare strcat function from C standard library.
        
        Signature: char* strcat(char *dest, const char *src)
        
        - Parameters: destination pointer (i8*), source pointer (i8*)
        - Returns: destination pointer (i8*)
        """
        char_ptr_ty = ir.IntType(8).as_pointer()
        strcat_ty = ir.FunctionType(char_ptr_ty, [char_ptr_ty, char_ptr_ty])
        strcat_func = ir.Function(self.module, strcat_ty, name="strcat")
        self.functions["strcat"] = strcat_func
    
    def _declare_malloc(self):
        """
        Declare malloc function from C standard library.
        
        Signature: void* malloc(size_t size)
        
        - Parameter: number of bytes to allocate (i64)
        - Returns: pointer to allocated memory (i8*)
        """
        malloc_ty = ir.FunctionType(ir.IntType(8).as_pointer(), [ir.IntType(64)])
        malloc_func = ir.Function(self.module, malloc_ty, name="malloc")
        self.functions["malloc"] = malloc_func
    
    def get_function(self, name: str) -> ir.Function:
        """
        Get a built-in function by name.
        
        Args:
            name: The name of the built-in function (e.g., "printf")
            
        Returns:
            The LLVM function object
            
        Raises:
            KeyError: If the function name is not a registered built-in
        """
        if name not in self.functions:
            raise KeyError(f"Built-in function '{name}' not found. Available: {list(self.functions.keys())}")
        
        return self.functions[name]
    
    def has_function(self, name: str) -> bool:
        """
        Check if a function name is a registered built-in.
        
        Args:
            name: The function name to check
            
        Returns:
            True if the function is a built-in, False otherwise
        """
        return name in self.functions
    
    def list_functions(self) -> list:
        """
        Get a list of all registered built-in function names.
        
        Returns:
            List of function names
        """
        return list(self.functions.keys())
