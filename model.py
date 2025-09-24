from dataclasses import dataclass, field
from typing import List, Union, Optional
from abc import ABC, abstractmethod

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
    Función helper para asignar números de línea a los nodos del AST.
    Útil para reportar errores precisos durante la compilación.
    """
    if hasattr(node, 'lineno'):
        node.lineno = lineno
        # print(f"[DEBUG] Asignando línea {lineno} a {type(node).__name__}")  # Comentado para salida más limpia
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
    """Clase base para sentencias"""
    pass

@dataclass
class Expression(Node):
    """Clase base para expresiones"""
    pass

@dataclass
class Type(Node):
    """Representa un tipo de dato"""
    name: str

# =====================================================================
# Programa y Metadata
# =====================================================================

@dataclass
class Program(Node):
    """Nodo raíz del programa"""
    metadata: Optional['Metadata']
    functions: List['Function']

@dataclass
class Metadata(Node):
    """Metadatos BepInPlugin"""
    plugin_name: str
    version: str
    guid: str

# =====================================================================
# Tipos
# =====================================================================

@dataclass
class Type(Node):
    """Representa un tipo de dato"""
    name: str
    
    def __str__(self):
        return self.name

# =====================================================================
# Funciones y Parámetros
# =====================================================================

@dataclass
class Function(Node):
    """Clase base para funciones"""
    name: str
    params: List['Parameter']
    body: 'Block'

@dataclass
class BaseFunction(Function):
    """Función con modificador <base>"""
    def __str__(self):
        return f"<base> {self.name}"

@dataclass
class BreedFunction(Function):
    """Función con modificador <breed>"""
    def __str__(self):
        return f"<breed> {self.name}"

@dataclass
class NormalFunction(Function):
    """Función normal sin modificadores"""
    def __str__(self):
        return self.name

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
    """Declaración de variable: tipo nombre = valor;"""
    var_type: Type
    name: str
    value: Expression
    
    def __str__(self):
        return f"{self.var_type} {self.name} = {self.value};"

@dataclass
class Assignment(Statement):
    """Asignación: nombre = valor;"""
    name: str
    value: Expression
    
    def __str__(self):
        return f"{self.name} = {self.value};"

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
class ReturnStatement(Statement):
    """Sentencia return"""
    value: Expression
    
    def __str__(self):
        return f"return {self.value};"

# =====================================================================
# Expresiones
# =====================================================================

@dataclass
class BinaryOperation(Expression):
    """Operación binaria"""
    operator: str
    left: Expression
    right: Expression
    
    def __str__(self):
        return f"({self.left} {self.operator} {self.right})"

@dataclass
class UnaryOperation(Expression):
    """Operación unaria"""
    operator: str
    operand: Expression
    
    def __str__(self):
        return f"{self.operator}{self.operand}"

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
class NumberLiteral(Expression):
    """Literal numérico"""
    value: Union[int, float]
    
    def __str__(self):
        return str(self.value)

@dataclass
class StringLiteral(Expression):
    """Literal de cadena"""
    value: str
    
    def __str__(self):
        return f'"{self.value}"'

@dataclass
class PropExpression(Expression):
    """Expresión <prop>(variable)"""
    variable: str
    
    def __str__(self):
        return f"<prop>({self.variable})"

@dataclass
class BooleanLiteral(Expression):
    """Literal booleano"""
    value: bool
    
    def __str__(self):
        return "true" if self.value else "false"

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
        return f'[BepInPlugin("{node.plugin_name}", "{node.version}", "{node.guid}")]'
    
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
        return f"{self.visit(node.var_type)} {node.name} = {self.visit(node.value)};"
    
    def visit_Assignment(self, node: Assignment):
        return f"{node.name} = {self.visit(node.value)};"
    
    def visit_FunctionCallStmt(self, node: FunctionCallStmt):
        return f"{self.visit(node.call)};"
    
    def visit_IfStatement(self, node: IfStatement):
        result = f"if ({self.visit(node.condition)}) {self.visit(node.then_block)}"
        if node.else_block:
            result += f" else {self.visit(node.else_block)}"
        return result
    
    def visit_ReturnStatement(self, node: ReturnStatement):
        return f"return {self.visit(node.value)};"
    
    def visit_BinaryOperation(self, node: BinaryOperation):
        return f"({self.visit(node.left)} {node.operator} {self.visit(node.right)})"
    
    def visit_UnaryOperation(self, node: UnaryOperation):
        return f"{node.operator}{self.visit(node.operand)}"
    
    def visit_CallExpression(self, node: CallExpression):
        args = ", ".join(self.visit(arg) for arg in node.arguments)
        return f"{node.name}({args})"
    
    def visit_Variable(self, node: Variable):
        return node.name
    
    def visit_NumberLiteral(self, node: NumberLiteral):
        return str(node.value)
    
    def visit_StringLiteral(self, node: StringLiteral):
        return f'"{node.value}"'
    
    def visit_PropExpression(self, node: PropExpression):
        return f"<prop>({node.variable})"
    
    def visit_BooleanLiteral(self, node: BooleanLiteral):
        return "true" if node.value else "false"