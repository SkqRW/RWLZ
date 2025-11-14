from Lexer.lexer import LizardLexer

"""
Usage: rwlz.py [-h] [-v] [--scan | --dot | --sym | --check] [filename]

RWLZ Language Compiler

Options:
    -h, --help            Show this help message and exit
    -v, --version         Show version information and exit

Format options:
    --scan                Run the lexer and show tokens
    --dot                 Generate a DOT file for the AST
    --png                 Generate a PNG image of the AST
    --sym                 Show the symbol table
    --check               Perform semantic analysis and type checking
    [filename]            The source file to compile

"""

import argparse
import sys
import os
import subprocess
import platform

from rich import print
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from Lexer.lexer import LizardLexer
from Parser.parser import LizardParser
from Semantic.checker import SemanticChecker
from Utils.ast_printer import print_ast, print_ast_summary, generate_png
from Utils.errors import reset_errors, get_error_count

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
    print("[blue]Usage: rwlz.py --option filename[/blue]", file=sys.stderr)
    sys.exit(exit_code)

# Function to parse command line arguments
def parse_args():
    cli = argparse.ArgumentParser(
        prog="rwlz.py",
        description="RWLZ Language Compiler"
    )
    cli.add_argument("-v", "--version", action="version", version="0.1")

    fgroup = cli.add_argument_group("Format options")
    cli.add_argument("filename", 
                     type=str,
                     nargs="?",
                     help="The source file to compile")

    mutex = fgroup.add_mutually_exclusive_group()
    mutex.add_argument("--scan", action="store_true", default=False, help="Run the lexer and show tokens")
    mutex.add_argument("--dot", action="store_true", default=False, help="Generate DOT file for AST")
    mutex.add_argument("--png", action="store_true", default=False, help="Generate PNG image of AST using Graphviz")
    mutex.add_argument("--sym", action="store_true", default=False, help="Show symbol table")
    mutex.add_argument("--check", action="store_true", default=False, help="Perform semantic analysis")
    mutex.add_argument("--compile", action="store_true", default=False, help="Compile to executable")

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
    valid_options = {"--scan", "--dot", "--sym", "--png", "--check", "--compile", "-h", "--help", "-v", "--version"}
    args = sys.argv[1:]
    for arg in args:
        if arg.startswith("-") and arg not in valid_options:
            return arg  # Return the invalid argument
    return None

def main():
    if(len(sys.argv) == 1):
        usage()

    invalid_arg = check_invalid_args()
    if invalid_arg:
        print(f"❌ [red]Error: Invalid argument '{invalid_arg}'. Use -h to see available options.[/red]")
        sys.exit(1)

    args = parse_args()
    
    if args.filename:
        fname = args.filename
        # Validation of .rwlz extension
        if not fname.endswith('.rwlz'):
            usage()
            return

        # Read source file
        try:
            with open(fname, encoding="utf-8") as file:
                source = file.read()
        except FileNotFoundError:
            print(f"❌ [red]Error: File '{fname}' not found.[/red]")
            return
        except Exception as e:
            print(f"❌ [red]Error reading file: {e}[/red]")
            return
        
        # Reset error counter
        reset_errors()
        
        # Lexical analysis
        try:
            lexer = LizardLexer()
            tokens = list(lexer.tokenize(source))
            
            if args.scan:
                print_tokens(tokens)
                return
                
        except Exception as e:
            print(f"❌ [red]Error during lexical analysis: {e}[/red]")
            import traceback
            traceback.print_exc()
            return
        
        # Check for lexical errors
        if get_error_count() > 0:
            print(f"❌ [red]Lexical analysis failed with {get_error_count()} error(s).[/red]")
            return
        
        # Syntax analysis (parsing)
        try:
            parser = LizardParser()
            ast = parser.parse(lexer.tokenize(source))
            
            if ast is None:
                print("❌ [red]Error: Could not parse the file. Check the syntax.[/red]")
                return
            
            print(f"✅ [green]Parsing successful! AST generated: {type(ast).__name__}[/green]")
            
            # Generate DOT file if requested
            if args.dot:
                print_ast(ast)
                return
            
            # Generate PNG if requested
            if args.png:
                base_name = fname.replace('.rwlz', '')
                generate_png(ast, f"{base_name}_ast")
                return
                
        except Exception as e:
            print(f"❌ [red]Error during parsing: {e}[/red]")
            import traceback
            traceback.print_exc()
            return
        
        # Show AST summary
        print_ast_summary(ast)
        
        # Semantic analysis
        if args.check or args.sym or args.compile:
            print("\n" + "="*60)
            print("🔍 [cyan]Starting Semantic Analysis...[/cyan]")
            print("="*60 + "\n")
            
            try:
                checker = SemanticChecker()
                success = checker.check(ast)
                
                stats = checker.get_statistics()
                
                # Show symbol table if requested
                if args.sym:
                    print("\n" + "="*60)
                    print("📋 [cyan]Symbol Table:[/cyan]")
                    print("="*60 + "\n")
                    checker.print_symbol_table()
                
                # Print results
                print("\n" + "="*60)
                print("📊 [cyan]Semantic Analysis Results:[/cyan]")
                print("="*60)
                
                if success:
                    print(f"✅ [green]Semantic analysis completed successfully![/green]")
                    if stats['warnings'] > 0:
                        print(f"⚠️  [yellow]{stats['warnings']} warning(s) found[/yellow]")
                else:
                    print(f"❌ [red]Semantic analysis failed with {stats['errors']} error(s)[/red]")
                    if stats['warnings'] > 0:
                        print(f"⚠️  [yellow]Also found {stats['warnings']} warning(s)[/yellow]")
                
                print("="*60 + "\n")
                
                # If compilation is requested and semantic analysis passed
                if args.compile and success:
                    print("\n" + "="*60)
                    print("⚙️  [cyan]Starting Code Generation...[/cyan]")
                    print("="*60 + "\n")
                    
                    try:
                        from LLVM.codegen import LLVMCodeGenerator
                        from LLVM.compiler import LLVMCompiler
                        
                        # Generate LLVM IR from AST
                        # Pass the symbol table from semantic checker to code generator
                        codegen = LLVMCodeGenerator(symtab=checker.symtab)
                        ir_code = codegen.generate(ast)
                        
                        # Prepare file names
                        base_name = fname.replace('.rwlz', '')
                        ir_file = f"{base_name}.ll"
                        output_file = base_name
                        
                        print(f"📝 [cyan]Generated LLVM IR:[/cyan]")
                        print("-"*60)
                        print(ir_code)
                        print("-"*60 + "\n")
                        
                        # Compile IR to executable
                        print("🔨 [cyan]Compiling to executable...[/cyan]")
                        compiler = LLVMCompiler()
                        compiler.compile_to_executable(
                            ir_code=ir_code,
                            output_filename=output_file,
                            ir_filename=ir_file,
                            keep_object=False
                        )
                        
                        print(f"✅ [green]Compilation successful![/green]")
                        print(f"📦 Executable: [yellow]{output_file}[/yellow]")
                        print(f"📄 LLVM IR: [yellow]{ir_file}[/yellow]")
                        
                    except Exception as e:
                        print(f"❌ [red]Error during code generation: {e}[/red]")
                        import traceback
                        traceback.print_exc()
                        return
                elif args.compile and not success:
                    print("❌ [red]Cannot compile due to semantic errors.[/red]")
                    return
                
            except Exception as e:
                print(f"❌ [red]Error during semantic analysis: {e}[/red]")
                import traceback
                traceback.print_exc()
                return


if __name__ == '__main__':
    main()

# Example usage:
# python rwlz.py --scan ../Test/Lizard.rwlz
# python rwlz.py --check ../Test/ComplexLizard.rwlz
# python rwlz.py --sym ../Test/ComplexLizard.rwlz