"""
Módulo para visualización y pretty printing del AST (Abstract Syntax Tree).

Este módulo contiene utilidades para imprimir y visualizar árboles de sintaxis abstracta
de manera legible, tanto con Rich (si está disponible) como con impresión simple.
También incluye funcionalidades para generar gráficos PNG usando Graphviz y mostrar
análisis resumidos del AST.
"""

import os
import subprocess
import platform
from typing import TYPE_CHECKING

# Importación opcional de Rich para pretty printing
try:
    from rich.console import Console
    from rich.tree import Tree
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Importación opcional de Graphviz para generar PNG
try:
    from graphviz import Digraph
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

# Importación para type checking
if TYPE_CHECKING:
    from .model import Node


class ASTFormatter:
    """Clase utilitaria para formatear e imprimir AST nodes."""
    
    @staticmethod
    def pretty_print(node: 'Node', indent: int = 0) -> None:
        """
        Imprime el AST de forma legible usando Rich si está disponible,
        o usando impresión simple como alternativa.
        
        Args:
            node: El nodo AST a imprimir
            indent: Nivel de indentación inicial (usado en impresión simple)
        """
        if RICH_AVAILABLE:
            console = Console()
            tree = ASTFormatter._build_tree(node)
            console.print("\n[bold yellow]Árbol de Sintaxis Abstracta (AST):[/bold yellow]")
            console.print(tree)
        else:
            print("\nÁrbol de Sintaxis Abstracta (AST):")
            ASTFormatter._print_simple(node, indent)
    
    @staticmethod
    def _build_tree(node: 'Node', tree=None, is_root: bool = True):
        """
        Construye un árbol visual del AST usando Rich Tree.
        
        Args:
            node: El nodo AST a procesar
            tree: El árbol Rich al que agregar el nodo (None para crear uno nuevo)
            is_root: Si este es el nodo raíz del árbol
            
        Returns:
            Rich Tree object representando el AST
        """
        if not RICH_AVAILABLE:
            return None
            
        if is_root:
            tree = Tree(f"[bold cyan]{type(node).__name__}[/bold cyan]")
        
        # Agregar información de línea si está disponible
        node_label = f"[bold cyan]{type(node).__name__}[/bold cyan]"
        if hasattr(node, 'lineno') and node.lineno:
            node_label += f" [dim](línea {node.lineno})[/dim]"
            
        if not is_root:
            tree = tree.add(node_label)
        
        # Agregar campos del dataclass como ramas
        for field_name, field_value in node.__dict__.items():
            if field_name == 'lineno':
                continue
            
            # Usar el método de filtrado si existe
            if hasattr(node, '_should_skip_field') and node._should_skip_field(field_name, field_value):
                continue
                
            if ASTFormatter._is_node(field_value):
                # Nodo hijo
                subtree = tree.add(f"[green]{field_name}[/green]")
                ASTFormatter._build_tree(field_value, subtree, False)
            elif isinstance(field_value, list) and field_value:
                # Lista de nodos
                list_tree = tree.add(f"[green]{field_name}[/green] ({len(field_value)} elementos)")
                for i, item in enumerate(field_value):
                    if ASTFormatter._is_node(item):
                        item_tree = list_tree.add(f"[{i}]")
                        ASTFormatter._build_tree(item, item_tree, False)
                    else:
                        list_tree.add(f"[{i}]: {item}")
            elif field_value is not None:
                # Valor primitivo
                tree.add(f"[green]{field_name}[/green]: {field_value}")
        
        return tree
    
    @staticmethod
    def _print_simple(node: 'Node', indent: int = 0) -> None:
        """
        Imprime el AST de forma simple sin Rich.
        
        Args:
            node: El nodo AST a imprimir
            indent: Nivel de indentación
        """
        prefix = "  " * indent
        node_info = f"{type(node).__name__}"
        if hasattr(node, 'lineno') and node.lineno:
            node_info += f" (línea {node.lineno})"
        print(f"{prefix}{node_info}")
        
        for field_name, field_value in node.__dict__.items():
            if field_name == 'lineno':
                continue
            
            # Usar el método de filtrado si existe
            if hasattr(node, '_should_skip_field') and node._should_skip_field(field_name, field_value):
                continue
                
            if ASTFormatter._is_node(field_value):
                print(f"{prefix}  {field_name}:")
                ASTFormatter._print_simple(field_value, indent + 2)
            elif isinstance(field_value, list) and field_value:
                print(f"{prefix}  {field_name}: [{len(field_value)} elementos]")
                for i, item in enumerate(field_value):
                    if ASTFormatter._is_node(item):
                        print(f"{prefix}    [{i}]:")
                        ASTFormatter._print_simple(item, indent + 3)
                    else:
                        print(f"{prefix}    [{i}]: {item}")
            elif field_value is not None:
                print(f"{prefix}  {field_name}: {field_value}")
    
    @staticmethod
    def _is_node(obj) -> bool:
        """
        Verifica si un objeto es un nodo AST.
        
        Args:
            obj: El objeto a verificar
            
        Returns:
            True si el objeto es un nodo AST, False en caso contrario
        """
        # Evitamos importación circular usando duck typing
        return hasattr(obj, 'accept') and hasattr(obj, 'lineno')


def should_skip_field(node: 'Node', field_name: str, field_value) -> bool:
    """
    Determina si un campo debe omitirse en la visualización para evitar redundancia.
    
    Args:
        node: El nodo que contiene el campo
        field_name: Nombre del campo
        field_value: Valor del campo
        
    Returns:
        True si el campo debe omitirse, False en caso contrario
    """
    # Para Parameters, no mostrar 'name' separadamente si ya está incluido en el contexto
    if (field_name == 'name' and 
        hasattr(node, 'param_type') and 
        type(node).__name__ == 'Parameter'):
        return True
    
    # Agregar más reglas de filtrado según sea necesario
    return False


def print_ast(ast_root):
    """
    Imprime el AST de manera visual usando Rich Tree con nodos tipados.
    
    Args:
        ast_root: El nodo raíz del AST a imprimir
    """
    if ast_root is None:
        if RICH_AVAILABLE:
            from rich import print
            print("❌ [red]Error: No se pudo generar el AST[/red]")
        else:
            print("❌ Error: No se pudo generar el AST")
        return
    
    # Usar el formateador si el nodo es de nuestro modelo
    if ASTFormatter._is_node(ast_root):
        ASTFormatter.pretty_print(ast_root)
    else:
        # Fallback para compatibilidad con tuplas (código legacy)
        if not RICH_AVAILABLE:
            print("Árbol de Sintaxis Abstracta (AST):")
            print(str(ast_root))
            return
            
        console = Console()
        
        def build_tree(node, parent_tree=None):
            if isinstance(node, tuple) and len(node) > 0:
                # El primer elemento es el tipo de nodo
                node_type = str(node[0])
                
                # Crear el nodo del árbol con estilo
                if parent_tree is None:
                    tree = Tree(f"[bold blue]{node_type}[/bold blue]")
                else:
                    tree = parent_tree.add(f"[bold green]{node_type}[/bold green]")
                
                # Procesar el resto de elementos
                for i, child in enumerate(node[1:], 1):
                    if isinstance(child, (tuple, list)):
                        build_tree(child, tree)
                    else:
                        # Es un valor terminal
                        tree.add(f"[yellow]{repr(child)}[/yellow]")
                
                return tree
                
            elif isinstance(node, list):
                # Lista de nodos
                if parent_tree is None:
                    tree = Tree("[bold cyan]List[/bold cyan]")
                else:
                    tree = parent_tree.add("[bold cyan]List[/bold cyan]")
                
                for item in node:
                    build_tree(item, tree)
                
                return tree
            else:
                # Valor simple
                if parent_tree is None:
                    return Tree(f"[yellow]{repr(node)}[/yellow]")
                else:
                    parent_tree.add(f"[yellow]{repr(node)}[/yellow]")
                    return parent_tree
        
        # Construir y mostrar el árbol
        tree = build_tree(ast_root)
        console.print("\n🌳 [bold magenta]AST - Abstract Syntax Tree[/bold magenta]")
        console.print(tree)
        print()  # Línea en blanco al final


def print_ast_summary(ast_root):
    """
    Muestra un resumen del AST parseado con información estadística.
    
    Args:
        ast_root: El nodo raíz del AST a analizar
    """
    if ast_root is None:
        return
    
    if not RICH_AVAILABLE:
        print("=== Resumen del AST ===")
        print(f"Tipo de nodo raíz: {type(ast_root).__name__}")
        return
        
    console = Console()
    
    # Crear tabla de resumen
    table = Table(title="📊 Lizard AST - Análisis Resumido")
    table.add_column("Característica", style="cyan", width=20)
    table.add_column("Valor", style="green", width=30)
    table.add_column("Detalles", style="yellow", width=40)
    
    # Análisis básico
    program_info = {
        "functions": 0,
        "base_functions": 0,
        "breed_functions": 0,
        "hook_functions": 0,
        "normal_functions": 0,
        "total_statements": 0,
        "has_metadata": False,
        "metadata_info": "",
        "total_lines": 0
    }
    
    if hasattr(ast_root, 'metadata') and ast_root.metadata:
        program_info["has_metadata"] = True
        program_info["metadata_info"] = f"{ast_root.metadata.ID} v{ast_root.metadata.VERSION}"
    
    if hasattr(ast_root, 'functions'):
        program_info["functions"] = len(ast_root.functions)
        
        for func in ast_root.functions:
            if hasattr(func, '__class__'):
                if 'BaseFunction' in func.__class__.__name__:
                    program_info["base_functions"] += 1
                elif 'BreedFunction' in func.__class__.__name__:
                    program_info["breed_functions"] += 1
                elif 'HookFunction' in func.__class__.__name__:
                    program_info["hook_functions"] += 1
                else:
                    program_info["normal_functions"] += 1
                
                # Contar líneas y statements
                if hasattr(func, 'lineno') and func.lineno:
                    program_info["total_lines"] = max(program_info["total_lines"], func.lineno)
                
                if hasattr(func, 'body') and hasattr(func.body, 'statements'):
                    program_info["total_statements"] += len(func.body.statements)
    
    # Agregar filas a la tabla
    table.add_row("Tipo de AST", type(ast_root).__name__, "Nodo raíz del programa")
    table.add_row("Metadatos", "✅ Sí" if program_info["has_metadata"] else "❌ No", program_info["metadata_info"])
    
    func_details = f"Base: {program_info['base_functions']}, Breed: {program_info['breed_functions']}, Hook: {program_info['hook_functions']}, Normal: {program_info['normal_functions']}"
    table.add_row("Total Funciones", str(program_info["functions"]), func_details)
    table.add_row("Total Statements", str(program_info["total_statements"]), "Sentencias en todos los bloques")
    table.add_row("Líneas procesadas", str(program_info["total_lines"]), "Última línea con código")
    
    console.print(table)
    print()


def generate_png(ast_root, filename="ast"):
    """
    Genera un archivo PNG del AST usando Graphviz con nodos tipados y colores específicos.
    
    Args:
        ast_root: El nodo raíz del AST
        filename: Nombre del archivo PNG a generar (sin extensión)
    """
    if not GRAPHVIZ_AVAILABLE:
        if RICH_AVAILABLE:
            from rich import print
            print("❌ [red]Error: La librería 'graphviz' no está instalada.[/red]")
            print("   Instálala con: pip install graphviz")
        else:
            print("❌ Error: La librería 'graphviz' no está instalada.")
            print("   Instálala con: pip install graphviz")
        return
    
    try:
        # Crear un nuevo grafo dirigido
        dot = Digraph(comment='Lizard AST')
        dot.attr(rankdir='TB')  # Top to Bottom
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
        dot.attr('graph', label='🦎 Lizard AST Visualization', labelloc='t', fontsize='16')
        
        if ast_root is None:
            if RICH_AVAILABLE:
                from rich import print
                print("❌ [red]Error: AST root is None[/red]")
            else:
                print("❌ Error: AST root is None")
            return
        
        node_counter = [0]  # Lista para mantener referencia mutable
        
        def add_node(node, parent_id=None, edge_label=""):
            current_id = f"node{node_counter[0]}"
            node_counter[0] += 1
            
            # Manejar nodos AST del modelo
            if ASTFormatter._is_node(node):
                node_type = type(node).__name__
                
                # Información adicional del nodo
                info = ""
                displayed_fields = set()  # Campos ya mostrados en la info del nodo
                
                if hasattr(node, 'lineno') and node.lineno:
                    info += f"\\nline: {node.lineno}"
                    displayed_fields.add('lineno')
                
                # Agregar información específica del nodo (evitar redundancia con campos)
                if hasattr(node, 'name') and node.name:
                    info += f"\\nname: {node.name}"
                    displayed_fields.add('name')
                elif hasattr(node, 'operator') and node.operator:
                    info += f"\\nop: {node.operator}"
                    displayed_fields.add('operator')
                elif hasattr(node, 'value') and node.value is not None:
                    value_str = str(node.value)
                    if len(value_str) > 15:
                        value_str = value_str[:12] + "..."
                    info += f"\\nvalue: {value_str}"
                    displayed_fields.add('value')
                
                # Mostrar tipos de manera integrada para evitar nodos separados redundantes
                if hasattr(node, 'type') and node.type is not None:
                    # Para literales, mostrar el tipo integrado
                    type_str = str(node.type).split('.')[-1] if hasattr(node.type, 'name') else str(node.type)
                    info += f"\\ntype: {type_str}"
                    displayed_fields.add('type')
                elif hasattr(node, 'param_type') and node.param_type is not None:
                    # Para parámetros, mostrar el tipo integrado
                    info += f"\\ntype: {node.param_type.name}"
                    displayed_fields.add('param_type')
                elif hasattr(node, 'var_type') and node.var_type is not None:
                    # Para declaraciones de variables, mostrar el tipo integrado
                    info += f"\\ntype: {node.var_type.name}"
                    displayed_fields.add('var_type')
                elif hasattr(node, 'return_type') and node.return_type is not None:
                    # Para funciones, mostrar el tipo de retorno integrado
                    info += f"\\nreturn: {node.return_type.name}"
                    displayed_fields.add('return_type')
                
                # Mostrar flags booleanos importantes directamente en la info del nodo
                if hasattr(node, 'is_const'):
                    # Solo mostrar is_const cuando es True (más claro visualmente)
                    if node.is_const:
                        info += f"\\nconst: true"
                    displayed_fields.add('is_const')  # Siempre ocultar el nodo separado
                
                if hasattr(node, 'is_prefix') and node.is_prefix is not None:
                    info += f"\\nprefix: {node.is_prefix}"
                    displayed_fields.add('is_prefix')
                
                # Elegir color según el tipo de nodo con paleta ampliada
                color = 'lightgreen'  # Color por defecto
                
                # Funciones con diferentes tonos
                if 'Function' in node_type:
                    if 'Base' in node_type:
                        color = 'tomato'           # Funciones base
                    elif 'Breed' in node_type:
                        color = 'lightcoral'      # Funciones breed
                    elif 'Hook' in node_type:
                        color = 'indianred'       # Funciones hook
                    else:
                        color = 'salmon'           # Funciones normales
                        
                # Expresiones y operaciones
                elif 'Expression' in node_type or 'Operation' in node_type or 'Oper' in node_type:
                    if 'Binary' in node_type or 'Unary' in node_type or 'BinOper' in node_type or 'UnaryOper' in node_type:
                        color = 'wheat'            # Operaciones aritméticas
                    elif 'Call' in node_type:
                        color = 'burlywood'        # Llamadas a funciones
                    elif 'Array' in node_type:
                        color = 'moccasin'         # Operaciones con arrays
                    else:
                        color = 'lightyellow'      # Otras expresiones
                        
                # Literales con colores específicos por tipo
                elif 'Literal' in node_type or node_type in ['Integer', 'Float', 'String', 'Char', 'Boolean']:
                    if node_type in ['Integer', 'Float']:
                        color = 'lightsteelblue'  # Números
                    elif node_type in ['String', 'Char']:
                        color = 'thistle'         # Texto
                    elif node_type == 'Boolean':
                        color = 'lightgreen'      # Booleanos
                    else:
                        color = 'lavender'        # Otros literales
                        
                # Variables y ubicaciones
                elif 'Variable' in node_type or 'Location' in node_type:
                    color = 'palegreen'           # Variables
                    
                # Declaraciones y sentencias
                elif 'Statement' in node_type or 'Decl' in node_type:
                    if 'If' in node_type or 'While' in node_type or 'For' in node_type:
                        color = 'lightcyan'       # Control de flujo
                    elif 'Decl' in node_type:
                        color = 'powderblue'      # Declaraciones
                    else:
                        color = 'aliceblue'       # Otras sentencias
                        
                # Tipos y estructuras principales
                elif node_type in ['Program', 'Metadata']:
                    color = 'lightpink'          # Nodos principales
                elif node_type == 'Type':
                    color = 'plum'               # Tipos
                elif node_type in ['Block', 'Parameter']:
                    color = 'mistyrose'          # Estructuras
                
                dot.node(current_id, f"{node_type}{info}", fillcolor=color)
                
                # Conectar con el padre si existe
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
                
                # Procesar los campos del nodo
                for field_name, field_value in node.__dict__.items():
                    # Saltar campos ya mostrados en la información del nodo
                    if field_name in displayed_fields:
                        continue
                    
                    if field_value is not None:
                        if isinstance(field_value, list) and field_value:
                            # Lista de elementos con colores específicos
                            list_id = f"list{node_counter[0]}"
                            node_counter[0] += 1
                            
                            # Color específico según el tipo de lista
                            list_color = 'lightsteelblue'  # Color por defecto
                            if field_name in ['functions', 'statements']:
                                list_color = 'lightblue'       # Listas de código
                            elif field_name in ['params', 'arguments']:
                                list_color = 'lightsalmon'     # Listas de parámetros
                            elif field_name in ['elements', 'values']:
                                list_color = 'lightgoldenrodyellow'  # Listas de valores
                            
                            dot.node(list_id, f"{field_name}\\n({len(field_value)} elementos)", 
                                   fillcolor=list_color, shape='ellipse')
                            dot.edge(current_id, list_id)
                            
                            for i, item in enumerate(field_value):
                                add_node(item, list_id, f"[{i}]")
                        else:
                            # Campo individual
                            add_node(field_value, current_id, field_name)
                    
            elif isinstance(node, tuple) and len(node) > 0:
                # Fallback para tuplas (compatibilidad)
                node_type = str(node[0])
                dot.node(current_id, node_type, fillcolor='lightgreen')
                
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
                
                for i, child in enumerate(node[1:], 1):
                    add_node(child, current_id, f"arg{i}")
                    
            elif isinstance(node, list):
                # Lista de nodos con color específico
                dot.node(current_id, f"List\\n[{len(node)} items]", 
                        fillcolor='lightgoldenrodyellow', shape='ellipse')
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
                
                for i, item in enumerate(node):
                    add_node(item, current_id, f"[{i}]")
                    
            else:
                # Valor terminal con color según tipo
                value = str(node)
                if len(value) > 20:  # Truncar valores muy largos
                    value = value[:17] + "..."
                
                # Color específico según el tipo de valor
                terminal_color = 'lightyellow'  # Color por defecto
                if isinstance(node, (int, float)):
                    terminal_color = 'lightsteelblue'    # Números
                elif isinstance(node, str):
                    if len(node) == 1:
                        terminal_color = 'thistle'        # Caracteres
                    else:
                        terminal_color = 'lavender'       # Strings
                elif isinstance(node, bool):
                    terminal_color = 'lightgreen'        # Booleanos
                elif node in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=']:
                    terminal_color = 'wheat'             # Operadores
                
                dot.node(current_id, f'"{value}"', fillcolor=terminal_color, shape='ellipse')
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
            
            return current_id
        
        # Generar el grafo
        root_id = add_node(ast_root)
        
        # Guardar como PNG
        dot.render(filename, format='png', cleanup=True)
        
        png_file = f"{filename}.png"
        if RICH_AVAILABLE:
            from rich import print
            print(f"✅ [green]PNG generado exitosamente: {png_file}[/green]")
        else:
            print(f"✅ PNG generado exitosamente: {png_file}")
        
        # Abrir el archivo PNG automáticamente
        try:
            # Obtener la ruta absoluta del archivo PNG
            abs_png_path = os.path.abspath(png_file)
            
            # Verificar que el archivo existe antes de intentar abrirlo
            if not os.path.exists(abs_png_path):
                if RICH_AVAILABLE:
                    print(f"⚠️ [yellow]Advertencia: El archivo PNG no se encontró en: {abs_png_path}[/yellow]")
                else:
                    print(f"⚠️ Advertencia: El archivo PNG no se encontró en: {abs_png_path}")
                return
            
            if platform.system() == "Windows":
                os.startfile(abs_png_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", abs_png_path])
            else:  # Linux y otros Unix
                subprocess.run(["xdg-open", abs_png_path])
            
            if RICH_AVAILABLE:
                print(f"📖 [cyan]Abriendo {abs_png_path} con el visor predeterminado...[/cyan]")
            else:
                print(f"📖 Abriendo {abs_png_path} con el visor predeterminado...")
            
        except Exception as open_error:
            if RICH_AVAILABLE:
                print(f"⚠️ [yellow]Advertencia: No se pudo abrir automáticamente el archivo PNG: {open_error}[/yellow]")
                print(f"   [dim]Puedes abrirlo manualmente: {os.path.abspath(png_file) if os.path.exists(png_file) else png_file}[/dim]")
            else:
                print(f"⚠️ Advertencia: No se pudo abrir automáticamente el archivo PNG: {open_error}")
                print(f"   Puedes abrirlo manualmente: {os.path.abspath(png_file) if os.path.exists(png_file) else png_file}")
        
    except Exception as e:
        if RICH_AVAILABLE:
            from rich import print
            print(f"❌ [red]Error generando PNG: {e}[/red]")
        else:
            print(f"❌ Error generando PNG: {e}")