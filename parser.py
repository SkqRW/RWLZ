from sly import Parser
from lexer import LizardLexer
from model import *
from model import _L

class LizardParser(Parser):
    # Importar tokens del lexer
    tokens = LizardLexer.tokens

    # Precedencias para expresiones (para evitar ambigüedad)
    precedence = (
        ('left', OR),
        ('left', AND),
        ('right', NOT),
        ('nonassoc', LT, LE, GT, GE, EQ, NEQ),
        ('left', PLUS, MINUS),
        ('left', TIMES, DIVIDE),
    )

    # Reglas de la gramática
    @_('metadata_decl function_list')
    def program(self, p):
        return _L(Program(metadata=p.metadata_decl, functions=p.function_list), p.lineno)

    @_('function_list')
    def program(self, p):
        return _L(Program(metadata=None, functions=p.function_list), p.lineno)

    @_('function_list function_def')
    def function_list(self, p):
        return p.function_list + [p.function_def]

    @_('function_def')
    def function_list(self, p):
        return [p.function_def]

    # Metadata
    @_('"[" BEPINPLUGIN "(" STRING "," STRING "," STRING ")" "]"')
    def metadata_decl(self, p):
        return _L(Metadata(
            plugin_name=p.STRING0.strip('"'),
            version=p.STRING1.strip('"'),
            guid=p.STRING2.strip('"')
        ), p.lineno)

    # Funciones
    @_('BASE ID "(" param_list_opt ")" block')
    def function_def(self, p):
        return _L(BaseFunction(
            name=p.ID,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)

    @_('BREED ID "(" param_list_opt ")" block')  
    def function_def(self, p):
        return _L(BreedFunction(
            name=p.ID,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)

    @_('ID "(" param_list_opt ")" block')
    def function_def(self, p):
        return _L(NormalFunction(
            name=p.ID,
            params=p.param_list_opt,
            body=p.block
        ), p.lineno)

    @_('param_list')
    def param_list_opt(self, p):
        return p.param_list

    @_('')
    def param_list_opt(self, p):
        return []

    @_('param_list "," param')
    def param_list(self, p):
        return p.param_list + [p.param]

    @_('param')
    def param_list(self, p):
        return [p.param]

    @_('type ID')
    def param(self, p):
        return _L(Parameter(name=p.ID, param_type=p.type), p.lineno)

    @_('INT')
    @_('FLOAT')
    @_('BOOL')
    @_('STRING_TYPE')
    @_('ID')
    def type(self, p):
        return _L(Type(name=p[0]), p.lineno)

    # Bloques
    @_('"{" statement_list "}"')
    def block(self, p):
        return _L(Block(statements=p.statement_list), p.lineno)

    @_('statement_list statement')
    def statement_list(self, p):
        return p.statement_list + [p.statement]

    @_('statement')
    def statement_list(self, p):
        return [p.statement]

    # Sentencias
    @_('type ID ASSIGN expr ";"')
    def statement(self, p):
        return _L(VarDecl(var_type=p.type, name=p.ID, value=p.expr), p.lineno)

    @_('ID ASSIGN expr ";"')
    def statement(self, p):
        return _L(Assignment(name=p.ID, value=p.expr), p.lineno)

    @_('function_call ";"')
    def statement(self, p):
        return _L(FunctionCallStmt(call=p.function_call), p.lineno)

    @_('IF "(" expr ")" block ELSE block')
    def statement(self, p):
        return _L(IfStatement(condition=p.expr, then_block=p.block0, else_block=p.block1), p.lineno)

    @_('IF "(" expr ")" block')
    def statement(self, p):
        return _L(IfStatement(condition=p.expr, then_block=p.block), p.lineno)

    @_('RETURN expr ";"')
    def statement(self, p):
        return _L(ReturnStatement(value=p.expr), p.lineno)

    # Llamadas a funciones
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

    # Expresiones
    @_('expr PLUS expr')
    @_('expr MINUS expr')
    @_('expr TIMES expr')
    @_('expr DIVIDE expr')
    @_('expr EQ expr')
    @_('expr NEQ expr')
    @_('expr LT expr')
    @_('expr LE expr')
    @_('expr GT expr')
    @_('expr GE expr')
    @_('expr AND expr')
    @_('expr OR expr')
    def expr(self, p):
        return _L(BinaryOperation(operator=p[1], left=p.expr0, right=p.expr1), p.lineno)

    @_('NOT expr')
    def expr(self, p):
        return _L(UnaryOperation(operator=p.NOT, operand=p.expr), p.lineno)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('function_call')
    def expr(self, p):
        return p.function_call

    @_('NUMBER')
    def expr(self, p):
        return _L(NumberLiteral(value=p.NUMBER), p.lineno)

    @_('STRING')
    def expr(self, p):
        return _L(StringLiteral(value=p.STRING.strip('"')), p.lineno)

    @_('ID')
    def expr(self, p):
        return _L(Variable(name=p.ID), p.lineno)

    @_('PROP "(" ID ")"')
    def expr(self, p):
        return _L(PropExpression(variable=p.ID), p.lineno)
