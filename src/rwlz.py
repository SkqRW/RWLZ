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
import os
import subprocess
import platform

from rich import print
from Lexer.lexer import LizardLexer
from Parser.parser import LizardParser
from rich.table import Table
from rich.tree import Tree
from rich.console import Console
from Utils.ast_printer import print_ast, print_ast_summary, generate_png

# Function to show usage information
def usage(exit_code=1):
    print("[blue]Usage: bminor.py --option filename[/blue]", file=sys.stderr)
    sys.exit(exit_code)

# Function to parse command line arguments
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
        # Calculate start and end positions if available
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

def check_invalid_args():
    valid_options = {"--scan", "--dot", "--sym", "--png", "-h", "--help", "-v", "--version"}
    args = sys.argv[1:]
    for arg in args:
        if arg.startswith("-") and arg not in valid_options:
            return arg  # Retorna el argumento inválido
    return None

def main():
    if(len(sys.argv) == 1):
        usage()

    #if(len(sys.argv) > 3):
    #    usage()
    #    return  
    

    invalid_arg = check_invalid_args()
    if invalid_arg:
        print(f"❌ [red]Error: Argumento inválido '{invalid_arg}'. Use -h para ver las opciones disponibles.[/red]")
        sys.exit(1)

    args = parse_args()
    

    if args.filename:
        fname = args.filename
        # Validation of .rwlz extension
        if not fname.endswith('.rwlz'):
            usage()
            return

        with open(fname, encoding="utf-8") as file:
            source = file.read()
        
        try:
            lexer = LizardLexer()
            tokens = list(lexer.tokenize(source))
            
            if args.scan:
                print_tokens(tokens)
        except Exception as e:
            print(f"❌ [red]Error durante el análisis léxico: {e}[/red]")
            import traceback
            traceback.print_exc()
            return

        
        try:
            parser = LizardParser()
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
            
                
        except Exception as e:
            print(f"❌ [red]Error durante el parsing: {e}[/red]")
            import traceback
            traceback.print_exc()
            return
        
        # Mostrar información resumida del AST
        print_ast_summary(ast)



if __name__ == '__main__':
    main()

# python rwlz.py --scan ..\Test\Lizard.rwlz