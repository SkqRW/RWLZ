from sly import Lexer
from Utils.errors import error, get_error_count

class LizardLexer(Lexer):
    tokens = {
        BASE, BREED, PROP, HOOK,
        PRINT,
        ID, ARRAY, AUTO,
        INTEGER_LITERAL, FLOAT_LITERAL, STRING_LITERAL, CHAR_LITERAL,
        INT, FLOAT, BOOL, CHAR, STRING, VOID,
        IF, ELSE, RETURN, TRUE, FALSE,
        FOR, WHILE, BREAK, CONTINUE,
        EQ, NEQ, LE, GE, LT, GT, ASSIGN, 
        PLUS, MINUS, TIMES, DIVIDE, MODULO,
        INCREMENT, DECREMENT,
        PLUS_ASSIGN, MINUS_ASSIGN, TIMES_ASSIGN, DIVIDE_ASSIGN,
        AND, OR, NOT,
        CONST,
        BEPINPLUGIN
    }

    ignore = ' \t\r'

    ignore_comment = r'//.*'
    ignore_longcomment = r'/\*[\s\S]*?\*/'

    @_(r'\n+')
    def ignore_newlines(self, t):
        """ Ignores newlines and updates line number count. """
        self.lineno += t.value.count('\n')

    # Tokens literales (símbolos que usamos tal cual)
    literals = '+-*/%^=()[]{}:;,' 

    # Definimos las expresiones regulares usando el diccionario
    # Palabras clave especiales (orden importante: más específicas primero)
    BEPINPLUGIN = r'BepInPlugin'
    BASE = r'<base>'
    BREED = r'<breed>'
    PROP = r'<prop>'
    PRINT = r'print'

    # Operadores de comparación (orden importante: más largos primero)
    EQ = r'=='
    NEQ = r'!='
    LE = r'<='
    GE = r'>='
    LT = r'<'
    GT = r'>'
    
    # Operadores de asignación compuesta (orden importante: más largos primero)
    PLUS_ASSIGN = r'\+='
    MINUS_ASSIGN = r'-='
    TIMES_ASSIGN = r'\*='
    DIVIDE_ASSIGN = r'/='
    
    # Operadores de incremento/decremento
    INCREMENT = r'\+\+'
    DECREMENT = r'--'
    
    # Operadores aritméticos y asignación
    ASSIGN = r'='
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    MODULO = r'%'
    
    # Operadores lógicos
    AND = r'&&'
    OR = r'\|\|'
    NOT = r'!'

    # NOTE: STRING token removed - using STRING_LITERAL instead for escape sequence support
    # STRING = r'\".*?\"'
    
    # Definimos todos los tokens en un diccionario para fácil referencia
    keywords = {
        # Palabras clave especiales (todas en minúsculas)
        'bepinplugin': 'BEPINPLUGIN',
        '<base>': 'BASE',
        '<breed>': 'BREED', 
        '<prop>': 'PROP',
        '<hook>': 'HOOK',
        'print': 'PRINT',
        'auto': 'AUTO',
        'array': 'ARRAY',
        
        # Palabras clave de control
        'if': 'IF',
        'else': 'ELSE', 
        'return': 'RETURN',
        'for': 'FOR',
        'while': 'WHILE',
        'break': 'BREAK',
        'continue': 'CONTINUE',
        'true': 'TRUE',
        'false': 'FALSE',

        
        # Tipos de datos
        'int': 'INT',
        'float': 'FLOAT',
        'bool': 'BOOL',
        'char': 'CHAR',
        'string': 'STRING',
        'void': 'VOID',
        'const': 'CONST',
        
        # Operadores de comparación
        '==': 'EQ',
        '!=': 'NEQ',
        '<=': 'LE',
        '>=': 'GE',
        '<': 'LT',
        '>': 'GT',
        
        # Operadores de asignación compuesta
        '+=': 'PLUS_ASSIGN',
        '-=': 'MINUS_ASSIGN',
        '*=': 'TIMES_ASSIGN',
        '/=': 'DIVIDE_ASSIGN',
        
        # Operadores de incremento/decremento
        '++': 'INCREMENT',
        '--': 'DECREMENT',
        
        # Operadores aritméticos y asignación
        '=': 'ASSIGN',
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'TIMES',
        '/': 'DIVIDE',
        '%': 'MODULO',
        
        # Operadores lógicos
        '&&': 'AND',
        '||': 'OR',
        '!': 'NOT'
    }

    # Expresiones regulares para literales
    FLOAT_LITERAL = r'([0-9]+\.[0-9]+([eE][+-]?[0-9]+)?)|([0-9]+[eE][+-]?[0-9]+)'  # Números flotantes
    INTEGER_LITERAL = r'0|[1-9][0-9]*'  # Números enteros
    CHAR_LITERAL = r"\'([\x20-\x7E]|\\([abefnrtv\\'\"]|0x[0-9a-fA-F]{2}))\'"  # Caracteres
    STRING_LITERAL = r'"([^"\n\\]|\\([abefnrtv\\\'""]|0x[0-9a-fA-F]{2}))*"'  # Cadenas de texto (excluye comillas sin escape)

    @_(r'([0-9]+\.[0-9]+([eE][+-]?[0-9]+)?)|([0-9]+[eE][+-]?[0-9]+)')
    def FLOAT(self, t):
        t.type = 'FLOAT'
        return float(t.value)
    
    @_(r'0|[1-9][0-9]*')
    def NUMBER(self, t):
        t.type = 'NUMBER'
        return int(t.value)
    
    # tomado de b-minor
    @_(r'(0\.[0-9]+)|([1-9][0-9]*\.[0-9]+)([eE][+-]?[0-9]+)?')
    def INVALID_FLOAT(self, t):
        error(f"Número de punto flotante inválido: {t.value} en la línea {t.lineno}", t.lineno)
        # No retorna el token para que no sea procesado como válido

    @_(r'\"[^\"]*\n?')
    def INVALID_STRING(self, t):
        error(f"Cadena de texto no válida (sin cierre de comillas): {t.value}", t.lineno)
        # No retorna el token para que no sea procesado como válido

    @_(r"'[^']*\n?")
    def INVALID_CHAR(self, t):
        error(f"Literal de carácter no válido (sin cierre de comillas): {t.value}", t.lineno)
        # No retorna el token para que no sea procesado como válido
    
    @_(r'[A-Za-z_][A-Za-z0-9_]*')
    def ID(self, t):
        """
        Identifica si una palabra es reservada del lenguaje o un identificador normal.
        Si la palabra está en la lista de palabras reservadas, asigna el tipo correspondiente.
        Si no, la clasifica como identificador (ID).
        """
        if t.value in self.keywords:
            t.type = self.keywords[t.value]
        else:
            t.type = 'ID'
        return t



    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno = t.value.count('\n')
    
    @_(r'//.*')
    def ignore_cppcomment(self, t):
        pass
    
    @_(r'/\*(.|\n)*\*/')
    def ignore_comment(self, t):
        self.lineno = t.value.count('\n')
    