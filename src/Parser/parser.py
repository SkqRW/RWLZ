from sly import Parser
from Lexer.lexer import LizardLexer
from Utils.model import *
from Utils.model import _L
from Utils.errors import error, syntax_error

class LizardParser(Parser):
    # =====================================================================
    # CONFIGURACIÓN DEL PARSER
    # =====================================================================
    
    # Importar tokens del lexer
    tokens = LizardLexer.tokens
    #debugfile = 'LizardParser.out'

    # Precedencias para expresiones (para evitar ambigüedad)
    # Orden: menor precedencia (arriba) a mayor precedencia (abajo)
    precedence = (
        ('right', PLUS_ASSIGN, MINUS_ASSIGN, TIMES_ASSIGN, DIVIDE_ASSIGN),  # Assignments
        ('left', OR),                                                        # Logical OR
        ('left', AND),                                                       # Logical AND
        ('right', NOT),                                                      # Logical NOT
        ('nonassoc', LT, LE, GT, GE, EQ, NEQ),                             # Comparisons
        ('left', PLUS, MINUS),                                              # Addition/Subtraction
        ('left', TIMES, DIVIDE, MODULO),                                    # Multiplication/Division
        ('right', 'UMINUS', 'UPLUS'),                                       # Unary operators
        ('left', INCREMENT, DECREMENT),                                     # Increment/Decrement
    )    
    
    # =====================================================================
    # PROGRAMA PRINCIPAL Y METADATA
    # =====================================================================
    
    @_('metadata_decl decl_list')
    def program(self, p):
        # Optional metadata in case the project is compiled with its identifier json
        # El identificador es de BepInEx para mods
        return _L(Program(metadata=p.metadata_decl, functions=p.decl_list), p.lineno)

    @_('decl_list')
    def program(self, p):
        return _L(Program(metadata=None, functions=p.decl_list), p.lineno)

    @_('decl decl_list')
    def decl_list(self, p):
        return [p.decl] + p.decl_list

    @_('decl')
    def decl_list(self, p):
        return [p.decl]


    # BEPINPLUGIN Metadata
    # BepInPlugin: [BepInPlugin("name", "version", "guid")]
    @_('"[" BEPINPLUGIN "(" STRING "," STRING "," STRING ")" "]"')
    def metadata_decl(self, p):
        return _L(Metadata(
            ID=p.STRING0.strip('"'),
            VERSION=p.STRING1.strip('"'),
            NAME=p.STRING2.strip('"')
        ), p.lineno)

    # =====================================================================
    # Function Declarations 
    # =====================================================================
    
    # NO IN USE STILL
    @_('BASE type ID "(" param_list_opt ")" block')
    def decl(self, p):
        return _L(BaseFunction(
            name=p.ID,
            return_type=p.type,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)

    # NO IN USE STILL
    @_('BREED type ID "(" param_list_opt ")" block')  
    def decl(self, p):
        return _L(BreedFunction(
            name=p.ID,
            return_type=p.type,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)
    
    # NO IN USE STILL
    @_('HOOK type ID "(" param_list_opt ")" block')  
    def decl(self, p):
        return _L(HookFunction(
            name=p.ID,
            return_type=p.type,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)

    @_('type ID "(" param_list_opt ")" block')
    def decl(self, p):
        return _L(NormalFunction(
            name=p.ID,
            return_type=p.type,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)

    # =====================================================================
    # Function Parameters
    # =====================================================================
    
    @_('param_list')
    def param_list_opt(self, p):
        return p.param_list

    @_('')
    def param_list_opt(self, p):
        return []

    @_('param "," param_list')
    def param_list(self, p):
        return [p.param] + p.param_list

    @_('param')
    def param_list(self, p):
        return [p.param]

    @_('type ID')
    def param(self, p):
        return _L(Parameter(name=p.ID, param_type=p.type), p.lineno)

    @_('CONST type ID')
    def param(self, p):
        return _L(Parameter(name=p.ID, param_type=p.type), p.lineno)

    # =====================================================================
    # DATA TYPES
    # =====================================================================
    
    @_('INT')
    @_('FLOAT')
    @_('BOOL')
    @_('CHAR')
    @_('STRING')
    @_('VOID')
    @_('AUTO')
    def type(self, p):
        return _L(Type(name=p[0]), p.lineno)

    @_('ARRAY type')
    def type(self, p):
        return _L(Type(name=f"array {p.type.name}"), p.lineno)

    # =====================================================================
    # BLOQUES Y LISTAS DE SENTENCIAS
    # =====================================================================
    
    @_('"{" statement_list "}"')
    def block(self, p):
        """Bloque de código: { statements }"""
        return _L(Block(statements=p.statement_list), p.lineno)

    @_('statement_list statement')
    def statement_list(self, p):
        """Lista de múltiples statements"""
        return p.statement_list + [p.statement]

    @_('statement')
    def statement_list(self, p):
        """Lista de un solo statement"""
        return [p.statement]

    # =====================================================================
    # Var and Array Declarations, Assignments, and Function Calls
    # =====================================================================
    
    @_('type ID ASSIGN expr ";"')
    def statement(self, p):
        return _L(VarDecl(var_type=p.type, name=p.ID, value=p.expr), p.lineno)

    @_('type ID ";"')
    def statement(self, p):
        return _L(VarDecl(var_type=p.type, name=p.ID), p.lineno)

    @_('CONST type ID ASSIGN expr ";"')
    def statement(self, p):
        return _L(VarDecl(var_type=p.type, name=p.ID, value=p.expr, is_const=True), p.lineno)

    @_('type ID "[" expr "]" ";"')
    def statement(self, p):
        return _L(ArrayDecl(var_type=p.type, name=p.ID, size=p.expr), p.lineno)

    @_('type ID "[" "]" ASSIGN "[" expr_list "]" ";"')
    def statement(self, p):
        return _L(ArrayDecl(var_type=p.type, name=p.ID, values=p.expr_list), p.lineno)

    @_('type ID "[" expr "]" ASSIGN "[" expr_list "]" ";"')
    def statement(self, p):
        return _L(ArrayDecl(var_type=p.type, name=p.ID, size=p.expr, values=p.expr_list), p.lineno)

    @_('ID ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="=", value=p.expr), p.lineno)

    @_('ID PLUS_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="+=", value=p.expr), p.lineno)

    @_('ID MINUS_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="-=", value=p.expr), p.lineno)

    @_('ID TIMES_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="*=", value=p.expr), p.lineno)

    @_('ID DIVIDE_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="/=", value=p.expr), p.lineno)

    @_('ID "[" expr "]" ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=ArrayLocation(name=p.ID, index=p.expr0), operator="=", value=p.expr1), p.lineno)

    @_('ID "[" expr "]" PLUS_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=ArrayLocation(name=p.ID, index=p.expr0), operator="+=", value=p.expr1), p.lineno)

    @_('ID "[" expr "]" MINUS_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=ArrayLocation(name=p.ID, index=p.expr0), operator="-=", value=p.expr1), p.lineno)

    @_('ID "[" expr "]" TIMES_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=ArrayLocation(name=p.ID, index=p.expr0), operator="*=", value=p.expr1), p.lineno)

    @_('ID "[" expr "]" DIVIDE_ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(target=ArrayLocation(name=p.ID, index=p.expr0), operator="/=", value=p.expr1), p.lineno)

    @_('INCREMENT ID ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="++", is_prefix=True), p.lineno)

    @_('ID INCREMENT ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="++", is_prefix=False), p.lineno)

    @_('DECREMENT ID ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="--", is_prefix=True), p.lineno)

    @_('ID DECREMENT ";"')
    def statement(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="--", is_prefix=False), p.lineno)

    @_('function_call ";"')
    def statement(self, p):
        return _L(FunctionCallStmt(call=p.function_call), p.lineno)

    # ===============================================
    # CONTROL FLOW (Control de Flujo)
    # ===============================================
    """
    Esta sección maneja las estructuras de control:
    - Condicionales (if, if-else)
    - Bucles (while, for)
    - Control de bucles (break, continue)
    """

    @_('IF "(" expr ")" block ELSE block')
    def statement(self, p):
        return _L(IfStatement(condition=p.expr, then_block=p.block0, else_block=p.block1), p.lineno)

    @_('IF "(" expr ")" block')
    def statement(self, p):
        return _L(IfStatement(condition=p.expr, then_block=p.block), p.lineno)

    @_('WHILE "(" expr ")" block')
    def statement(self, p):
        return _L(WhileStatement(condition=p.expr, body=p.block), p.lineno)

    @_('FOR "(" for_init ";" for_condition ";" for_update ")" block')
    def statement(self, p):
        return _L(ForStatement(init=p.for_init, condition=p.for_condition, update=p.for_update, body=p.block), p.lineno)

    @_('BREAK ";"')
    def statement(self, p):
        return _L(BreakStatement(), p.lineno)

    @_('CONTINUE ";"')
    def statement(self, p):
        return _L(ContinueStatement(), p.lineno)

    @_('RETURN expr ";"')
    def statement(self, p):
        return _L(ReturnStatement(value=p.expr), p.lineno)

    @_('RETURN ";"')
    def statement(self, p):
        return _L(ReturnStatement(), p.lineno)

    @_('PRINT "(" expr ")" ";"')
    def statement(self, p):
        return _L(PrintStatement(expression=p.expr), p.lineno)

    # ===============================================
    # ASSIGNMENTS (Asignaciones)
    # ===============================================
    """
    Esta sección maneja todas las formas de asignación:
    - Asignación simple (=)
    - Asignaciones compuestas (+=, -=, *=, /=, %=)
    - Asignaciones de arrays
    - Incremento y decremento
    """

    # Reglas para bucle for
    @_('type ID ASSIGN expr')
    def for_init(self, p):
        return _L(VarDecl(var_type=p.type, name=p.ID, value=p.expr), p.lineno)

    @_('ID ASSIGN expr')
    def for_init(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="=", value=p.expr), p.lineno)

    @_('')
    def for_init(self, p):
        return None

    @_('expr')
    def for_condition(self, p):
        return p.expr

    @_('')
    def for_condition(self, p):
        return None

    @_('assignment_expr')
    def for_update(self, p):
        return p.assignment_expr

    @_('increment_expr')
    def for_update(self, p):
        return p.increment_expr

    @_('')
    def for_update(self, p):
        return None

    # Calls to functions
    @_('ID "(" arg_list_opt ")"')
    def function_call(self, p):
        return _L(CallExpression(name=p.ID, arguments=p.arg_list_opt), p.lineno)

    @_('arg_list')
    def arg_list_opt(self, p):
        return p.arg_list

    @_('')
    def arg_list_opt(self, p):
        return []

    @_('arg_list "," expr')
    def arg_list(self, p):
        return p.arg_list + [p.expr]

    @_('expr')
    def arg_list(self, p):
        return [p.expr]

    # List of expressions (for array literals)
    @_('expr_list "," expr')
    def expr_list(self, p):
        return p.expr_list + [p.expr]

    @_('expr')
    def expr_list(self, p):
        return [p.expr]

    # Assignments and increments used in for loops
    @_('ID ASSIGN expr')
    def assignment_expr(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="=", value=p.expr), p.lineno)

    @_('INCREMENT ID')
    def increment_expr(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="++", is_prefix=True), p.lineno)

    @_('ID INCREMENT')
    def increment_expr(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="++", is_prefix=False), p.lineno)

    @_('DECREMENT ID')
    def increment_expr(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="--", is_prefix=True), p.lineno)

    @_('ID DECREMENT')
    def increment_expr(self, p):
        return _L(Assignment(target=VarLocation(name=p.ID), operator="--", is_prefix=False), p.lineno)

    # ===============================================
    # EXPRESSIONS(Expresiones)
    # ===============================================

    @_('expr PLUS expr')
    @_('expr MINUS expr')
    @_('expr TIMES expr')
    @_('expr DIVIDE expr')
    @_('expr MODULO expr')
    @_('expr EQ expr')
    @_('expr NEQ expr')
    @_('expr LT expr')
    @_('expr LE expr')
    @_('expr GT expr')
    @_('expr GE expr')
    @_('expr AND expr')
    @_('expr OR expr')
    def expr(self, p):
        return _L(BinOper(operator=p[1], left=p.expr0, right=p.expr1), p.lineno)

    @_('NOT expr')
    @_('MINUS expr %prec UMINUS')
    @_('PLUS expr %prec UPLUS')
    def expr(self, p):
        return _L(UnaryOper(operator=p[0], operand=p.expr), p.lineno)

    @_('INCREMENT ID')
    def expr(self, p):
        return _L(IncrementExpression(variable=p.ID, operator="++", is_prefix=True), p.lineno)

    @_('ID INCREMENT')
    def expr(self, p):
        return _L(IncrementExpression(variable=p.ID, operator="++", is_prefix=False), p.lineno)

    @_('DECREMENT ID')
    def expr(self, p):
        return _L(IncrementExpression(variable=p.ID, operator="--", is_prefix=True), p.lineno)

    @_('ID DECREMENT')
    def expr(self, p):
        return _L(IncrementExpression(variable=p.ID, operator="--", is_prefix=False), p.lineno)

    @_('ID "[" expr "]"')
    def expr(self, p):
        return _L(ArrayAccess(name=p.ID, index=p.expr), p.lineno)

    @_('"[" expr_list "]"')
    def expr(self, p):
        return _L(ArrayLiteral(elements=p.expr_list), p.lineno)

    @_('"[" "]"')
    def expr(self, p):
        return _L(ArrayLiteral(elements=[]), p.lineno)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    # ===============================================
    # FUNCTION CALLS (Llamadas a Funciones)
    # ===============================================
    """
    Esta sección maneja las llamadas a funciones:
    - Funciones con argumentos
    - Funciones sin argumentos
    - Integración con expresiones
    """

    @_('function_call')
    def expr(self, p):
        return p.function_call

    # ===============================================
    # LITERALS (Literales)
    # ===============================================
    """
    Esta sección maneja todos los valores literales:
    - Números enteros y decimales
    - Cadenas de texto y caracteres
    - Valores booleanos (true/false)
    - Variables e identificadores
    - Arrays literales
    """

    @_('INTEGER_LITERAL')
    def expr(self, p):
        return _L(Integer(value=int(p.INTEGER_LITERAL)), p.lineno)

    @_('FLOAT_LITERAL')
    def expr(self, p):
        return _L(Float(value=float(p.FLOAT_LITERAL)), p.lineno)

    @_('STRING')
    @_('STRING_LITERAL')
    def expr(self, p):
        return _L(String(value=p[0].strip('"')), p.lineno)

    @_('CHAR_LITERAL')
    def expr(self, p):
        return _L(Char(value=p.CHAR_LITERAL.strip("'")), p.lineno)

    @_('TRUE')
    def expr(self, p):
        return _L(Boolean(value=True), p.lineno)

    @_('FALSE')
    def expr(self, p):
        return _L(Boolean(value=False), p.lineno)

    @_('ID')
    def expr(self, p):
        return _L(Variable(name=p.ID), p.lineno)

    # ===============================================
    # SPECIAL EXPRESSIONS (Expresiones Especiales)
    # ===============================================
    """
    Esta sección maneja las expresiones especiales del lenguaje Lizard:
    - prop(): Acceso a propiedades
    - base(): Llamadas a clase base
    - breed(): Operaciones de herencia
    Estas son características únicas del lenguaje para BepInEx plugins
    """

    @_('PROP "(" expr ")"')
    def expr(self, p):
        """Expresión prop() para acceso a propiedades"""
        return _L(PropExpression(variable=p.expr), p.lineno)

    @_('BASE "(" expr ")"')
    def expr(self, p):
        """Expresión base() para llamadas a clase base"""
        return _L(BaseExpression(expression=p.expr), p.lineno)

    @_('BREED "(" expr ")"')
    def expr(self, p):
        """Expresión breed() para operaciones de herencia"""
        return _L(BreedExpression(expression=p.expr), p.lineno)


        
    def __init__(self):
        """Inicialización del parser con contador de errores"""
        super().__init__()
        self.error_count = 0
