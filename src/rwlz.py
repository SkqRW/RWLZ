from Lexer.lexer import LizardLexer

"""
uso: bminor.py [-h] [-v] [--scan | --dot | --sym] [filename]

Compilador para programas B-Minor

opciones:
    -h, --help            Muestra este mensaje de ayuda y sale
    -v, --version         Muestra la información de versión y sale

Opciones de formato:
    --scan                Ejecuta el lexer y muestra los tokens
    --dot                 Genera un archivo DOT para el AST
    --sym                 Muestra la tabla de símbolos
    [filename]            El archivo fuente a compilar

"""

#argparse

import argparse
import ast
import sys

from rich import print
from Lexer.lexer import LizardLexer
from Parser.parser import LizardParser
from rich.table import Table
from rich.tree import Tree
from rich.console import Console
from graphviz import Digraph

# Muestra un mensaje de ayuda cuando no se proporciona ningun argumento extra
def usage(exit_code=1):
    print("[blue]Usage: bminor.py --option filename[/blue]", file=sys.stderr)
    sys.exit(exit_code)

# Función para analizar los argumentos de la línea de comandos
def parse_args():
    cli = argparse.ArgumentParser(
        prog="rwlz.py",
        description="Compilador para B-Minor"
    )
    cli.add_argument("-v", "--version", action="version", version="0.1")

    fgroup = cli.add_argument_group("Formateado opciones")
    cli.add_argument("filename", 
                     type=str,
                     nargs="?",
                     help="The source file to compile")

    mutex = fgroup.add_mutually_exclusive_group()
    mutex.add_argument("--scan", action="store_true", default=False, help="Run the lexer and show tokens")
    mutex.add_argument("--dot", action="store_true", default=False, help="Generate DOT file for AST")
    mutex.add_argument("--sym", action="store_true", default=False, help="Show symbol table")
    mutex.add_argument("--png", action="store_true", default=False, help="Generate PNG image of AST using Graphviz")

    return cli.parse_args()

def print_tokens(tokens):
    table = Table(title="🦎 Lizard Lexer - Token Analysis")
    table.add_column("Token Type", style="cyan", width=12)
    table.add_column("Value", style="magenta", width=14)
    table.add_column("Line", style="green", justify="right", width=4)
    table.add_column("Start", style="yellow", justify="right", width=5)
    table.add_column("End", style="red", justify="right", width=5)

    for token in tokens:
        # Calcular el índice de fin basado en el índice de inicio y la longitud del valor
        token_start = getattr(token, "index", "")
        token_end = ""
        if hasattr(token, "index") and token.value is not None:
            token_end = token.index + len(str(token.value))
        
        table.add_row(
            str(token.type),
            str(token.value),
            str(getattr(token, "lineno", "")),
            str(token_start),
            str(token_end)
        )
    print(table)
    print(f"\n✅ [green]Total tokens processed: {len(tokens)}[/green]")

def print_ast(ast_root):
    """Imprime el AST de manera visual usando Rich Tree con nodos tipados"""
    if ast_root is None:
        print("❌ [red]Error: No se pudo generar el AST[/red]")
        return
    
    # Usar el método pretty_print del nodo si está disponible
    if hasattr(ast_root, 'pretty_print'):
        ast_root.pretty_print()
    else:
        # Fallback para compatibilidad con tuplas (código legacy)
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
    """Muestra un resumen del AST parseado"""
    if ast_root is None:
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
    table.add_row("Total Funciones", str(program_info["functions"]), f"Base: {program_info['base_functions']}, Breed: {program_info['breed_functions']}, Normal: {program_info['normal_functions']}")
    table.add_row("Total Statements", str(program_info["total_statements"]), "Sentencias en todos los bloques")
    table.add_row("Líneas procesadas", str(program_info["total_lines"]), "Última línea con código")
    
    console.print(table)
    print()

def generate_png(ast_root, filename="ast"):
    """Genera un archivo PNG del AST usando Graphviz con nodos tipados"""
    try:
        from Utils.model import Node  # Importar la clase base Node
        
        # Crear un nuevo grafo dirigido
        dot = Digraph(comment='Lizard AST')
        dot.attr(rankdir='TB')  # Top to Bottom
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')
        dot.attr('graph', label='🦎 Lizard AST Visualization', labelloc='t', fontsize='16')
        
        if ast_root is None:
            print("❌ [red]Error: AST root is None[/red]")
            return
        
        node_counter = [0]  # Lista para mantener referencia mutable
        
        def add_node(node, parent_id=None, edge_label=""):
            current_id = f"node{node_counter[0]}"
            node_counter[0] += 1
            
            # Manejar nodos AST del modelo
            if isinstance(node, Node):
                node_type = type(node).__name__
                
                # Información adicional del nodo
                info = ""
                if hasattr(node, 'lineno') and node.lineno:
                    info += f"\\nline: {node.lineno}"
                
                # Agregar información específica del nodo (evitar redundancia con campos)
                if hasattr(node, 'name'):
                    # Solo mostrar name si no es un Parameter (que ya muestra name en los campos)
                    info += f"\\nname: {node.name}"
                elif hasattr(node, 'operator') and node.operator:
                    info += f"\\nop: {node.operator}"
                elif hasattr(node, 'value') and node.value is not None:
                    value_str = str(node.value)
                    if len(value_str) > 15:
                        value_str = value_str[:12] + "..."
                    info += f"\\nvalue: {value_str}"
                
                # Elegir color según el tipo de nodo
                color = 'lightgreen'
                if 'Function' in node_type:
                    color = 'lightcoral'
                elif 'Expression' in node_type or 'Literal' in node_type or 'Variable' in node_type or 'Operation' in node_type:
                    color = 'lightyellow'
                elif 'Statement' in node_type:
                    color = 'lightcyan'
                elif node_type in ['Program', 'Metadata']:
                    color = 'lightpink'
                
                dot.node(current_id, f"{node_type}{info}", fillcolor=color)
                
                # Conectar con el padre si existe
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
                
                # Procesar los campos del nodo
                for field_name, field_value in node.__dict__.items():
                    if field_name == 'lineno':
                        continue  # Ya mostrado en el info
                    
                    if field_value is not None:
                        if isinstance(field_value, list) and field_value:
                            # Lista de elementos
                            list_id = f"list{node_counter[0]}"
                            node_counter[0] += 1
                            dot.node(list_id, f"{field_name}\\n({len(field_value)} elementos)", 
                                   fillcolor='lightsteelblue', shape='ellipse')
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
                # Lista de nodos
                dot.node(current_id, f"List\\n[{len(node)} items]", 
                        fillcolor='lightsteelblue', shape='ellipse')
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
                
                for i, item in enumerate(node):
                    add_node(item, current_id, f"[{i}]")
                    
            else:
                # Valor terminal
                value = str(node)
                if len(value) > 20:  # Truncar valores muy largos
                    value = value[:17] + "..."
                dot.node(current_id, f'"{value}"', fillcolor='lightyellow', shape='ellipse')
                if parent_id:
                    dot.edge(parent_id, current_id, label=edge_label)
            
            return current_id
        
        # Generar el grafo
        root_id = add_node(ast_root)
        
        # Guardar como PNG
        dot.render(filename, format='png', cleanup=True)
        print(f"✅ [green]PNG generado exitosamente: {filename}.png[/green]")
        
    except ImportError as e:
        if 'graphviz' in str(e):
            print("❌ [red]Error: La librería 'graphviz' no está instalada.[/red]")
            print("   Instálala con: pip install graphviz")
        else:
            print(f"❌ [red]Error de importación: {e}[/red]")
    except Exception as e:
        print(f"❌ [red]Error generando PNG: {e}[/red]")

# Función principal
def main():
    if(len(sys.argv) == 1):
        usage()

    if(len(sys.argv) > 3):
        usage()
        return  

    def check_invalid_args():
        valid_options = {"--scan", "--dot", "--sym", "--png", "-h", "--help", "-v", "--version"}
        args = sys.argv[1:]
        for arg in args:
            if arg.startswith("-") and arg not in valid_options:
                return

    check_invalid_args()

    args = parse_args()
    

    if args.filename:
        fname = args.filename
        # Validar extensión .rwlz
        if not fname.endswith('.rwlz'):
            usage()
            return

        with open(fname, encoding="utf-8") as file:
            source = file.read()
        
        lexer = LizardLexer()
        tokens = list(lexer.tokenize(source))
        
        if args.scan:
            print_tokens(tokens)

        parser = LizardParser()
        
        try:
            ast = parser.parse(lexer.tokenize(source))
            
            if ast is None:
                print("❌ [red]Error: No se pudo parsear el archivo. Verifica la sintaxis.[/red]")
                return
            
            print(f"✅ [green]Parsing exitoso! AST generado: {type(ast).__name__}[/green]")
            
            if args.dot:
                print_ast(ast)
            
            if args.png:
                # Generar nombre del archivo basado en el archivo fuente
                base_name = fname.replace('.rwlz', '')
                generate_png(ast, f"{base_name}_ast")
            
            # Mostrar información resumida del AST
            print_ast_summary(ast)
                
        except Exception as e:
            print(f"❌ [red]Error durante el parsing: {e}[/red]")
            import traceback
            traceback.print_exc()



if __name__ == '__main__':
    main()

# python rwlz.py --scan ..\Test\Lizard.rwlz