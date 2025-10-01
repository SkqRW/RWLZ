from dataclasses import dataclass, field
from typing import List, Union, Optional
from abc import ABC, abstractmethod
from enum import Enum
from .errors import error

# =====================================================================
# Enums
# =====================================================================

class LiteralType(Enum):
    """Enum para tipos de literales"""
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    CHAR = "char"
    BOOLEAN = "boolean"

# Importación opcional de Rich para pretty printing
try:
    from rich.console import Console
    from rich.tree import Tree
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# =====================================================================
# Helper Functions
# =====================================================================

def _L(node, lineno):
    """
    Helper to assign line numbers to AST nodes
    """
    if hasattr(node, 'lineno'):
        node.lineno = lineno
        # print(f"[DEBUG] Asignando línea {lineno} a {type(node).__name__}")
    return node

# =====================================================================
# Clases Base
# =====================================================================

@dataclass
class Node(ABC):
    """Clase base para todos los nodos del AST"""
    lineno: Optional[int] = field(default=None, init=False)
    
    def accept(self, visitor, *args, **kwargs):
        """Patrón Visitor para recorrer el AST"""
        return visitor.visit(self, *args, **kwargs)
    
    def pretty_print(self, indent=0):
        """Imprime el AST de forma legible"""
        if RICH_AVAILABLE:
            console = Console()
            tree = self._build_tree()
            console.print("\n[bold yellow]Árbol de Sintaxis Abstracta (AST):[/bold yellow]")
            console.print(tree)
        else:
            print("\nÁrbol de Sintaxis Abstracta (AST):")
            self._print_simple(indent)
    
    def _build_tree(self, tree=None, is_root=True):
        """Construye un árbol visual del AST usando Rich Tree"""
        if not RICH_AVAILABLE:
            return None
            
        if is_root:
            tree = Tree(f"[bold cyan]{type(self).__name__}[/bold cyan]")
        
        # Agregar información de línea si está disponible
        node_label = f"[bold cyan]{type(self).__name__}[/bold cyan]"
        if self.lineno:
            node_label += f" [dim](línea {self.lineno})[/dim]"
            
        if not is_root:
            tree = tree.add(node_label)
        
        # Agregar campos del dataclass como ramas
        for field_name, field_value in self.__dict__.items():
            if field_name == 'lineno':
                continue
                
            if isinstance(field_value, Node):
                # Nodo hijo
                subtree = tree.add(f"[green]{field_name}[/green]")
                field_value._build_tree(subtree, False)
            elif isinstance(field_value, list) and field_value:
                # Lista de nodos
                list_tree = tree.add(f"[green]{field_name}[/green] ({len(field_value)} elementos)")
                for i, item in enumerate(field_value):
                    if isinstance(item, Node):
                        item_tree = list_tree.add(f"[{i}]")
                        item._build_tree(item_tree, False)
                    else:
                        list_tree.add(f"[{i}]: {item}")
            elif field_value is not None:
                # Valor primitivo
                tree.add(f"[green]{field_name}[/green]: {field_value}")
        
        return tree
    
    def _should_skip_field(self, field_name: str, field_value) -> bool:
        """Determina si un campo debe omitirse en la visualización para evitar redundancia"""
        # Para Parameters, no mostrar 'name' separadamente si ya está incluido en el contexto
        if (field_name == 'name' and 
            hasattr(self, 'param_type') and 
            type(self).__name__ == 'Parameter'):
            return True
        
        # Agregar más reglas de filtrado según sea necesario
        return False
    
    def _print_simple(self, indent=0):
        """Imprime el AST de forma simple sin Rich"""
        prefix = "  " * indent
        node_info = f"{type(self).__name__}"
        if self.lineno:
            node_info += f" (línea {self.lineno})"
        print(f"{prefix}{node_info}")
        
        for field_name, field_value in self.__dict__.items():
            if field_name == 'lineno':
                continue
                
            if isinstance(field_value, Node):
                print(f"{prefix}  {field_name}:")
                field_value._print_simple(indent + 2)
            elif isinstance(field_value, list) and field_value:
                print(f"{prefix}  {field_name}: [{len(field_value)} elementos]")
                for i, item in enumerate(field_value):
                    if isinstance(item, Node):
                        print(f"{prefix}    [{i}]:")
                        item._print_simple(indent + 3)
                    else:
                        print(f"{prefix}    [{i}]: {item}")
            elif field_value is not None:
                print(f"{prefix}  {field_name}: {field_value}")

@dataclass
class Statement(Node):
    pass

@dataclass 
class Expression(Node):
    pass

@dataclass
class Literal(Expression):
    value : Union[int, float, str, bool]
    type  : Optional[LiteralType] = None

# =====================================================================
# Program y Metadata
# =====================================================================

@dataclass
class Program(Statement):
    """ Main Node of the language """
    metadata: Optional['Metadata']
    functions: List['Function']

@dataclass
class Metadata(Statement):
    """ Metadatos BepInPlugin """
    ID: str
    NAME: str
    VERSION: str
@dataclass
class Type(Node):
    name: str
    
    def __str__(self):
        return self.name

# =====================================================================
# Funciones y Parámetros
# =====================================================================

@dataclass
class Function(Node):
    name: str
    params: List['Parameter']
    body: 'Block'
    return_type: Optional['Type'] = None

@dataclass
class BaseFunction(Function):
    """Función con modificador <base>"""
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"<base> {self.name}{return_str}"

@dataclass
class BreedFunction(Function):
    """Función con modificador <breed>"""
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"<breed> {self.name}{return_str}"

@dataclass
class NormalFunction(Function):
    """Función normal sin modificadores"""
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"{self.name}{return_str}"

@dataclass
class Parameter(Node):
    """Parámetro de función"""
    name: str
    param_type: Type
    
    def __str__(self):
        return f"{self.param_type} {self.name}"

# =====================================================================
# Sentencias
# =====================================================================

@dataclass
class Block(Statement):
    """Bloque de código { ... }"""
    statements: List[Statement]

@dataclass
class VarDecl(Statement):
    var_type: Type
    name: str
    value: Optional[Literal] = None
    is_const: bool = False
    
    def __post_init__(self):
        if self.is_const and self.value is None:
            error(f"The const '{self.name}' should have an initial value", self.lineno)
    
    def __str__(self):
        const_str = "const " if self.is_const else ""
        if self.value:
            return f"{const_str}{self.var_type} {self.name} = {self.value};"
        return f"{const_str}{self.var_type} {self.name};"

@dataclass
class ArrayDecl(Statement):
    var_type: Type
    name: str
    size: Optional[Expression] = None
    values: Optional[List[Expression]] = None
    is_const: bool = False
    
    def __str__(self):
        const_str = "const " if self.is_const else ""
        size_str = f"[{self.size}]" if self.size else "[]"
        if self.values:
            vals = ", ".join(str(v) for v in self.values)
            return f"{const_str}{self.var_type} {self.name}{size_str} = [{vals}];"
        return f"{const_str}{self.var_type} {self.name}{size_str};"

class Location(Expression):
    pass

@dataclass
class VarLocation(Location):
    name: str
    def __str__(self):
        return self.name

@dataclass
class ArrayLocation(Location):
    name: str
    index: Expression
    def __str__(self):
        return f"{self.name}[{self.index}]"

@dataclass
class Assignment(Statement):
    target: Location
    operator: str
    value: Expression
    
    def __str__(self):
        return f"{self.target} {self.operator} {self.value};"

@dataclass
class IncrementStatement(Statement):
    """Incremento/decremento como sentencia: ++var, var++, --var, var--"""
    variable: str
    operator: str  # ++, --
    is_prefix: bool  # True para ++var, False para var++
    
    def __str__(self):
        if self.is_prefix:
            return f"{self.operator}{self.variable};"
        return f"{self.variable}{self.operator};"

@dataclass
class FunctionCallStmt(Statement):
    """Llamada a función como sentencia"""
    call: 'CallExpression'
    
    def __str__(self):
        return f"{self.call};"

@dataclass
class IfStatement(Statement):
    """Sentencia if"""
    condition: Expression
    then_block: Block
    else_block: Optional[Block] = None
    
    def __str__(self):
        if self.else_block:
            return f"if ({self.condition}) {{ ... }} else {{ ... }}"
        return f"if ({self.condition}) {{ ... }}"

@dataclass
class WhileStatement(Statement):
    """Sentencia while"""
    condition: Expression
    body: Block
    
    def __str__(self):
        return f"while ({self.condition}) {{ ... }}"

@dataclass
class ForStatement(Statement):
    """Sentencia for"""
    init: Optional[Statement]  # Inicialización
    condition: Optional[Expression]  # Condición
    update: Optional[Statement]  # Actualización
    body: Block
    
    def __str__(self):
        init_str = str(self.init) if self.init else ""
        cond_str = str(self.condition) if self.condition else ""
        update_str = str(self.update) if self.update else ""
        return f"for ({init_str} {cond_str}; {update_str}) {{ ... }}"

@dataclass
class BreakStatement(Statement):
    """Sentencia break"""
    
    def __str__(self):
        return "break;"

@dataclass
class ContinueStatement(Statement):
    """Sentencia continue"""
    
    def __str__(self):
        return "continue;"

@dataclass
class ReturnStatement(Statement):
    """Sentencia return"""
    value: Optional[Expression] = None
    
    def __str__(self):
        if self.value:
            return f"return {self.value};"
        return "return;"

@dataclass
class PrintStatement(Statement):
    """Sentencia print"""
    expression: Expression
    
    def __str__(self):
        return f"print({self.expression});"

# =====================================================================
# Expresiones
# =====================================================================

@dataclass
class BinOper(Expression):
    operator: str
    left: Expression
    right: Expression
    
    def __str__(self):
        return f"({self.left} {self.operator} {self.right})"

@dataclass
class UnaryOper(Expression):
    operator: str
    operand: Expression
    
    def __str__(self):
        return f"{self.operator}{self.operand}"

@dataclass
class IncrementExpression(Expression):
    variable: str
    operator: str  # ++, --
    is_prefix: bool  # True para ++var, False para var++
    
    def __str__(self):
        if self.is_prefix:
            return f"{self.operator}{self.variable}"
        return f"{self.variable}{self.operator}"

@dataclass
class AssignmentExpression(Expression):
    """Expresión de asignación: var = valor, var += valor, etc."""
    variable: str
    operator: str  # =, +=, -=, *=, /=
    value: Expression
    
    def __str__(self):
        return f"{self.variable} {self.operator} {self.value}"

@dataclass
class ArrayAccess(Expression):
    """Acceso a array: nombre[índice]"""
    name: str
    index: Expression
    
    def __str__(self):
        return f"{self.name}[{self.index}]"

@dataclass
class ArrayLiteral(Expression):
    """Literal de array: [1, 2, 3]"""
    elements: List[Expression]
    
    def __str__(self):
        elements_str = ", ".join(str(e) for e in self.elements)
        return f"[{elements_str}]"

@dataclass
class CallExpression(Expression):
    """Llamada a función como expresión"""
    name: str
    arguments: List[Expression]
    
    def __str__(self):
        args = ", ".join(str(arg) for arg in self.arguments)
        return f"{self.name}({args})"

@dataclass
class Variable(Expression):
    """Variable"""
    name: str
    
    def __str__(self):
        return self.name

@dataclass
class NumberLiteral(Literal):
    """Literal numérico"""
    value: Union[int, float]
    
    def __str__(self):
        return str(self.value)
    
@dataclass  
class Float(Literal):
    value: float
    def __post_init__(self):
        assert isinstance(self.value, float), "The value should be a 'float'"
        self.type = LiteralType.FLOAT

    def __str__(self):
        return str(self.value)

@dataclass
class Integer(Literal):
    value: int
    def __post_init__(self):
        assert isinstance(self.value, int), "The value should be an 'integer'"
        self.type = LiteralType.INT

    def __str__(self):
        return str(self.value)

@dataclass
class String(Literal):
    value: str

    def __post_init__(self):
        assert isinstance(self.value, str), "The value should be a 'string'"
        self.type = LiteralType.STRING

    def __str__(self):
        return f'"{self.value}"'

@dataclass
class Char(Literal):   
    value: str

    def __post_init__(self):
        assert isinstance(self.value, str), "The value should be a 'char'"
        assert len(self.value) == 1, "Char must be a single character"
        self.type = LiteralType.CHAR
    
    def __str__(self):
        return f"'{self.value}'"

@dataclass
class Boolean(Literal):
    value: bool

    def __post_init__(self):
        assert isinstance(self.value, bool), "The value should be a 'boolean'"
        self.type = LiteralType.BOOLEAN
    
    def __str__(self):
        return "true" if self.value else "false"

@dataclass
class PropExpression(Expression):
    """Expresión <prop>(variable)"""
    variable: str
    
    def __str__(self):
        return f"<prop>({self.variable})"

@dataclass
class BaseExpression(Expression):
    """Expresión <base>(expression)"""
    expression: Expression
    
    def __str__(self):
        return f"<base>({self.expression})"

@dataclass
class BreedExpression(Expression):
    """Expresión <breed>(expression)"""
    expression: Expression
    
    def __str__(self):
        return f"<breed>({self.expression})"

# =====================================================================
# Visitor Pattern
# =====================================================================

class Visitor(ABC):
    """Clase base para implementar el patrón Visitor"""
    
    def visit(self, node: Node, *args, **kwargs):
        """Punto de entrada principal para visitar un nodo"""
        method_name = f'visit_{type(node).__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node, *args, **kwargs)

    def generic_visit(self, node: Node, *args, **kwargs):
        """Método por defecto para nodos no manejados"""
        raise NotImplementedError(f"No hay método visit_{type(node).__name__} en {type(self).__name__}")

# =====================================================================
# Visitor de ejemplo: Pretty Printer
# =====================================================================

class PrettyPrinter(Visitor):
    """Visitor que imprime el código de forma legible"""
    
    def __init__(self, indent_size=2):
        self.indent_size = indent_size
        self.indent_level = 0
    
    def _indent(self):
        return " " * (self.indent_level * self.indent_size)
    
    def visit_Program(self, node: Program):
        result = ""
        if node.metadata:
            result += self.visit(node.metadata) + "\n\n"
        
        for i, func in enumerate(node.functions):
            if i > 0:
                result += "\n"
            result += self.visit(func)
        
        return result
    
    def visit_Metadata(self, node: Metadata):
        return f'[BepInPlugin("{node.ID}", "{node.VERSION}", "{node.NAME}")]'
    
    def visit_BaseFunction(self, node: BaseFunction):
        return self._visit_function(node, "<base>")
    
    def visit_BreedFunction(self, node: BreedFunction):
        return self._visit_function(node, "<breed>")
    
    def visit_NormalFunction(self, node: NormalFunction):
        return self._visit_function(node, "")
    
    def _visit_function(self, node: Function, modifier=""):
        params = ", ".join(self.visit(param) for param in node.params)
        header = f"{modifier} {node.name}({params})" if modifier else f"{node.name}({params})"
        body = self.visit(node.body)
        return f"{header} {body}"
    
    def visit_Parameter(self, node: Parameter):
        return f"{self.visit(node.param_type)} {node.name}"
    
    def visit_Type(self, node: Type):
        return node.name
    
    def visit_Block(self, node: Block):
        self.indent_level += 1
        statements = []
        for stmt in node.statements:
            statements.append(self._indent() + self.visit(stmt))
        self.indent_level -= 1
        
        if not statements:
            return "{ }"
        
        return "{\n" + "\n".join(statements) + "\n" + self._indent() + "}"
    
    def visit_VarDecl(self, node: VarDecl):
        const_str = "const " if node.is_const else ""
        if node.value:
            return f"{const_str}{self.visit(node.var_type)} {node.name} = {self.visit(node.value)};"
        return f"{const_str}{self.visit(node.var_type)} {node.name};"
    
    def visit_ArrayDecl(self, node: ArrayDecl):
        const_str = "const " if node.is_const else ""
        size_str = f"[{self.visit(node.size)}]" if node.size else "[]"
        if node.values:
            vals = ", ".join(self.visit(v) for v in node.values)
            return f"{const_str}{self.visit(node.var_type)} {node.name}{size_str} = [{vals}];"
        return f"{const_str}{self.visit(node.var_type)} {node.name}{size_str};"
    
    def visit_Assignment(self, node: Assignment):
        return f"{node.name} = {self.visit(node.value)};"

    
    def visit_IncrementStatement(self, node: IncrementStatement):
        if node.is_prefix:
            return f"{node.operator}{node.variable};"
        return f"{node.variable}{node.operator};"
    
    def visit_FunctionCallStmt(self, node: FunctionCallStmt):
        return f"{self.visit(node.call)};"
    
    def visit_IfStatement(self, node: IfStatement):
        result = f"if ({self.visit(node.condition)}) {self.visit(node.then_block)}"
        if node.else_block:
            result += f" else {self.visit(node.else_block)}"
        return result
    
    def visit_WhileStatement(self, node: WhileStatement):
        return f"while ({self.visit(node.condition)}) {self.visit(node.body)}"
    
    def visit_ForStatement(self, node: ForStatement):
        init_str = self.visit(node.init).rstrip(';') if node.init else ""
        cond_str = self.visit(node.condition) if node.condition else ""
        update_str = self.visit(node.update).rstrip(';') if node.update else ""
        return f"for ({init_str}; {cond_str}; {update_str}) {self.visit(node.body)}"
    
    def visit_BreakStatement(self, node: BreakStatement):
        return "break;"
    
    def visit_ContinueStatement(self, node: ContinueStatement):
        return "continue;"
    
    def visit_ReturnStatement(self, node: ReturnStatement):
        if node.value:
            return f"return {self.visit(node.value)};"
        return "return;"
    
    def visit_PrintStatement(self, node: PrintStatement):
        return f"print({self.visit(node.expression)});"
    
    def visit_BinaryOperation(self, node: BinOper):
        return f"({self.visit(node.left)} {node.operator} {self.visit(node.right)})"
    
    def visit_UnaryOperation(self, node: UnaryOper):
        return f"{node.operator}{self.visit(node.operand)}"
    
    def visit_IncrementExpression(self, node: IncrementExpression):
        if node.is_prefix:
            return f"{node.operator}{node.variable}"
        return f"{node.variable}{node.operator}"
    
    def visit_AssignmentExpression(self, node: AssignmentExpression):
        return f"{node.variable} {node.operator} {self.visit(node.value)}"
    
    def visit_ArrayAccess(self, node: ArrayAccess):
        return f"{node.name}[{self.visit(node.index)}]"
    
    def visit_ArrayLiteral(self, node: ArrayLiteral):
        elements = ", ".join(self.visit(e) for e in node.elements)
        return f"[{elements}]"
    
    def visit_CallExpression(self, node: CallExpression):
        args = ", ".join(self.visit(arg) for arg in node.arguments)
        return f"{node.name}({args})"
    
    def visit_Variable(self, node: Variable):
        return node.name
    
    def visit_NumberLiteral(self, node: NumberLiteral):
        return str(node.value)
    
    def visit_StringLiteral(self, node: String):
        return f'"{node.value}"'
    
    def visit_CharLiteral(self, node: Char):
        return f"'{node.value}'"
    
    def visit_BooleanLiteral(self, node: Boolean):
        return "true" if node.value else "false"
    
    def visit_PropExpression(self, node: PropExpression):
        return f"<prop>({node.variable})"
    
    def visit_BaseExpression(self, node: BaseExpression):
        return f"<base>({self.visit(node.expression)})"
    
    def visit_BreedExpression(self, node: BreedExpression):
        return f"<breed>({self.visit(node.expression)})"