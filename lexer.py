from sly import Lexer

class LizardLexer(Lexer):
    tokens = {
        BASE, BREED, PROP,
        ID, STRING, NUMBER,
        IF, ELSE, RETURN,
        INT, FLOAT, BOOL, STRING_TYPE,
        EQ, NEQ, LE, GE, LT, GT, ASSIGN, PLUS, MINUS, TIMES, DIVIDE,
        AND, OR, NOT,
        BEPINPLUGIN
    }

    # Ignorar espacios y tabs
    ignore = ' \t\r'

    # Comentarios tipo //
    ignore_comment = r'//.*'
    ignore_longcomment = r'/\*[\s\S]*?\*/'

    @_(r'\n+')
    def ignore_newlines(self, t):
        """
        Ignora saltos de línea y actualiza el contador de líneas.
        """
        self.lineno += t.value.count('\n')

    # Tokens literales (símbolos que usamos tal cual)
    literals = { '(', ')', '{', '}', '[', ']', ',', ';', ':' }

    # Definimos las expresiones regulares usando el diccionario
    # Palabras clave especiales (orden importante: más específicas primero)
    BEPINPLUGIN = r'BepInPlugin'
    BASE = r'<base>'
    BREED = r'<breed>'
    PROP = r'<prop>'
    
    # Palabras clave de control y tipos de datos
    IF = r'if'
    ELSE = r'else'
    RETURN = r'return'
    INT = r'int'
    FLOAT = r'float'
    BOOL = r'bool'
    STRING_TYPE = r'string'

    # Operadores de comparación (orden importante: más largos primero)
    EQ = r'=='
    NEQ = r'!='
    LE = r'<='
    GE = r'>='
    LT = r'<'
    GT = r'>'
    
    # Operadores aritméticos y asignación
    ASSIGN = r'='
    PLUS = r'\+'
    MINUS = r'-'
    TIMES = r'\*'
    DIVIDE = r'/'
    
    # Operadores lógicos
    AND = r'&&'
    OR = r'\|\|'
    NOT = r'!'

    # Identificadores (manejados por función @_ más abajo)
    # ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    
    # Definimos todos los tokens en un diccionario para fácil referencia
    keywords = {
        # Palabras clave especiales
        'BepInPlugin': 'BEPINPLUGIN',
        'bepinplugin': 'BEPINPLUGIN',
        '<base>': 'BASE',
        '<breed>': 'BREED', 
        '<prop>': 'PROP',
        
        # Palabras clave de control
        'if': 'IF',
        'else': 'ELSE', 
        'return': 'RETURN',
        
        # Tipos de datos
        'int': 'INT',
        'float': 'FLOAT',
        'bool': 'BOOL',
        'string': 'STRING_TYPE',
        
        # Operadores de comparación
        '==': 'EQ',
        '!=': 'NEQ',
        '<=': 'LE',
        '>=': 'GE',
        '<': 'LT',
        '>': 'GT',
        
        # Operadores aritméticos y asignación
        '=': 'ASSIGN',
        '+': 'PLUS',
        '-': 'MINUS',
        '*': 'TIMES',
        '/': 'DIVIDE',
        
        # Operadores lógicos
        '&&': 'AND',
        '||': 'OR',
        '!': 'NOT'
    }
    
    # Números enteros o floats - patrón único que maneja ambos
    @_(r'\d+(\.\d+)?')
    def NUMBER(self, t):
        if '.' in t.value:
            t.value = float(t.value)
        else:
            t.value = int(t.value)
        return t

    @_(r'[A-Za-z_][A-Za-z0-9_]*')
    def ID(self, t):
        """
        Identifica si una palabra es reservada del lenguaje o un identificador normal.
        Si la palabra está en la lista de palabras reservadas, asigna el tipo correspondiente.
        Si no, la clasifica como identificador (ID).
        """
        # Primero verificamos con el valor original (case-sensitive para tokens especiales)
        if t.value in self.keywords:
            t.type = self.keywords[t.value]
        # Luego verificamos en minúsculas para palabras clave normales
        elif t.value.lower() in self.keywords:
            t.type = self.keywords[t.value.lower()]
        else:
            t.type = 'ID'
        return t

    # Strings entre comillas
    STRING = r'\".*?\"'
