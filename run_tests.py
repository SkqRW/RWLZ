#!/usr/bin/env python3
"""
🦎 LIZARD TEST RUNNER
==================

Script para ejecutar todos los tests del compilador Lizard.
Ejecuta tests válidos (que deben compilar exitosamente) y tests inválidos (que deben fallar).

Uso:
    python run_tests.py [--verbose] [--stop-on-error]

Opciones:
    --verbose        Muestra salida detallada de cada test
    --stop-on-error  Detiene la ejecución al primer error
    --help          Muestra esta ayuda
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
import time

# Configuración de paths
SCRIPT_DIR = Path(__file__).parent
TEST_DIR = SCRIPT_DIR / "Test"
VALID_TESTS_DIR = TEST_DIR / "valid_tests"
INVALID_TESTS_DIR = TEST_DIR / "invalid_tests"
SRC_DIR = SCRIPT_DIR / "src"
COMPILER_SCRIPT = SRC_DIR / "rwlz.py"

class TestResult:
    def __init__(self, test_file, expected_success, actual_success, output="", error="", execution_time=0.0):
        self.test_file = test_file
        self.expected_success = expected_success
        self.actual_success = actual_success
        self.output = output
        self.error = error
        self.execution_time = execution_time
        self.passed = expected_success == actual_success

def run_compiler(test_file_path, verbose=False):
    """Ejecuta el compilador en un archivo de test y retorna el resultado"""
    start_time = time.time()
    
    try:
        # Ejecutar el compilador con --scan para verificar que funciona
        result = subprocess.run([
            sys.executable, str(COMPILER_SCRIPT), "--scan", str(test_file_path)
        ], capture_output=True, text=True, timeout=30)
        
        execution_time = time.time() - start_time
        
        # El compilador es exitoso si no hay errores (return code 0)
        success = result.returncode == 0
        
        if verbose:
            print(f"  Return code: {result.returncode}")
            if result.stdout:
                print(f"  Stdout: {result.stdout[:200]}...")
            if result.stderr:
                print(f"  Stderr: {result.stderr[:200]}...")
        
        return TestResult(
            test_file=test_file_path.name,
            expected_success=True,  # Se actualizará según el tipo de test
            actual_success=success,
            output=result.stdout,
            error=result.stderr,
            execution_time=execution_time
        )
        
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return TestResult(
            test_file=test_file_path.name,
            expected_success=True,
            actual_success=False,
            output="",
            error="Test timeout (30s)",
            execution_time=execution_time
        )
    except Exception as e:
        execution_time = time.time() - start_time
        return TestResult(
            test_file=test_file_path.name,
            expected_success=True,
            actual_success=False,
            output="",
            error=f"Exception: {str(e)}",
            execution_time=execution_time
        )

def get_test_description(test_file_path):
    """Extrae la descripción del test desde la primera línea del archivo"""
    try:
        with open(test_file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line.startswith('//'):
                return first_line[2:].strip()
    except:
        pass
    return "Sin descripción"

def run_tests(test_dir, expected_success, test_type_name, verbose=False, stop_on_error=False):
    """Ejecuta todos los tests en un directorio"""
    test_files = sorted([f for f in test_dir.glob("*.rwlz")])
    
    if not test_files:
        print(f"⚠️  No se encontraron archivos .rwlz en {test_dir}")
        return []
    
    results = []
    total_files = len(test_files)
    
    print(f"Ejecutando {test_type_name} ({total_files} archivos)...")
    
    for i, test_file in enumerate(test_files, 1):
        if verbose:
            print(f"\n🧪 [{i}/{total_files}] Ejecutando: {test_file.name}")
            description = get_test_description(test_file)
            print(f"   Descripción: {description}")
        else:
            print(f"[{i}/{total_files}] {test_file.name}...", end=" ")
        
        result = run_compiler(test_file, verbose)
        result.expected_success = expected_success
        results.append(result)
        
        # Mostrar resultado
        if verbose:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"   {status} ({result.execution_time:.2f}s)")
            
            if not result.passed and result.error:
                print(f"   Error: {result.error[:100]}...")
        else:
            status = "PASS" if result.passed else "FAIL"
            print(f"{status} ({result.execution_time:.2f}s)")
        
        # Parar si hay error y se solicita stop-on-error
        if stop_on_error and not result.passed:
            print(f"\n❌ Deteniendo ejecución debido a error en: {test_file.name}")
            break
    
    return results

def print_results_table(valid_results, invalid_results):
    """Imprime una tabla con los resultados de todos los tests"""
    
    valid_passed = sum(1 for r in valid_results if r.passed)
    valid_total_time = sum(r.execution_time for r in valid_results)
    
    invalid_passed = sum(1 for r in invalid_results if r.passed)
    invalid_total_time = sum(r.execution_time for r in invalid_results)
    
    total_tests = len(valid_results) + len(invalid_results)
    total_passed = valid_passed + invalid_passed
    total_time = valid_total_time + invalid_total_time
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS DE TESTS")
    print("="*60)
    
    print(f"Tests Válidos (good_*.rwlz):")
    print(f"  Total: {len(valid_results)} | Exitosos: {valid_passed} | Fallidos: {len(valid_results) - valid_passed} | Tiempo: {valid_total_time:.2f}s")
    
    print(f"\nTests Inválidos (bad_*.rwlz):")  
    print(f"  Total: {len(invalid_results)} | Exitosos: {invalid_passed} | Fallidos: {len(invalid_results) - invalid_passed} | Tiempo: {invalid_total_time:.2f}s")
    
    print(f"\nTOTAL:")
    print(f"  Total: {total_tests} | Exitosos: {total_passed} | Fallidos: {total_tests - total_passed} | Tiempo: {total_time:.2f}s")
    
    # Mostrar tests fallidos
    failed_tests = [r for r in (valid_results + invalid_results) if not r.passed]
    
    if failed_tests:
        print("\n❌ TESTS FALLIDOS:")
        print("-" * 60)
        for result in failed_tests:
            expected = "Éxito" if result.expected_success else "Fallo"
            actual = "Éxito" if result.actual_success else "Fallo" 
            error_msg = result.error[:80] + "..." if len(result.error) > 80 else result.error
            
            print(f"• {result.test_file}")
            print(f"  Esperado: {expected} | Obtenido: {actual}")
            if error_msg:
                print(f"  Error: {error_msg}")
            print()
    else:
        print("\n🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")

def check_prerequisites():
    """Verifica que todos los archivos necesarios existan"""
    missing_files = []
    
    if not COMPILER_SCRIPT.exists():
        missing_files.append(str(COMPILER_SCRIPT))
    
    if not VALID_TESTS_DIR.exists():
        missing_files.append(str(VALID_TESTS_DIR))
        
    if not INVALID_TESTS_DIR.exists():
        missing_files.append(str(INVALID_TESTS_DIR))
    
    if missing_files:
        print("❌ Archivos faltantes:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(
        description="🦎 Lizard Test Runner - Ejecuta todos los tests del compilador"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Muestra salida detallada de cada test"
    )
    parser.add_argument(
        "--stop-on-error", "-s",
        action="store_true",
        help="Detiene la ejecución al primer error"
    )
    
    args = parser.parse_args()
    
    print("🦎 LIZARD COMPILER TEST RUNNER")
    print("=" * 50)
    
    # Verificar prerrequisitos
    if not check_prerequisites():
        sys.exit(1)
    
    # Ejecutar tests válidos (deben compilar sin errores)
    print("\n📁 EJECUTANDO TESTS VÁLIDOS...")
    valid_results = run_tests(
        VALID_TESTS_DIR, 
        expected_success=True, 
        test_type_name="tests válidos",
        verbose=args.verbose,
        stop_on_error=args.stop_on_error
    )
    
    # Ejecutar tests inválidos (deben fallar al compilar)
    print("\n📁 EJECUTANDO TESTS INVÁLIDOS...")
    invalid_results = run_tests(
        INVALID_TESTS_DIR, 
        expected_success=False, 
        test_type_name="tests inválidos",
        verbose=args.verbose,
        stop_on_error=args.stop_on_error
    )
    
    # Mostrar resultados
    print_results_table(valid_results, invalid_results)
    
    # Determinar código de salida
    total_tests = len(valid_results) + len(invalid_results)
    passed_tests = sum(1 for r in (valid_results + invalid_results) if r.passed)
    
    if passed_tests == total_tests:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        sys.exit(0)
    else:
        print(f"\n💥 {total_tests - passed_tests} TEST(S) FALLARON")
        sys.exit(1)

if __name__ == "__main__":
    main()