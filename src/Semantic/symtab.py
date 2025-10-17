"""
Symbol Table for RWLZ Language
Manages variable and function declarations with scoping.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from .typesys import RWLZType, BaseType
from rich.table import Table
from rich import print as rprint
from Utils.model import Node


@dataclass
class Symbol:
    """
    Represents a symbol (variable or function) in the symbol table.
    """
    name: str
    symbol_type: RWLZType
    is_const: bool = False
    is_initialized: bool = False
    is_used: bool = False
    lineno: int = 0
    is_parameter: bool = False
    
    def __str__(self):
        const_str = "const " if self.is_const else ""
        return f"{const_str}{self.symbol_type} {self.name}"


@dataclass
class FunctionSymbol(Symbol):
    """
    Represents a function in the symbol table.
    """
    param_types: List[RWLZType] = field(default_factory=list)
    param_names: List[str] = field(default_factory=list)
    return_type: RWLZType = field(default_factory=lambda: RWLZType(base_type=BaseType.VOID))
    function_kind: str = "normal"  # normal, base, breed, hook
    is_builtin: bool = False
    
    def __str__(self):
        params = ", ".join(f"{pt} {pn}" for pt, pn in zip(self.param_types, self.param_names))
        kind_prefix = f"<{self.function_kind}> " if self.function_kind != "normal" else ""
        return f"{kind_prefix}{self.name}({params}) -> {self.return_type}"


class Scope:
    """
    Represents a single scope level in the symbol table.
    """
    
    def __init__(self, name: str = "global", parent: Optional['Scope'] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {} # Not gonna care about optimizations in python
        self.children: List['Scope'] = []
    
    def define(self, symbol: Symbol) -> bool:
        """
        Define a new symbol in this scope.
        Returns False if the symbol already exists in this scope.
        """
        # Honestly, i like this advice to check before always put :pensative:
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True
    
    def lookup(self, name: str, current_only: bool = False) -> Optional[Symbol]:
        """
        Look up a symbol by name.
        If current_only is True, only search in the current scope.
        Otherwise, search up the scope chain.
        """
        if name in self.symbols:
            return self.symbols[name]
        
        if not current_only and self.parent:
            return self.parent.lookup(name, current_only=False)
        
        return None
    
    # TO STRING IKOVE()
    def __str__(self):
        symbols_str = "\n  ".join(str(s) for s in self.symbols.values())
        return f"Scope '{self.name}':\n  {symbols_str}" if symbols_str else f"Scope '{self.name}': (empty)"


class SymbolTable:
    """
    Manages symbol tables with scoping for the RWLZ language.
    """
    
    # R A I S E -  E X C E P T I O N S
    class SymbolDefinedError(Exception):
        """
        Excepción lanzada cuando se intenta agregar un símbolo
        que ya existe en la tabla actual con el mismo tipo.
        """
        def __init__(self, symbol_name: str, lineno: int = 0, scope_name: str = ""):
            self.symbol_name = symbol_name
            self.lineno = lineno
            self.scope_name = scope_name # parent
            message = f"Symbol '{symbol_name}' is already defined"
            if scope_name:
                message += f" in scope '{scope_name}'"
            if lineno > 0:
                message += f" (line {lineno})"
            super().__init__(message)
    
    class SymbolConflictError(Exception):
        """
        Excepción lanzada cuando se intenta agregar un símbolo
        que ya existe pero con un tipo diferente.
        """
        def __init__(self, symbol_name: str, existing_type, new_type, 
                     lineno: int = 0, scope_name: str = ""):
            self.symbol_name = symbol_name
            self.existing_type = existing_type
            self.new_type = new_type
            self.lineno = lineno
            self.scope_name = scope_name
            message = f"Symbol '{symbol_name}' already exists with type '{existing_type}', cannot redefine as '{new_type}'"
            if scope_name:
                message += f" in scope '{scope_name}'"
            if lineno > 0:
                message += f" (line {lineno})"
            super().__init__(message)
    
    def __init__(self):
        self.global_scope = Scope(name="global") #not main, sadly
        self.current_scope = self.global_scope
        self.scope_stack: List[Scope] = [self.global_scope]
        self._add_builtin_functions()
    
    # Print for logs, by beloved
    # Also, is here because i should initialize before anityhing else to use
    def _add_builtin_functions(self):
        """Add built-in functions to the global scope"""
        # print function
        print_func = FunctionSymbol(
            name="print",
            symbol_type=RWLZType(base_type=BaseType.VOID),
            param_types=[RWLZType(base_type=BaseType.STRING)],
            param_names=["value"],
            return_type=RWLZType(base_type=BaseType.VOID),
            is_initialized=True,
            is_builtin=True
        )
        # TO DO: more, more, ascend X
        self.global_scope.define(print_func)
    
    def enter_scope(self, name: str = "block"):
        """Enter a new scope"""
        new_scope = Scope(name=name, parent=self.current_scope)
        self.current_scope.children.append(new_scope)
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
    
    def exit_scope(self):
        """Exit the current scope and return to parent"""
        if len(self.scope_stack) <= 1:
            raise RuntimeError("Cannot exit global scope")
        
        self.scope_stack.pop()
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
    
    def define_symbol(self, symbol: Symbol) -> bool:
        """
        Define a new symbol in the current scope.
        Returns False if symbol already exists in current scope.
        """
        return self.current_scope.define(symbol)
    
    def lookup_symbol(self, name: str, current_only: bool = False) -> Optional[Symbol]:
        """
        Look up a symbol by name in current scope or parent scopes.
        """
        return self.current_scope.lookup(name, current_only=current_only)
    
    def define_function(self, func_symbol: FunctionSymbol) -> bool:
        """
        Define a new function in the global scope.
        Functions are always defined at global level.
        """
        # Check in global scope only
        if func_symbol.name in self.global_scope.symbols:
            return False
        return self.global_scope.define(func_symbol)
    
    def lookup_function(self, name: str) -> Optional[FunctionSymbol]:
        """
        Look up a function by name.
        Returns the function symbol if found, None otherwise.
        """
        symbol = self.global_scope.lookup(name, current_only=True)
        if isinstance(symbol, FunctionSymbol):
            return symbol
        return None
    
    def is_in_global_scope(self) -> bool:
        """Check if we're currently in the global scope"""
        return self.current_scope == self.global_scope
    
    def get_scope_level(self) -> int:
        """Get the current scope nesting level (0 = global)"""
        return len(self.scope_stack) - 1
    
    # =========================================================================
    # P R I N T I N G  A N D  S T R I N G I F I C A T I O N   S U P R E M A S Y
    # =========================================================================
    
    def print(self):
        """
        Pretty print the symbol table using Rich tables.
        Compatible with reference code but with enhanced formatting.
        """
        def print_scope(scope: Scope, level: int = 0):
            # Create table for this scope
            indent = "  " * level
            table = Table(title=f"{indent}Symbol Table: '{scope.name}'", show_header=True)
            table.add_column('Name', style='cyan', no_wrap=True)
            table.add_column('Type', style='bright_green')
            table.add_column('Details', style='yellow')
            
            for name, symbol in scope.symbols.items():
                if isinstance(symbol, FunctionSymbol):
                    # Format function
                    params = ", ".join(f"{pt} {pn}" for pt, pn in 
                                      zip(symbol.param_types, symbol.param_names))
                    type_str = f"function"
                    details = f"{symbol.function_kind}: ({params}) -> {symbol.return_type}"
                else:
                    # Format variable
                    const_str = "const " if symbol.is_const else ""
                    init_str = "✓" if symbol.is_initialized else "✗"
                    type_str = str(symbol.symbol_type)
                    details = f"{const_str}[initialized: {init_str}]"
                
                table.add_row(name, type_str, details)
            
            if scope.symbols:  # Only print if has symbols
                rprint(table)
                rprint()  # Empty line
            
            # Recursively print children
            for child in scope.children:
                print_scope(child, level + 1)
        
        rprint("\n[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]")
        rprint("[bold cyan]                 SYMBOL TABLE DUMP                      [/bold cyan]")
        rprint("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")
        print_scope(self.global_scope)
        rprint("[bold cyan]═══════════════════════════════════════════════════════[/bold cyan]\n")
    
    def __str__(self):
        """String representation of the symbol table"""
        def print_scope(scope: Scope, indent: int = 0) -> str:
            result = "  " * indent + str(scope) + "\n"
            for child in scope.children:
                result += print_scope(child, indent + 1)
            return result
        
        return "Symbol Table:\n" + print_scope(self.global_scope)
