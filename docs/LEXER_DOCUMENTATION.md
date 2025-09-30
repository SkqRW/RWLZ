# Documentación del Lexer - Compilador Lizard (.rwlz)

## Descripción General

El **LizardLexer** es el analizador léxico del compilador para el lenguaje de programación **Lizard** con extensión `.rwlz`. Este lexer está diseñado específicamente para desarrollar para .NET, con características especiales para BepInEx plugins y sintaxis inspirada en C/C#.

## Características Principales

- ✅ **Operaciones básicas completas** (aritméticas, lógicas, comparación)
- ✅ **Manejo de arrays estilo C** (con operadores +=, -=, *=, /=, ++, --)
- ✅ **Tipos de datos nativos** (int, float, bool, char, string)
- ✅ **Estructuras de control** (if/else, for, while, break, continue)
- ✅ **Funciones y variables automáticas**
- ✅ **Sintaxis especial para mods .NET** (BepInPlugin, \<base>, \<breed>, \<prop>)
- ✅ **Manejo robusto de errores**

---

## Tokens del Lenguaje

### 1. Palabras Clave Especiales (Mod Development)

| Token | Símbolo | Descripción |
|-------|---------|-------------|
| `BEPINPLUGIN` | `BepInPlugin` | Atributo para plugins BepInEx |
| `BASE` | `<base>` | Referencia a clase base |
| `BREED` | `<breed>` | Referencia a breed/tipo |
| `PROP` | `<prop>` | Referencia a propiedad |
| `PRINT` | `print` | Función de impresión |

### 2. Tipos de Datos

| Token | Palabra Clave | Descripción |
|-------|---------------|-------------|
| `INT` | `int` | Entero de 32 bits |
| `FLOAT` | `float` | Punto flotante |
| `BOOL` | `bool` | Booleano (true/false) |
| `CHAR` | `char` | Carácter individual |
| `STRING_TYPE` | `string` | Cadena de caracteres |
| `VOID` | `void` | Tipo vacío |
| `CONST` | `const` | Modificador de constante |
| `AUTO` | `auto` | Tipo automático |
| `ARRAY` | `array` | Tipo array |

### 3. Estructuras de Control

| Token | Palabra Clave | Descripción |
|-------|---------------|-------------|
| `IF` | `if` | Condicional |
| `ELSE` | `else` | Alternativa condicional |
| `FOR` | `for` | Bucle for |
| `WHILE` | `while` | Bucle while |
| `BREAK` | `break` | Romper bucle |
| `CONTINUE` | `continue` | Continuar bucle |
| `RETURN` | `return` | Retorno de función |
| `FUNCTION` | `function` | Declaración de función |

### 4. Literales Booleanos

| Token | Valor | Descripción |
|-------|-------|-------------|
| `TRUE` | `true` | Verdadero |
| `FALSE` | `false` | Falso |

---

## Operadores

### 1. Operadores Aritméticos

| Token | Símbolo | Descripción | Ejemplo |
|-------|---------|-------------|---------|
| `PLUS` | `+` | Suma | `a + b` |
| `MINUS` | `-` | Resta | `a - b` |
| `TIMES` | `*` | Multiplicación | `a * b` |
| `DIVIDE` | `/` | División | `a / b` |
| `MODULO` | `%` | Módulo | `a % b` |

### 2. Operadores de Asignación

| Token | Símbolo | Descripción | Ejemplo |
|-------|---------|-------------|---------|
| `ASSIGN` | `=` | Asignación simple | `a = 5` |
| `PLUS_ASSIGN` | `+=` | Suma y asigna | `a += 3` |
| `MINUS_ASSIGN` | `-=` | Resta y asigna | `a -= 2` |
| `TIMES_ASSIGN` | `*=` | Multiplica y asigna | `a *= 4` |
| `DIVIDE_ASSIGN` | `/=` | Divide y asigna | `a /= 2` |

### 3. Operadores de Incremento/Decremento

| Token | Símbolo | Descripción | Ejemplo |
|-------|---------|-------------|---------|
| `INCREMENT` | `++` | Incremento | `++i` o `i++` |
| `DECREMENT` | `--` | Decremento | `--i` o `i--` |

### 4. Operadores de Comparación

| Token | Símbolo | Descripción | Ejemplo |
|-------|---------|-------------|---------|
| `EQ` | `==` | Igual | `a == b` |
| `NEQ` | `!=` | No igual | `a != b` |
| `LT` | `<` | Menor que | `a < b` |
| `GT` | `>` | Mayor que | `a > b` |
| `LE` | `<=` | Menor o igual | `a <= b` |
| `GE` | `>=` | Mayor o igual | `a >= b` |

### 5. Operadores Lógicos

| Token | Símbolo | Descripción | Ejemplo |
|-------|---------|-------------|---------|
| `AND` | `&&` | AND lógico | `a && b` |
| `OR` | `\|\|` | OR lógico | `a \|\| b` |
| `NOT` | `!` | NOT lógico | `!a` |

---

## Literales

### 1. Números Enteros
- **Patrón**: `0|[1-9][0-9]*`
- **Ejemplos**: `0`, `42`, `1000`
- **Token**: `INTEGER_LITERAL`

### 2. Números Flotantes
- **Patrón**: `([1-9][0-9]*\.[0-9]+)([eE][+-]?[0-9]+)?`
- **Ejemplos**: `3.14`, `2.5e10`, `1.0E-5`
- **Token**: `FLOAT_LITERAL`

### 3. Caracteres
- **Patrón**: `'([\x20-\x7E]|\\([abefnrtv\\'\"]|0x[0-9a-fA-F]{2}))'`
- **Ejemplos**: `'a'`, `'\n'`, `'\x41'`
- **Token**: `CHAR_LITERAL`

### 4. Cadenas de Texto
- **Patrón**: `\"([\x20-\x7E]|\\([abefnrtv\\'\"]|0x[0-9a-fA-F]{2}))*\"`
- **Ejemplos**: `"Hello World"`, `"Line 1\nLine 2"`
- **Token**: `STRING_LITERAL`

---

## Símbolos Literales

Los siguientes caracteres se reconocen directamente como tokens:
```
+ - * / % ^ = ( ) [ ] { } : ; ,
```

---

## Gramática Libre de Contexto (BNF)

La siguiente es la gramática formal del lenguaje Lizard en formato Backus-Naur Form (BNF):

### Programa Principal
```bnf
<programa> ::= <plugin_declaration> <function_list>
             | <function_list>

<plugin_declaration> ::= '[' 'BepInPlugin' '(' <string_literal> ',' <string_literal> ',' <string_literal> ')' ']'

<function_list> ::= <function_declaration> <function_list>
                  | <function_declaration>
```

### Declaraciones de Funciones
```bnf
<function_declaration> ::= 'function' <type> <identifier> '(' <parameter_list> ')' <block>
                         | <type> <identifier> '(' <parameter_list> ')' <block>

<parameter_list> ::= <parameter> ',' <parameter_list>
                   | <parameter>
                   | ε

<parameter> ::= <type> <identifier>
              | 'const' <type> <identifier>
```

### Tipos de Datos
```bnf
<type> ::= 'int'
         | 'float' 
         | 'bool'
         | 'char'
         | 'string'
         | 'void'
         | 'auto'
         | 'array' <type>

<type_modifier> ::= 'const'
```

### Bloques y Declaraciones
```bnf
<block> ::= '{' <statement_list> '}'

<statement_list> ::= <statement> <statement_list>
                   | ε

<statement> ::= <declaration_statement>
              | <assignment_statement>
              | <expression_statement>
              | <control_statement>
              | <return_statement>
              | <print_statement>
              | <block>
```

### Declaraciones y Asignaciones
```bnf
<declaration_statement> ::= <type> <identifier> ';'
                          | <type> <identifier> '=' <expression> ';'
                          | 'const' <type> <identifier> '=' <expression> ';'
                          | <type> <identifier> '[' <expression> ']' ';'
                          | <type> <identifier> '=' <array_literal> ';'

<assignment_statement> ::= <identifier> '=' <expression> ';'
                         | <identifier> '+=' <expression> ';'
                         | <identifier> '-=' <expression> ';'
                         | <identifier> '*=' <expression> ';'
                         | <identifier> '/=' <expression> ';'
                         | <identifier> '[' <expression> ']' '=' <expression> ';'
                         | <identifier> '++' ';'
                         | '++' <identifier> ';'
                         | <identifier> '--' ';'
                         | '--' <identifier> ';'

<expression_statement> ::= <expression> ';'
```

### Estructuras de Control
```bnf
<control_statement> ::= <if_statement>
                      | <while_statement>
                      | <for_statement>
                      | <break_statement>
                      | <continue_statement>

<if_statement> ::= 'if' '(' <expression> ')' <statement>
                 | 'if' '(' <expression> ')' <statement> 'else' <statement>

<while_statement> ::= 'while' '(' <expression> ')' <statement>

<for_statement> ::= 'for' '(' <for_init> ';' <expression> ';' <for_update> ')' <statement>

<for_init> ::= <declaration_statement>
             | <assignment_statement>
             | ε

<for_update> ::= <assignment_expression>
               | <increment_expression>
               | ε

<break_statement> ::= 'break' ';'

<continue_statement> ::= 'continue' ';'

<return_statement> ::= 'return' <expression> ';'
                     | 'return' ';'

<print_statement> ::= 'print' '(' <expression> ')' ';'
```

### Expresiones
```bnf
<expression> ::= <logical_or_expression>

<logical_or_expression> ::= <logical_and_expression>
                          | <logical_or_expression> '||' <logical_and_expression>

<logical_and_expression> ::= <equality_expression>
                           | <logical_and_expression> '&&' <equality_expression>

<equality_expression> ::= <relational_expression>
                        | <equality_expression> '==' <relational_expression>
                        | <equality_expression> '!=' <relational_expression>

<relational_expression> ::= <additive_expression>
                          | <relational_expression> '<' <additive_expression>
                          | <relational_expression> '>' <additive_expression>
                          | <relational_expression> '<=' <additive_expression>
                          | <relational_expression> '>=' <additive_expression>

<additive_expression> ::= <multiplicative_expression>
                        | <additive_expression> '+' <multiplicative_expression>
                        | <additive_expression> '-' <multiplicative_expression>

<multiplicative_expression> ::= <unary_expression>
                              | <multiplicative_expression> '*' <unary_expression>
                              | <multiplicative_expression> '/' <unary_expression>
                              | <multiplicative_expression> '%' <unary_expression>

<unary_expression> ::= <postfix_expression>
                     | '!' <unary_expression>
                     | '-' <unary_expression>
                     | '+' <unary_expression>
                     | '++' <unary_expression>
                     | '--' <unary_expression>

<postfix_expression> ::= <primary_expression>
                       | <postfix_expression> '[' <expression> ']'
                       | <postfix_expression> '(' <argument_list> ')'
                       | <postfix_expression> '++'
                       | <postfix_expression> '--'

<primary_expression> ::= <identifier>
                       | <literal>
                       | '(' <expression> ')'
                       | <special_reference>

<special_reference> ::= '<base>' '(' <expression> ')'
                      | '<breed>' '(' <expression> ')'
                      | '<prop>' '(' <expression> ')'
```

### Expresiones de Asignación e Incremento
```bnf
<assignment_expression> ::= <identifier> '=' <expression>
                          | <identifier> '+=' <expression>
                          | <identifier> '-=' <expression>
                          | <identifier> '*=' <expression>
                          | <identifier> '/=' <expression>

<increment_expression> ::= <identifier> '++'
                         | '++' <identifier>
                         | <identifier> '--'
                         | '--' <identifier>
```

### Literales y Arrays
```bnf
<literal> ::= <integer_literal>
            | <float_literal>
            | <string_literal>
            | <char_literal>
            | <boolean_literal>

<boolean_literal> ::= 'true' | 'false'

<array_literal> ::= '[' <expression_list> ']'
                  | '[' ']'

<expression_list> ::= <expression>
                    | <expression> ',' <expression_list>

<argument_list> ::= <expression>
                  | <expression> ',' <argument_list>
                  | ε
```

### Identificadores y Terminales
```bnf
<identifier> ::= [A-Za-z_][A-Za-z0-9_]*

<integer_literal> ::= '0' | [1-9][0-9]*

<float_literal> ::= [1-9][0-9]*'.'[0-9]+([eE][+-]?[0-9]+)?

<string_literal> ::= '"' ([\x20-\x7E] | escape_sequence)* '"'

<char_literal> ::= "'" ([\x20-\x7E] | escape_sequence) "'"

<escape_sequence> ::= '\' ('a'|'b'|'e'|'f'|'n'|'r'|'t'|'v'|'\'|'"'|"'") 
                    | '\0x'[0-9a-fA-F]{2}
```

### Notas sobre la Gramática

1. **Precedencia de Operadores**: La gramática refleja la precedencia estándar de C/C#
2. **Asociatividad**: Los operadores son asociativos por la izquierda excepto los de asignación
3. **Ambigüedad**: Se evita mediante la estructura jerárquica de las expresiones
4. **Extensibilidad**: Fácil agregar nuevas construcciones siguiendo el patrón
5. **Compatibilidad**: Mantiene compatibilidad con sintaxis familiar de C/C#

---

## Identificadores

### Reglas para Identificadores
- **Patrón**: `[A-Za-z_][A-Za-z0-9_]*`
- **Debe comenzar**: Con letra (a-z, A-Z) o underscore (_)
- **Puede contener**: Letras, números y underscores
- **Token**: `ID`

### Ejemplos Válidos
```
variable
_private
myFunction
user123
MAX_VALUE
```

### Ejemplos Inválidos
```
123invalid  // No puede empezar con número
my-variable // No puede contener guiones
class$      // No puede contener símbolos especiales
```

---

## Comentarios

### 1. Comentarios de Línea
```cpp
// Este es un comentario de línea
int x = 5; // Comentario al final de línea
```

### 2. Comentarios de Bloque
```cpp
/*
Este es un comentario
de múltiples líneas
*/
int y = 10;
```

---

## Manejo de Errores

El lexer incluye detección automática de errores para:

### 1. Números Flotantes Inválidos
```cpp
// Error: Número flotante inválido
0.  // Falta dígitos después del punto
```

### 2. Cadenas Sin Cerrar
```cpp
// Error: Cadena sin cierre de comillas
"Esta cadena no está cerrada
```

### 3. Caracteres Sin Cerrar
```cpp
// Error: Carácter sin cierre de comillas
'a
```

---

## Ejemplos de Código Lizard

### Ejemplo 1: Plugin BepInEx Básico
```cpp
[BepInPlugin("MyMod", "Mi Mod Increíble", "1.0")]

function void Initialize() {
    print("Mod inicializado correctamente");
}
```

### Ejemplo 2: Función con Operaciones
```cpp
function int CalculateMovement(int speed, float power) {
    int steps = 10;
    steps += speed;
    
    if (steps > 5 && power >= 1.0) {
        return <prop>(steps * 2);
    } else {
        return 0;
    }
}
```

### Ejemplo 3: Manejo de Arrays
```cpp
function void ProcessArray() {
    array int numbers = [1, 2, 3, 4, 5];
    
    for (int i = 0; i < 5; ++i) {
        numbers[i] *= 2;
        print("Número procesado: " + numbers[i]);
    }
}
```

### Ejemplo 4: Operaciones Avanzadas
```cpp
function float CalculateDistance(float x1, float y1, float x2, float y2) {
    float deltaX = x2 - x1;
    float deltaY = y2 - y1;
    
    // Usar operadores compuestos
    deltaX *= deltaX;
    deltaY *= deltaY;
    
    return sqrt(deltaX + deltaY);
}
```

---

## Características Técnicas

### Precedencia de Operadores
El lexer maneja correctamente la precedencia reconociendo primero los operadores más largos:
1. `++`, `--` (incremento/decremento)
2. `+=`, `-=`, `*=`, `/=` (asignación compuesta)
3. `==`, `!=`, `<=`, `>=` (comparación)
4. `&&`, `||` (lógicos)
5. `+`, `-`, `*`, `/`, `%` (aritméticos)

### Manejo de Espacios en Blanco
- **Ignorados**: Espacios, tabulaciones, retornos de carro
- **Contabilizados**: Saltos de línea (para reporte de errores)

### Compatibilidad
- ✅ Compatible con sintaxis C/C# básica
- ✅ Extensiones especiales para desarrollo de mods .NET
- ✅ Soporte completo para arrays y operaciones estilo C
- ✅ Integración con BepInEx framework

---

## Notas para Desarrolladores

1. **Orden de Tokens**: Los tokens más específicos están definidos antes que los generales
2. **Escape de Caracteres**: Las expresiones regulares usan escape apropiado para caracteres especiales
3. **Validación**: El lexer incluye validación automática para detectar tokens malformados
4. **Extensibilidad**: Fácil agregar nuevos tokens siguiendo el patrón establecido

---

*Esta documentación cubre la versión actual del LizardLexer para el compilador .rwlz*