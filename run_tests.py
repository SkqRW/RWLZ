#!/usr/bin/env python3
"""
Sistema de pruebas automatizado para el compilador Lizard
Ejecuta todos los archivos de prueba (.rwlz) y muestra los resultados usando Rich
"""

import os
import sys
import re
import traceback
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from io import StringIO
import contextlib

# Importar Rich para formateo de salida
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich import box

# Importar componentes del compilador
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from Lexer.lexer import LizardLexer
from Parser.parser import LizardParser
from Utils.errors import reset_errors, get_error_count

console = Console()

class TestResult:
    """Representa el resultado de una prueba individual"""
    def __init__(self, filename: str, expected_type: str, expected_description: str = ""):
        self.filename = filename
        self.expected_type = expected_type  # "VALID" o "ERROR"
        self.expected_description = expected_description
        self.actual_result = None  # "SUCCESS", "ERROR", "EXCEPTION"
        self.error_message = ""
        self.error_type = ""  # "LEXER", "PARSER", "EXCEPTION"
        self.ast_generated = False
        self.exception_details = ""

    @property
    def passed(self) -> bool:
        """Determina si la prueba pasó según el resultado esperado"""
        if self.expected_type == "VALID":
            return self.actual_result == "SUCCESS"
        elif self.expected_type == "ERROR":
            return self.actual_result in ["ERROR", "EXCEPTION"]
        return False

    @property
    def status_emoji(self) -> str:
        """Devuelve un emoji representando el estado de la prueba"""
        if self.passed:
            return "✅"
        else:
            return "❌"

    @property
    def status_color(self) -> str:
        """Devuelve el color para mostrar el resultado"""
        if self.passed:
            return "green"
        else:
            return "red"

class TestRunner:
    """Ejecutor de pruebas principal"""
    
    def __init__(self, test_dir: str = "Test"):
        self.test_dir = Path(test_dir)
        self.valid_tests_dir = self.test_dir / "valid_tests"
        self.invalid_tests_dir = self.test_dir / "invalid_tests"
        self.results: List[TestResult] = []
        
    def extract_test_info(self, file_path: Path) -> Tuple[str, str]:
        """Extrae información del TEST o ERROR de los comentarios del archivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar comentarios TEST: o ERROR:
            test_match = re.search(r'//\s*TEST:\s*(.+)', content, re.IGNORECASE)
            error_match = re.search(r'//\s*ERROR:\s*(.+)', content, re.IGNORECASE)
            
            if test_match:
                return "VALID", test_match.group(1).strip()
            elif error_match:
                return "ERROR", error_match.group(1).strip()
            else:
                # Inferir del nombre del directorio
                if "valid" in str(file_path):
                    return "VALID", "Prueba válida sin descripción específica"
                else:
                    return "ERROR", "Prueba inválida sin descripción específica"
                    
        except Exception as e:
            console.print(f"[yellow]Advertencia: No se pudo leer {file_path}: {e}[/yellow]")
            return "UNKNOWN", str(e)

    def capture_compiler_output(self):
        """Captura la salida del compilador (stdout y stderr)"""
        return StringIO(), StringIO()
    
    def run_single_test(self, file_path: Path) -> TestResult:
        """Ejecuta una prueba individual"""
        expected_type, description = self.extract_test_info(file_path)
        result = TestResult(file_path.name, expected_type, description)
        
        # Capturar salida de errores
        captured_output = StringIO()
        captured_errors = StringIO()
        
        try:
            # Leer el archivo fuente
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Reiniciar contador de errores
            reset_errors()
            
            # Capturar salida de errores para obtener mensajes específicos
            with contextlib.redirect_stdout(captured_output), contextlib.redirect_stderr(captured_errors):
                # Fase 1: Análisis léxico
                lexer = LizardLexer()
                try:
                    tokens = list(lexer.tokenize(source))
                except Exception as lex_error:
                    result.actual_result = "ERROR"
                    result.error_type = "LEXER"
                    result.error_message = f"Error léxico: {str(lex_error)}"
                    return result
                
                # Verificar errores del lexer
                lexer_errors = captured_errors.getvalue()
                if get_error_count() > 0 or lexer_errors:
                    result.actual_result = "ERROR"
                    result.error_type = "LEXER"
                    if lexer_errors:
                        # Extraer mensaje específico del error léxico
                        error_lines = lexer_errors.strip().split('\n')
                        specific_error = error_lines[-1] if error_lines else "Error léxico no especificado"
                        result.error_message = f"Error léxico: {specific_error}"
                    else:
                        result.error_message = f"Error léxico detectado ({get_error_count()} errores)"
                    return result
                
                # Fase 2: Análisis sintáctico
                parser = LizardParser()
                reset_errors()  # Reiniciar para el parser
                captured_errors.truncate(0)  # Limpiar buffer de errores
                captured_errors.seek(0)
                
                try:
                    ast = parser.parse(lexer.tokenize(source))
                except Exception as parse_error:
                    result.actual_result = "ERROR"
                    result.error_type = "PARSER"
                    result.error_message = f"Error sintáctico: {str(parse_error)}"
                    return result
                
                # Verificar resultado del parsing
                parser_errors = captured_errors.getvalue()
                if ast is None or get_error_count() > 0 or parser_errors:
                    result.actual_result = "ERROR"
                    result.error_type = "PARSER"
                    if parser_errors:
                        # Extraer mensaje específico del error sintáctico
                        error_lines = parser_errors.strip().split('\n')
                        # Buscar líneas que contengan información de error útil
                        specific_errors = []
                        for line in error_lines:
                            if 'syntax error' in line.lower() or 'parse error' in line.lower():
                                specific_errors.append(line.strip())
                        
                        if specific_errors:
                            result.error_message = f"Error sintáctico: {specific_errors[-1]}"
                        else:
                            result.error_message = "Error sintáctico: estructura inválida"
                    else:
                        result.error_message = f"Error sintáctico detectado ({get_error_count()} errores)"
                else:
                    result.actual_result = "SUCCESS"
                    result.ast_generated = True
                    result.error_message = "Compilación exitosa"
                
        except Exception as e:
            result.actual_result = "EXCEPTION"
            result.error_type = "EXCEPTION"
            result.error_message = f"Excepción: {str(e)}"
            result.exception_details = traceback.format_exc()
            
        return result

    def collect_test_files(self) -> List[Path]:
        """Recolecta todos los archivos de prueba .rwlz"""
        test_files = []
        
        # Archivos válidos
        if self.valid_tests_dir.exists():
            test_files.extend(self.valid_tests_dir.glob("*.rwlz"))
            
        # Archivos inválidos
        if self.invalid_tests_dir.exists():
            test_files.extend(self.invalid_tests_dir.glob("*.rwlz"))
            
        return sorted(test_files)

    def run_all_tests(self) -> None:
        """Ejecuta todas las pruebas con barra de progreso"""
        test_files = self.collect_test_files()
        
        if not test_files:
            console.print("[red]❌ No se encontraron archivos de prueba (.rwlz)[/red]")
            return
            
        console.print(f"[cyan]🔍 Encontrados {len(test_files)} archivos de prueba[/cyan]")
        console.print()
        
        # Ejecutar pruebas con barra de progreso
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[green]Ejecutando pruebas...", total=len(test_files))
            
            for test_file in test_files:
                progress.update(task, description=f"[green]Probando {test_file.name}...")
                result = self.run_single_test(test_file)
                self.results.append(result)
                progress.advance(task)

    def generate_summary_table(self) -> Table:
        """Genera tabla de resumen de resultados"""
        table = Table(title="📊 Resumen de Pruebas", box=box.ROUNDED)
        table.add_column("Métrica", style="cyan", width=20)
        table.add_column("Valor", style="white", width=15)
        table.add_column("Detalle", style="dim", width=40)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        valid_tests = [r for r in self.results if r.expected_type == "VALID"]
        invalid_tests = [r for r in self.results if r.expected_type == "ERROR"]
        
        valid_passed = sum(1 for r in valid_tests if r.passed)
        invalid_passed = sum(1 for r in invalid_tests if r.passed)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        table.add_row("Total de Pruebas", str(total_tests), f"Archivos .rwlz procesados")
        table.add_row("✅ Pasaron", f"[green]{passed_tests}[/green]", f"Comportamiento esperado")
        table.add_row("❌ Fallaron", f"[red]{failed_tests}[/red]", f"Comportamiento inesperado")
        table.add_row("📊 Tasa de Éxito", f"[{'green' if success_rate >= 80 else 'yellow' if success_rate >= 60 else 'red'}]{success_rate:.1f}%[/]", "Porcentaje de pruebas exitosas")
        table.add_row("", "", "")
        table.add_row("🟢 Pruebas Válidas", f"{len(valid_tests)}", f"✅ {valid_passed} / ❌ {len(valid_tests) - valid_passed}")
        table.add_row("🔴 Pruebas Inválidas", f"{len(invalid_tests)}", f"✅ {invalid_passed} / ❌ {len(invalid_tests) - invalid_passed}")
        
        return table

    def generate_detailed_table(self, test_type: str) -> Table:
        """Genera tabla detallada para un tipo específico de pruebas"""
        if test_type == "VALID":
            filtered_results = [r for r in self.results if r.expected_type == "VALID"]
            title = "🟢 Pruebas Válidas - Resultados Detallados"
            expected_col = "Funcionalidad Esperada"
        else:
            filtered_results = [r for r in self.results if r.expected_type == "ERROR"]
            title = "🔴 Pruebas Inválidas - Resultados Detallados"
            expected_col = "Error Esperado"
            
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("Estado", justify="center", width=6)
        table.add_column("Archivo", style="cyan", width=18)
        table.add_column(expected_col, style="dim", width=45)
        table.add_column("Resultado", width=30)
        
        for result in sorted(filtered_results, key=lambda x: (not x.passed, x.filename)):
            status = result.status_emoji
            filename = result.filename
            expected = result.expected_description[:32] + "..." if len(result.expected_description) > 35 else result.expected_description
            
            # Formatear resultado actual con tipo de error
            if result.actual_result == "SUCCESS":
                actual = f"[green]✓ Compilado exitosamente[/green]"
            elif result.actual_result == "ERROR":
                if result.error_type == "LEXER":
                    actual = f"[yellow]⚠ Error Léxico[/yellow]"
                elif result.error_type == "PARSER":
                    actual = f"[orange3]⚠ Error Sintáctico[/orange3]"
                else:
                    actual = f"[yellow]⚠ Error Detectado[/yellow]"
            elif result.actual_result == "EXCEPTION":
                actual = f"[red]💥 Excepción del Sistema[/red]"
            else:
                actual = f"[dim]? Estado Desconocido[/dim]"
            
            # Color de fila según el resultado
            if result.passed:
                table.add_row(status, filename, expected, actual)
            else:
                table.add_row(status, f"[red]{filename}[/red]", expected, actual)
        
        return table

    def generate_error_details_table(self) -> Optional[Table]:
        """Genera tabla con detalles de errores para pruebas fallidas"""
        failed_tests = [r for r in self.results if not r.passed]
        
        if not failed_tests:
            return None
            
        table = Table(title="🔍 Detalles de Pruebas Fallidas", box=box.ROUNDED)
        table.add_column("Archivo", style="red", width=18)
        table.add_column("Esperado", style="cyan", width=12)
        table.add_column("Obtenido", style="yellow", width=15)
        table.add_column("Tipo Error", style="magenta", width=12)
        table.add_column("Descripción del Error", style="dim", width=45)
        
        for result in failed_tests:
            expected = "✓ Éxito" if result.expected_type == "VALID" else "❌ Error"
            
            if result.actual_result == "SUCCESS":
                obtained = "✓ Éxito"
            elif result.actual_result == "ERROR":
                obtained = "❌ Error"
            elif result.actual_result == "EXCEPTION":
                obtained = "💥 Excepción"
            else:
                obtained = "? Desconocido"
            
            error_type = result.error_type if result.error_type else "N/A"
            error_msg = result.error_message[:42] + "..." if len(result.error_message) > 45 else result.error_message
            
            table.add_row(result.filename, expected, obtained, error_type, error_msg)
        
        return table

    def print_results(self) -> None:
        """Imprime todos los resultados formateados"""
        console.clear()
        
        # Título principal
        title_text = Text("🦎 LIZARD COMPILER - SISTEMA DE PRUEBAS", style="bold magenta")
        console.print(Panel(title_text, box=box.DOUBLE, padding=(1, 2)))
        console.print()
        
        # Resumen general
        console.print(self.generate_summary_table())
        console.print()
        
        # Tablas detalladas
        console.print(self.generate_detailed_table("VALID"))
        console.print()
        
        console.print(self.generate_detailed_table("ERROR"))
        console.print()
        
        # Detalles de errores si existen
        error_table = self.generate_error_details_table()
        if error_table:
            console.print(error_table)
            console.print()
        
        # Mensaje final
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate == 100:
            final_msg = Text("🎉 ¡TODAS LAS PRUEBAS PASARON! 🎉", style="bold green")
        elif success_rate >= 80:
            final_msg = Text(f"✨ {success_rate:.1f}% de pruebas exitosas - ¡Buen trabajo!", style="bold yellow")
        else:
            final_msg = Text(f"⚠️ {success_rate:.1f}% de pruebas exitosas - Necesita atención", style="bold red")
            
        console.print(Panel(final_msg, box=box.ROUNDED, padding=(1, 2)))

def main():
    """Función principal"""
    # Cambiar al directorio del script si no estamos allí
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("Test"):
        console.print("[red]❌ Error: No se encontró el directorio 'Test'[/red]")
        console.print("[dim]Asegúrate de que el directorio Test existe en la raíz del proyecto[/dim]")
        sys.exit(1)
    
    # Crear y ejecutar runner de pruebas
    runner = TestRunner()
    
    try:
        console.print("[bold cyan]🦎 Sistema de Pruebas del Compilador Lizard[/bold cyan]")
        console.print()
        
        runner.run_all_tests()
        runner.print_results()
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Pruebas interrumpidas por el usuario[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error inesperado: {e}[/red]")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
