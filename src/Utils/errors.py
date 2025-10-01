# errors.py
from rich.console import Console

console = Console()
_errors_detected = 0  # Contador global de errores

def error(message, lineno=None):
    """
    Imprime un mensaje de error formateado.
    - message: texto del error
    - lineno: número de línea
    """
    global _errors_detected
    if lineno:
        console.print(f"[red]Error en línea {lineno}: {message}[/red]")
    else:
        console.print(f"[red]Error: {message}[/red]")
    _errors_detected += 1

def get_error_count():
    """ Devuelve la cantidad de errores detectados. """
    return _errors_detected

def reset_errors():
    """ Reinicia el contador de errores. """
    global _errors_detected
    _errors_detected = 0


# TO DO: Colocar advertencias
