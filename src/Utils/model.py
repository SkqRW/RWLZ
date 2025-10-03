from dataclasses import dataclass, field
from typing import List, Union, Optional
from abc import ABC, abstractmethod
from enum import Enum
from .errors import error

# =====================================================================
# Enums
# =====================================================================

class LiteralType(Enum):
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    CHAR = "char"
    BOOLEAN = "boolean"
    VOID = "void"


def _L(node, lineno):
    """ Assign lines to AST nodes """
    if hasattr(node, 'lineno'):
        node.lineno = lineno
    return node

@dataclass
class Node(ABC):
    lineno: Optional[int] = field(default=None, init=False)
    
    def accept(self, visitor, *args, **kwargs):
        return visitor.visit(self, *args, **kwargs)

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
    """ Metadata for BepInPlugin """
    ID: str
    NAME: str
    VERSION: str
@dataclass
class Type(Node):
    """ Data type representation """
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
    """ Function override creature stuff """
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"<base> {self.name}{return_str}"

@dataclass
class BreedFunction(Function):
    """ Breed params to hook custom interactions """
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"<breed> {self.name}{return_str}"

@dataclass
class HookFunction(Function):
    """ External game hooks """
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"<hook> {self.name}{return_str}"

@dataclass
class NormalFunction(Function):
    """ Normal user-defined function """
    def __str__(self):
        return_str = f" -> {self.return_type}" if self.return_type else ""
        return f"{self.name}{return_str}"
    
@dataclass
class Parameter(Node):
    name: str
    param_type: Type
    
    def __str__(self):
        return f"{self.param_type} {self.name}"

# =====================================================================
# Sentencias
# =====================================================================

@dataclass
class Block(Statement):
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
    value: Optional[Expression] = None

    operator: str = ""  # None for ++/--
    is_prefix: Optional[bool] = None  # Only for ++/--

    def __str__(self):
        if self.operator in ["++", "--"]:
            if self.is_prefix:
                return f"{self.operator}{self.target};"
            else:
                return f"{self.target}{self.operator};"
        return f"{self.target} {self.operator} {self.value};"

@dataclass
class FunctionCallStmt(Statement):
    call: 'CallExpression'
    
    def __str__(self):
        return f"{self.call};"

@dataclass
class IfStatement(Statement):
    condition: Expression
    then_block: Block
    else_block: Optional[Block] = None
    
    def __str__(self):
        if self.else_block:
            return f"if ({self.condition}) {{ ... }} else {{ ... }}"
        return f"if ({self.condition}) {{ ... }}"

@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Block
    
    def __str__(self):
        return f"while ({self.condition}) {{ ... }}"

@dataclass
class ForStatement(Statement):
    init: Optional[Statement] 
    condition: Optional[Expression]
    update: Optional[Statement]
    body: Block
    
    def __str__(self):
        init_str = str(self.init) if self.init else ""
        cond_str = str(self.condition) if self.condition else ""
        update_str = str(self.update) if self.update else ""
        return f"for ({init_str} {cond_str}; {update_str}) {{ ... }}"

@dataclass
class BreakStatement(Statement):

    def __str__(self):
        return "break;"

@dataclass
class ContinueStatement(Statement):

    def __str__(self):
        return "continue;"

@dataclass
class ReturnStatement(Statement):
    value: Optional[Expression] = None
    
    def __str__(self):
        if self.value:
            return f"return {self.value};"
        return "return;"

@dataclass
class PrintStatement(Statement):
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
    
@dataclass
class HookExpression(Expression):
    """Expresión <breed>(expression)"""
    expression: Expression
    
    def __str__(self):
        return f"<breed>({self.expression})"

