"""
Módulo para patrones de visita (Visitor Pattern) del AST.

Este módulo contiene la implementación del patrón Visitor para recorrer y procesar
árboles de sintaxis abstracta, incluyendo la clase base Visitor y implementaciones
específicas como PrettyPrinter para generar código legible.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

# Importación para type checking
if TYPE_CHECKING:
    from .model import Node, Program, Metadata, Function, Parameter, Type, Block
    from .model import VarDecl, ArrayDecl, Assignment, VarLocation, ArrayLocation
    from .model import FunctionCallStmt, IfStatement, WhileStatement, ForStatement
    from .model import BreakStatement, ContinueStatement, ReturnStatement, PrintStatement
    from .model import BinOper, UnaryOper, IncrementExpression, AssignmentExpression
    from .model import ArrayAccess, ArrayLiteral, CallExpression, Variable
    from .model import Integer, Float, String, Char, Boolean
    from .model import PropExpression, BaseExpression, BreedExpression, HookExpression
    from .model import BaseFunction, BreedFunction, HookFunction, NormalFunction


# =====================================================================
# Visitor Pattern Base
# =====================================================================

class Visitor(ABC):
    """Clase base para implementar el patrón Visitor"""
    
    def visit(self, node: 'Node', *args, **kwargs):
        """Punto de entrada principal para visitar un nodo"""
        method_name = f'visit_{type(node).__name__}'
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node, *args, **kwargs)

    def generic_visit(self, node: 'Node', *args, **kwargs):
        """Método por defecto para nodos no manejados"""
        raise NotImplementedError(f"No hay método visit_{type(node).__name__} en {type(self).__name__}")


# =====================================================================
# Implementaciones del Visitor Pattern
# =====================================================================

class PrettyPrinter(Visitor):
    """Visitor que imprime el código de forma legible"""
    
    def __init__(self, indent_size=2):
        self.indent_size = indent_size
        self.indent_level = 0
    
    def _indent(self):
        return " " * (self.indent_level * self.indent_size)
    
    def visit_Program(self, node: 'Program'):
        result = ""
        if node.metadata:
            result += self.visit(node.metadata) + "\n\n"
        
        for i, func in enumerate(node.functions):
            if i > 0:
                result += "\n"
            result += self.visit(func)
        
        return result
    
    def visit_Metadata(self, node: 'Metadata'):
        return f'[BepInPlugin("{node.ID}", "{node.VERSION}", "{node.NAME}")]'
    
    def visit_BaseFunction(self, node: 'BaseFunction'):
        return self._visit_function(node, "<base>")
    
    def visit_BreedFunction(self, node: 'BreedFunction'):
        return self._visit_function(node, "<breed>")
    
    def visit_HookFunction(self, node: 'HookFunction'):
        return self._visit_function(node, "<hook>")
    
    def visit_NormalFunction(self, node: 'NormalFunction'):
        return self._visit_function(node, "")
    
    def _visit_function(self, node: 'Function', modifier=""):
        params = ", ".join(self.visit(param) for param in node.params)
        header = f"{modifier} {node.name}({params})" if modifier else f"{node.name}({params})"
        body = self.visit(node.body)
        return f"{header} {body}"
    
    def visit_Parameter(self, node: 'Parameter'):
        return f"{self.visit(node.param_type)} {node.name}"
    
    def visit_Type(self, node: 'Type'):
        return node.name
    
    def visit_Block(self, node: 'Block'):
        self.indent_level += 1
        statements = []
        for stmt in node.statements:
            statements.append(self._indent() + self.visit(stmt))
        self.indent_level -= 1
        
        if not statements:
            return "{ }"
        
        return "{\n" + "\n".join(statements) + "\n" + self._indent() + "}"
    
    def visit_VarDecl(self, node: 'VarDecl'):
        const_str = "const " if node.is_const else ""
        if node.value:
            return f"{const_str}{self.visit(node.var_type)} {node.name} = {self.visit(node.value)};"
        return f"{const_str}{self.visit(node.var_type)} {node.name};"
    
    def visit_ArrayDecl(self, node: 'ArrayDecl'):
        const_str = "const " if node.is_const else ""
        size_str = f"[{self.visit(node.size)}]" if node.size else "[]"
        if node.values:
            vals = ", ".join(self.visit(v) for v in node.values)
            return f"{const_str}{self.visit(node.var_type)} {node.name}{size_str} = [{vals}];"
        return f"{const_str}{self.visit(node.var_type)} {node.name}{size_str};"
    
    def visit_Assignment(self, node: 'Assignment'):
        if node.operator in ["++", "--"]:
            if node.is_prefix:
                return f"{node.operator}{self.visit(node.target)};"
            else:
                return f"{self.visit(node.target)}{node.operator};"
        return f"{self.visit(node.target)} {node.operator} {self.visit(node.value)};"

    def visit_VarLocation(self, node: 'VarLocation'):
        return node.name
    
    def visit_ArrayLocation(self, node: 'ArrayLocation'):
        return f"{node.name}[{self.visit(node.index)}]"
    
    def visit_FunctionCallStmt(self, node: 'FunctionCallStmt'):
        return f"{self.visit(node.call)};"
    
    def visit_IfStatement(self, node: 'IfStatement'):
        result = f"if ({self.visit(node.condition)}) {self.visit(node.then_block)}"
        if node.else_block:
            result += f" else {self.visit(node.else_block)}"
        return result
    
    def visit_WhileStatement(self, node: 'WhileStatement'):
        return f"while ({self.visit(node.condition)}) {self.visit(node.body)}"
    
    def visit_ForStatement(self, node: 'ForStatement'):
        init_str = self.visit(node.init).rstrip(';') if node.init else ""
        cond_str = self.visit(node.condition) if node.condition else ""
        update_str = self.visit(node.update).rstrip(';') if node.update else ""
        return f"for ({init_str}; {cond_str}; {update_str}) {self.visit(node.body)}"
    
    def visit_BreakStatement(self, node: 'BreakStatement'):
        return "break;"
    
    def visit_ContinueStatement(self, node: 'ContinueStatement'):
        return "continue;"
    
    def visit_ReturnStatement(self, node: 'ReturnStatement'):
        if node.value:
            return f"return {self.visit(node.value)};"
        return "return;"
    
    def visit_PrintStatement(self, node: 'PrintStatement'):
        return f"print({self.visit(node.expression)});"
    
    def visit_BinOper(self, node: 'BinOper'):
        return f"({self.visit(node.left)} {node.operator} {self.visit(node.right)})"
    
    def visit_UnaryOper(self, node: 'UnaryOper'):
        return f"{node.operator}{self.visit(node.operand)}"
    
    def visit_IncrementExpression(self, node: 'IncrementExpression'):
        if node.is_prefix:
            return f"{node.operator}{node.variable}"
        return f"{node.variable}{node.operator}"
    
    def visit_AssignmentExpression(self, node: 'AssignmentExpression'):
        return f"{node.variable} {node.operator} {self.visit(node.value)}"
    
    def visit_ArrayAccess(self, node: 'ArrayAccess'):
        return f"{node.name}[{self.visit(node.index)}]"
    
    def visit_ArrayLiteral(self, node: 'ArrayLiteral'):
        elements = ", ".join(self.visit(e) for e in node.elements)
        return f"[{elements}]"
    
    def visit_CallExpression(self, node: 'CallExpression'):
        args = ", ".join(self.visit(arg) for arg in node.arguments)
        return f"{node.name}({args})"
    
    def visit_Variable(self, node: 'Variable'):
        return node.name
    
    def visit_Integer(self, node: 'Integer'):
        return str(node.value)

    def visit_Float(self, node: 'Float'):
        return str(node.value)

    def visit_String(self, node: 'String'):
        return f'"{node.value}"'
    
    def visit_Char(self, node: 'Char'):
        return f"'{node.value}'"
    
    def visit_Boolean(self, node: 'Boolean'):
        return "true" if node.value else "false"
    
    def visit_PropExpression(self, node: 'PropExpression'):
        return f"<prop>({node.variable})"
    
    def visit_BaseExpression(self, node: 'BaseExpression'):
        return f"<base>({self.visit(node.expression)})"
    
    def visit_BreedExpression(self, node: 'BreedExpression'):
        return f"<breed>({self.visit(node.expression)})"
    
    def visit_HookExpression(self, node: 'HookExpression'):
        return f"<hook>({self.visit(node.expression)})"


# =====================================================================
# Utilidades para el Visitor Pattern
# =====================================================================

class ASTTraverser(Visitor):
    """
    Visitor utilitario que recorre el AST sin procesar nada.
    Útil como clase base para visitors que necesitan recorrer todo el árbol.
    """
    
    def generic_visit(self, node: 'Node', *args, **kwargs):
        """Recorre automáticamente todos los nodos hijos"""
        # Recorrer todos los campos del nodo
        for field_name, field_value in node.__dict__.items():
            if hasattr(field_value, 'accept'):
                # Es un nodo AST
                self.visit(field_value, *args, **kwargs)
            elif isinstance(field_value, list):
                # Es una lista, posiblemente de nodos AST
                for item in field_value:
                    if hasattr(item, 'accept'):
                        self.visit(item, *args, **kwargs)


class NodeCollector(ASTTraverser):
    """
    Visitor que recolecta todos los nodos de un tipo específico del AST.
    
    Ejemplo de uso:
        collector = NodeCollector(VarDecl)
        collector.visit(ast_root)
        variables = collector.nodes  # Lista de todos los VarDecl encontrados
    """
    
    def __init__(self, target_type):
        super().__init__()
        self.target_type = target_type
        self.nodes = []
    
    def generic_visit(self, node: 'Node', *args, **kwargs):
        # Si el nodo es del tipo que buscamos, lo agregamos
        if isinstance(node, self.target_type):
            self.nodes.append(node)
        
        # Continuar con el recorrido normal
        super().generic_visit(node, *args, **kwargs)


class NodeCounter(ASTTraverser):
    """
    Visitor que cuenta diferentes tipos de nodos en el AST.
    """
    
    def __init__(self):
        super().__init__()
        self.counts = {}
    
    def generic_visit(self, node: 'Node', *args, **kwargs):
        # Contar este tipo de nodo
        node_type = type(node).__name__
        self.counts[node_type] = self.counts.get(node_type, 0) + 1
        
        # Continuar con el recorrido normal
        super().generic_visit(node, *args, **kwargs)