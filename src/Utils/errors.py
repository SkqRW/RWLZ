# errors.py
from rich.console import Console

console = Console()
_errors_detected = 0  # Contador global de errores

def error(message, lineno=0):
    """ 
    Print a formatted error message.
    - message: error text
    - lineno: line number, 0 by default (no line)
    """
    global _errors_detected
    if lineno:
        console.print(f"[red]Error en línea {lineno}: {message}[/red]")
    else:
        console.print(f"[red]Error: {message}[/red]")
    _errors_detected += 1

def get_error_count():
    """ Returns the number of errors detected. """
    return _errors_detected

def reset_errors():
    """ Resets the error counter. """
    global _errors_detected
    _errors_detected = 0


def syntax_error(token=None, lineno=0):
    """
    Handles syntax errors during parsing.
    - token: token that caused the error
    - lineno: line number of the error
    """
    if token:
        error(f"Syntax error in token '{token}' (line {lineno})", lineno)
    else:
        error("Syntax error: unexpected end of file", lineno or 0)

def warning(message, lineno=0):
    """
    Print a formatted warning message.
    - message: warning text
    - lineno: line number, 0 by default (no line)
    """
    if lineno:
        console.print(f"[yellow]Warning on line {lineno}: {message}[/yellow]")
    else:
        console.print(f"[yellow]Warning: {message}[/yellow]")

# TO DO: Add more specific error types, like info stuff
