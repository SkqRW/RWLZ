@echo off
setlocal enabledelayedexpansion
echo LIZARD TEST RUNNER - WINDOWS BATCH
echo ===================================

cd /d "%~dp0"

:: Verificar que existe el compilador
if not exist "src\rwlz.py" (
    echo Error: No se encuentra src\rwlz.py
    pause
    exit /b 1
)

:: Verificar que existen las carpetas de tests
if not exist "Test\valid_tests" (
    echo Error: No se encuentra Test\valid_tests
    pause
    exit /b 1
)

if not exist "Test\invalid_tests" (
    echo Error: No se encuentra Test\invalid_tests
    pause
    exit /b 1
)

set passed=0
set failed=0

echo.
echo EJECUTANDO TESTS VALIDOS (deben pasar)...
echo ==========================================

for %%f in (Test\valid_tests\good_*.rwlz) do (
    echo Ejecutando: %%~nxf
    python src\rwlz.py --scan "%%f" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   PASS - %%~nxf
        set /a passed+=1
    ) else (
        echo   FAIL - %%~nxf (se esperaba exito)
        set /a failed+=1
    )
)

echo.
echo EJECUTANDO TESTS INVALIDOS (deben fallar)...
echo =============================================

for %%f in (Test\invalid_tests\bad_*.rwlz) do (
    echo Ejecutando: %%~nxf
    python src\rwlz.py --scan "%%f" >nul 2>&1
    if !errorlevel! neq 0 (
        echo   PASS - %%~nxf (fallo como se esperaba)
        set /a passed+=1
    ) else (
        echo   FAIL - %%~nxf (se esperaba fallo)
        set /a failed+=1
    )
)

echo.
echo ============================================
echo RESUMEN DE RESULTADOS
echo ============================================
set /a total=passed+failed
echo Tests ejecutados: !total!
echo Tests exitosos:   !passed!
echo Tests fallidos:   !failed!

if !failed! equ 0 (
    echo.
    echo TODOS LOS TESTS PASARON!
) else (
    echo.
    echo !failed! TEST(S) FALLARON
)

echo.
pause