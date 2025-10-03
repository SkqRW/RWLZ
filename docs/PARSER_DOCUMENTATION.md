# 🦎 Lizard Language Parser Documentation

## Tabla de Contenidos
- [Introducción](#introducción)
- [Arquitectura del Parser](#arquitectura-del-parser)
- [Gramática EBNF](#gramática-ebnf)
- [Precedencia de Operadores](#precedencia-de-operadores)
- [Tipos de Nodos AST](#tipos-de-nodos-ast)
- [Características Especiales](#características-especiales)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Manejo de Errores](#manejo-de-errores)
- [Resolución de Conflictos](#resolución-de-conflictos)

---

## Introducción

El **Lizard Language Parser** es un analizador sintáctico construido con **SLY (Sly Lex-Yacc)** que convierte una secuencia de tokens en un Árbol de Sintaxis Abstracta (AST). Este parser está específicamente diseñado para el lenguaje Lizard, un lenguaje de programación orientado a la creación de plugins para BepInEx.

### Características Principales
- ✅ **609 líneas de código** organizadas en 11 secciones
- ✅ **Soporte completo** para funciones Base, Breed y Normal
- ✅ **Gramática robusta** con manejo de precedencias
- ✅ **AST rico** con 20+ tipos de nodos
- ✅ **Manejo de errores** integrado
- ✅ **Documentación exhaustiva** con comentarios explicativos

---

## Arquitectura del Parser

### Estructura del Archivo (`parser.py`)

| Sección | Líneas | Descripción |
|---------|--------|-------------|
| **🔧 Configuración** | 28-47 | Precedencias y configuración del parser |
| **📄 Programa Principal** | 48-82 | Reglas para programa y metadata BepInEx |
| **🎯 Funciones** | 83-123 | Definiciones de funciones (Base/Breed/Normal) |
| **📝 Parámetros** | 124-179 | Manejo de parámetros y tipos de datos |
| **📋 Statements** | 180-289 | Declaraciones y sentencias |
| **🔄 Control Flow** | 290-336 | Estructuras de control (if, while, for) |
| **📊 Assignments** | 337-432 | Asignaciones y operadores compuestos |
| **⚡ Expressions** | 433-511 | Expresiones aritméticas y lógicas |
| **🔢 Literals** | 512-569 | Literales y valores constantes |
| **🎭 Special Expressions** | 570-587 | Expresiones especiales (prop, base, breed) |
| **❌ Error Handling** | 588-609 | Manejo de errores de sintaxis |

### Dependencias

```python
from sly import Parser              # Framework de parsing
from Lexer.lexer import LizardLexer # Lexer del lenguaje Lizard
from Utils.model import *           # Nodos del AST
from Utils.model import _L          # Helper para líneas
from Utils.errors import error      # Sistema de errores
```

---

## Gramática EBNF

La siguiente es la gramática formal del lenguaje Lizard en formato Extended Backus-Naur Form (EBNF):

### Programa Principal
```ebnf
program ::= declList 
          | metadataDecl declList

metadataDecl ::= '[' 'BEPINPLUGIN' '(' stringLiteral ',' stringLiteral ',' stringLiteral ')' ']'

declList ::= decl 
           | decl declList
```

### Declaraciones de Funciones
```ebnf
decl ::= type id '(' paramListOpt ')' block
       | 'BREED' type id '(' paramListOpt ')' block
       | 'BASE'  type id '(' paramListOpt ')' block
       | 'HOOK'  type id '(' paramListOpt ')' block
       | 'PROP'  type id '(' paramListOpt ')' block

paramListOpt ::= () 
               | paramList

paramList ::= param 
            | param ',' paramList

param ::= 'CONST' type id
        | type id
```

### Tipos de Datos
```ebnf
type ::= 'ARRAY' type
       | 'AUTO'
       | 'VOID'
       | 'STRING'
       | 'CHAR'
       | 'BOOL'
       | 'FLOAT'
       | 'INT'
```

### Bloques y Declaraciones
```ebnf
block ::= '{' statementList '}'

statementList ::= statement 
                | statementList statement
```

### Declaraciones (Statements)
```ebnf
statement ::= 'PRINT' '(' expr ')' ';'
            | 'RETURN' ';'
            | 'RETURN' expr ';'
            | 'CONTINUE' ';'
            | 'BREAK' ';'
            | 'FOR' '(' forInit ';' forCondition ';' forUpdate ')' block
            | 'WHILE' '(' expr ')' block
            | 'IF' '(' expr ')' block
            | 'IF' '(' expr ')' block 'ELSE' block
            | functionCall ';'
            | id 'decrement' ';'
            | 'decrement' id ';'
            | id 'increment' ';'
            | 'increment' id ';'
            | id '[' expr ']' 'divide_assign' expr ';'
            | id '[' expr ']' 'times_assign' expr ';'
            | id '[' expr ']' 'minus_assign' expr ';'
            | id '[' expr ']' 'plus_assign' expr ';'
            | id '[' expr ']' 'assign' expr ';'
            | id 'divide_assign' expr ';'
            | id 'times_assign' expr ';'
            | id 'minus_assign' expr ';'
            | id 'plus_assign' expr ';'
            | id 'assign' expr ';'
            | type id '[' expr ']' 'assign' '[' exprList ']' ';'
            | type id '[]' 'assign' '[' exprList ']' ';'
            | type id '[' expr ']' ';'
            | 'CONST' type id 'assign' expr ';'
            | type id ';'
            | type id 'assign' expr ';'
```

### Estructuras de Control (For Loop)
```ebnf
forInit ::= () 
          | id 'assign' expr
          | type id 'assign' expr

forCondition ::= () 
               | expr

forUpdate ::= () 
            | incrementExpr
            | assignmentExpr
```

### Llamadas a Funciones
```ebnf
functionCall ::= id '(' argListOpt ')'

argListOpt ::= () 
             | argList

argList ::= expr 
          | argList ',' expr
```

### Listas de Expresiones
```ebnf
exprList ::= expr 
           | exprList ',' expr

assignmentExpr ::= id 'assign' expr

incrementExpr ::= id 'decrement'
                | 'decrement' id
                | id 'increment'
                | 'increment' id
```

### Expresiones
```ebnf
expr ::= 'BREED' '(' expr ')'
       | 'BASE' '(' expr ')'
       | 'PROP' '(' expr ')'
       | id
       | 'FALSE'
       | 'TRUE'
       | charLiteral
       | stringLiteral
       | 'STRING'
       | floatLiteral
       | integerLiteral
       | functionCall
       | '(' expr ')'
       | '[]'
       | '[' exprList ']'
       | id '[' expr ']'
       | incrementExpr
       | '+' expr
       | '-' expr
       | 'NOT' expr
       | expr 'OR' expr
       | expr 'AND' expr
       | expr 'GE' expr
       | expr 'GT' expr
       | expr 'LE' expr
       | expr 'LT' expr
       | expr 'NEQ' expr
       | expr 'EQ' expr
       | expr 'MODULO' expr
       | expr 'DIVIDE' expr
       | expr 'TIMES' expr
       | expr 'MINUS' expr
       | expr 'PLUS' expr
```

### Notas sobre la Gramática EBNF

1. **Formato EBNF**: Utiliza Extended Backus-Naur Form para una sintaxis más clara y concisa
2. **Declaraciones Especializadas**: Soporta declaraciones con prefijos `BREED`, `BASE`, `HOOK`, y `PROP` para desarrollo de mods
3. **Metadata BepInPlugin**: Incluye soporte explícito para atributos de plugins BepInEx
4. **Operadores Tokenizados**: Los operadores se representan como tokens específicos del lexer
5. **Arrays Nativos**: Soporte completo para declaración y manipulación de arrays
6. **Expresiones de Referencias**: Incluye `BREED()`, `BASE()`, y `PROP()` como expresiones especiales
7. **Precedencia Implícita**: La precedencia de operadores está manejada por el parser mediante las reglas de precedencia
8. **Compatibilidad**: Mantiene sintaxis familiar de C/C# con extensiones específicas para mods .NET

---

## Precedencia de Operadores

El parser define una jerarquía de precedencias para resolver ambigüedades:

| Precedencia | Operadores | Asociatividad | Descripción |
|-------------|------------|---------------|-------------|
| **Más baja** | `+=`, `-=`, `*=`, `/=` | Derecha | Asignaciones compuestas |
| | `\|\|` | Izquierda | OR lógico |
| | `&&` | Izquierda | AND lógico |
| | `!` | Derecha | NOT lógico |
| | `<`, `<=`, `>`, `>=`, `==`, `!=` | No asociativo | Comparaciones |
| | `+`, `-` | Izquierda | Suma/Resta |
| | `*`, `/`, `%` | Izquierda | Multiplicación/División |
| | `UMINUS`, `UPLUS` | Derecha | Operadores unarios |
| **Más alta** | `++`, `--` | Izquierda | Incremento/Decremento |

### Ejemplo de Resolución
```lizard
// Sin paréntesis: a + b * c
// Se interpreta como: a + (b * c)
int result = 5 + 3 * 2;  // = 11, no 16

// Con paréntesis explícitos
int result2 = (5 + 3) * 2;  // = 16
```

---

## Tipos de Nodos AST

### Nodos Principales

#### Program
```python
@dataclass
class Program:
    metadata: Optional[Metadata]
    functions: List[Function]
```

#### Metadata (BepInEx)
```python
@dataclass
class Metadata:
    plugin_id: str
    plugin_name: str
    plugin_version: str
```

#### Funciones
```python
@dataclass
class BaseFunction:
    name: str
    return_type: Optional[Type]
    params: List[Parameter]
    body: Block

@dataclass
class BreedFunction:
    name: str
    return_type: Optional[Type]
    params: List[Parameter]
    body: Block

@dataclass  
class NormalFunction:
    name: str
    return_type: Optional[Type]
    params: List[Parameter]
    body: Block
```

### Nodos de Expresiones

#### Operaciones Binarias
```python
@dataclass
class BinaryOperation:
    left: Expression
    operator: str  # +, -, *, /, %, ==, !=, <, >, <=, >=, &&, ||
    right: Expression
```

#### Operaciones Unarias
```python
@dataclass
class UnaryOperation:
    operator: str  # -, !
    operand: Expression

@dataclass
class IncrementExpression:
    variable: str
    operator: str  # ++, --
    is_prefix: bool
```

#### Acceso a Arrays
```python
@dataclass
class ArrayAccess:
    name: str
    index: Expression

@dataclass
class ArrayLiteral:
    elements: List[Expression]
```

### Nodos de Statements

#### Declaraciones
```python
@dataclass
class VarDecl:
    var_type: Type
    name: str
    value: Optional[Expression]
    is_const: bool = False

@dataclass
class Assignment:
    variable: str
    value: Expression

@dataclass
class CompoundAssignment:
    variable: str
    operator: str  # +=, -=, *=, /=
    value: Expression
```

#### Control de Flujo
```python
@dataclass
class IfStatement:
    condition: Expression
    then_block: Block
    else_block: Optional[Block] = None

@dataclass
class WhileStatement:
    condition: Expression
    body: Block

@dataclass
class ForStatement:
    init: Optional[Statement]
    condition: Optional[Expression]
    update: Optional[Statement]
    body: Block
```

### Expresiones Especiales de Lizard

```python
@dataclass
class PropExpression:
    variable: Expression

@dataclass
class BaseExpression:
    expression: Expression

@dataclass
class BreedExpression:
    expression: Expression
```

---

## Características Especiales

### 1. Modificadores de Función
El lenguaje Lizard soporta modificadores especiales para funciones:

#### `<base>` - Función Base
```lizard
<base> int Initialize(int health) {
    // Función que actúa como clase base
    return health * 2;
}
```

#### `<breed>` - Función Breed  
```lizard
<breed> float ProcessDamage(float damage) {
    // Función que hereda comportamiento
    return damage * 1.5;
}
```

### 2. Metadata BepInEx
Soporte para metadata de plugins BepInEx:

```lizard
[BepInPlugin("PluginID", "Plugin Name", "1.0.0")]
```

### 3. Expresiones Especiales
- **`prop(expr)`**: Acceso a propiedades
- **`base(expr)`**: Llamadas a clase base  
- **`breed(expr)`**: Operaciones de herencia

### 4. Arrays Tipados
```lizard
array int numbers = [1, 2, 3, 4, 5];
array float values[10];  // Array de tamaño fijo
```

### 5. Operadores Compuestos Completos
```lizard
// Operadores simples
x += 5;
y -= 3;
z *= 2;
w /= 4;

// Operadores en arrays
numbers[0] += 10;
scores[i] *= 1.5;
```

---

## Ejemplos de Uso

### Programa Completo
```lizard
[BepInPlugin("RainLizard", "Advanced Mod", "2.0")]

<base> int Initialize(int maxHealth, float multiplier) {
    const int MAX_CREATURES = 100;
    int playerHealth = maxHealth;
    array int scores = [10, 20, 30, 40, 50];
    
    // Bucle for con operadores compuestos
    for (int i = 0; i < 5; ++i) {
        scores[i] *= 2;
        playerHealth += scores[i];
    }
    
    // Condicional compleja
    if (playerHealth > 100 && multiplier > 1.0) {
        print("Estado óptimo alcanzado");
        return playerHealth;
    } else {
        print("Requiere mejoras");
        return 0;
    }
}

<breed> float CalculateDamage(float base, bool critical) {
    float damage = base;
    
    if (critical) {
        damage *= 1.5;
    }
    
    return damage;
}

int ProcessData() {
    array int data[10];
    int processed = 0;
    
    while (processed < 10) {
        data[processed] = processed * 2;
        ++processed;
        
        if (data[processed - 1] > 15) {
            break;
        }
    }
    
    return processed;
}
```

### AST Generado
```
Program(
    metadata=Metadata(
        plugin_id="RainLizard",
        plugin_name="Advanced Mod", 
        plugin_version="2.0"
    ),
    functions=[
        BaseFunction(
            name="Initialize",
            return_type=Type(name="int"),
            params=[...],
            body=Block(statements=[...])
        ),
        BreedFunction(...),
        NormalFunction(...)
    ]
)
```

---

## Manejo de Errores

### Tipos de Errores

#### 1. Errores de Sintaxis
```python
def error(self, p):
    """Manejo de errores de sintaxis durante el parsing"""
    if p:
        error(f"Error de sintaxis en el token '{p.value}' (línea {p.lineno})", p.lineno)
    else:
        error("Error de sintaxis: fin de archivo inesperado", 0)
```

#### 2. Ejemplos de Errores Comunes

**Error de Sintaxis:**
```lizard
// ❌ Error: falta punto y coma
int x = 5
int y = 10;

// ✅ Correcto:
int x = 5;
int y = 10;
```

**Error de Paréntesis:**
```lizard
// ❌ Error: paréntesis no balanceados
if (x > 5 {
    print("Mayor que 5");
}

// ✅ Correcto:
if (x > 5) {
    print("Mayor que 5");
}
```

**Error de Tipo de Función:**
```lizard
// ❌ Error: función base sin tipo de retorno
<base> Initialize() {
    return 5;
}

// ✅ Correcto:
<base> int Initialize() {
    return 5;
}
```

### Recuperación de Errores
El parser utiliza el mecanismo de recuperación de errores de SLY:
- Reporta errores con número de línea
- Continúa el análisis cuando es posible
- Proporciona mensajes de error descriptivos

---

## Resolución de Conflictos

### Conflicto Shift/Reduce Conocido

El parser tiene **1 conflicto shift/reduce** en el estado 242, relacionado con el punto y coma:

```
State 242:
    statement -> assignment •
    statement -> assignment • ";"
```

**Resolución:** SLY automáticamente elige **shift** (continuar leyendo tokens), que es el comportamiento correcto para este caso.

### Estrategias de Resolución

1. **Precedencias Explícitas**: Definidas en `precedence` tuple
2. **Reglas Específicas**: Uso de `%prec` para operadores unarios
3. **Asociatividad**: Left, right, o nonassoc según el operador
4. **Orden de Reglas**: Las reglas más específicas van primero

### Ejemplo de Precedencia
```lizard
// Sin precedencias, sería ambiguo:
result = -x + y;

// Con precedencia UMINUS > PLUS:
result = (-x) + y;  // ✅ Interpretación correcta
```

---

## Estadísticas del Parser

### Métricas de Código
- **📊 Total de líneas**: 609
- **🎯 Reglas gramaticales**: ~80 reglas
- **🔧 Tipos de nodos AST**: 25+ tipos
- **⚡ Tokens soportados**: 30+ tokens
- **📋 Precedencias definidas**: 9 niveles

### Capacidades
- ✅ **Funciones procesadas**: Base, Breed, Normal
- ✅ **Statements soportados**: 15+ tipos
- ✅ **Expresiones**: Aritméticas, lógicas, especiales
- ✅ **Control de flujo**: if, while, for, break, continue
- ✅ **Arrays**: Declaración, acceso, literales
- ✅ **Operadores**: Básicos, compuestos, unarios

### Rendimiento
- **🚀 Parsing speed**: ~318 tokens procesados eficientemente
- **💾 Memory usage**: AST optimizado con dataclasses
- **🔄 Error recovery**: Manejo robusto de errores
- **📈 Scalability**: Arquitectura extensible

---

## Conclusión

El **Lizard Language Parser** es una implementación robusta y bien documentada que proporciona:

- 🎯 **Gramática completa** para el lenguaje Lizard
- 🛠️ **AST rico** con todos los tipos de nodos necesarios
- 📚 **Documentación exhaustiva** para mantenimiento
- 🔧 **Arquitectura extensible** para futuras mejoras
- ✅ **Funcionalidad verificada** con casos de prueba

La organización en secciones y la documentación detallada hacen que este parser sea fácil de mantener, extender y depurar, proporcionando una base sólida para el compilador del lenguaje Lizard.

---

*Documentación generada para Lizard Language Parser v1.0*  
*Última actualización: Septiembre 2025*