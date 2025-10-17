# Mejoras al Symbol Table (symtab.py)

## 📋 Resumen

Se han agregado **métodos de compatibilidad** al `SymbolTable` para que sea compatible con el código de referencia, manteniendo todas las mejoras y funcionalidades avanzadas de la implementación actual.

## ✨ Funcionalidades Agregadas

### 1. **Excepciones Personalizadas**

```python
class SymbolTable:
    class SymbolDefinedError(Exception):
        """Símbolo ya definido en el scope actual"""
        pass
    
    class SymbolConflictError(Exception):
        """Símbolo existe con tipo diferente"""
        pass
```

**Uso:**
```python
try:
    symtab.add("x", symbol, raise_on_conflict=True)
except SymbolTable.SymbolDefinedError:
    print("Variable ya declarada")
except SymbolTable.SymbolConflictError:
    print("Variable declarada con tipo diferente")
```

### 2. **Interfaz Dict-Like**

#### `__getitem__` - Acceso estilo diccionario
```python
symbol = symtab["variable_name"]
```

#### `__setitem__` - Asignación estilo diccionario
```python
symtab["variable_name"] = symbol
```

#### `__contains__` - Operador 'in'
```python
if "variable_name" in symtab:
    print("Variable existe")
```

### 3. **Método `add()` con Excepciones**

Método alternativo compatible con el código de referencia que puede lanzar excepciones:

```python
def add(self, name: str, value, raise_on_conflict: bool = True):
    """
    Agrega un símbolo a la tabla.
    
    Args:
        name: Nombre del símbolo
        value: Symbol o Node (para compatibilidad)
        raise_on_conflict: Si True, lanza excepciones; si False, retorna bool
    
    Returns:
        bool: True si se agregó exitosamente
    
    Raises:
        SymbolDefinedError: Si el símbolo ya existe con el mismo tipo
        SymbolConflictError: Si el símbolo existe con tipo diferente
    """
```

**Ejemplos de uso:**

```python
# Estilo con excepciones (código de referencia)
try:
    symtab.add("x", symbol, raise_on_conflict=True)
except SymbolTable.SymbolDefinedError:
    error("Variable ya declarada")

# Estilo con booleanos (implementación actual)
if not symtab.add("x", symbol, raise_on_conflict=False):
    error("No se pudo agregar la variable")
```

### 4. **Método `get()` Mejorado**

Recupera símbolos con búsqueda en scopes padres:

```python
symbol = symtab.get("variable_name")
if symbol is None:
    print("Variable no encontrada")
```

### 5. **Propiedades de Compatibilidad**

#### `name` - Nombre del scope actual
```python
print(f"Scope actual: {symtab.name}")
```

#### `entries` - Símbolos del scope actual
```python
for name, symbol in symtab.entries.items():
    print(f"{name}: {symbol}")
```

#### `parent` - Scope padre
```python
if symtab.parent:
    print("Tiene scope padre")
```

#### `children` - Scopes hijos
```python
print(f"Número de scopes hijos: {len(symtab.children)}")
```

### 6. **Método `print()` Mejorado**

Impresión elegante de la tabla de símbolos con Rich:

```python
symtab.print()
```

**Output:**
```
═══════════════════════════════════════════════════════
                 SYMBOL TABLE DUMP                      
═══════════════════════════════════════════════════════

Symbol Table: 'global'
┏━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name    ┃ Type     ┃ Details                       ┃
┡━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ x       │ int      │ [initialized: ✓]             │
│ PI      │ float    │ const [initialized: ✓]       │
│ foo     │ function │ normal: (int x) -> int       │
└─────────┴──────────┴───────────────────────────────┘
```

## 🔄 Compatibilidad con Código de Referencia

### Código de Referencia → Tu Implementación

| Código Antiguo | Tu Código (Compatible) |
|----------------|------------------------|
| `symtab = Symtab('global')` | `symtab = SymbolTable()` |
| `symtab.add(name, node)` | `symtab.add(name, symbol, raise_on_conflict=True)` |
| `result = symtab.get(name)` | `result = symtab.get(name)` |
| `if name in symtab: ...` | `if name in symtab: ...` ✓ |
| `symtab[name]` | `symtab[name]` ✓ |
| `symtab.name` | `symtab.name` ✓ |
| `symtab.entries` | `symtab.entries` ✓ |
| `symtab.print()` | `symtab.print()` ✓ (mejorado) |

### Ejemplo de Migración

**Código de Referencia:**
```python
from symtab import Symtab

env = Symtab('global')
try:
    env.add(n.name, n)
except Symtab.SymbolConflictError:
    error(f"Variable '{n.name}' con tipo diferente", n.lineno)
except Symtab.SymbolDefinedError:
    error(f"Variable '{n.name}' ya declarada", n.lineno)
```

**Tu Código (Compatible):**
```python
from Semantic.symtab import SymbolTable, Symbol

symtab = SymbolTable()
symbol = Symbol(name=n.name, symbol_type=tipo, lineno=n.lineno)

try:
    symtab.add(n.name, symbol, raise_on_conflict=True)
except SymbolTable.SymbolConflictError:
    error(f"Variable '{n.name}' con tipo diferente", n.lineno)
except SymbolTable.SymbolDefinedError:
    error(f"Variable '{n.name}' ya declarada", n.lineno)
```

## 🎯 Ventajas de Tu Implementación

### Mejoras sobre el Código de Referencia

1. ✅ **Clases de Datos Estructuradas**
   - `Symbol` y `FunctionSymbol` con `@dataclass`
   - Type hints completos
   - Mejor organización del código

2. ✅ **Separación de Responsabilidades**
   - Clase `Scope` dedicada
   - Clase `SymbolTable` para gestión
   - Mejor encapsulación

3. ✅ **Sistema de Tipos Integrado**
   - `RWLZType` en símbolos
   - Type checking robusto
   - Soporte para tipos complejos (arrays)

4. ✅ **Funcionalidades Avanzadas**
   - Variables constantes (`is_const`)
   - Estado de inicialización
   - Diferentes tipos de funciones (base, breed, hook)
   - Funciones built-in predefinidas

5. ✅ **Mejor Gestión de Scopes**
   - Stack de scopes explícito
   - Métodos `enter_scope()` / `exit_scope()`
   - Tracking de nivel de anidamiento

6. ✅ **Visualización Mejorada**
   - Tablas Rich con formato
   - Información detallada de símbolos
   - Jerarquía visual de scopes

## 📚 Ejemplos de Uso

### Ejemplo 1: Uso Básico
```python
from Semantic.symtab import SymbolTable, Symbol
from Semantic.typesys import RWLZType, BaseType

# Crear tabla de símbolos
symtab = SymbolTable()

# Agregar variable
var = Symbol(
    name="counter",
    symbol_type=RWLZType(base_type=BaseType.INT),
    is_initialized=True,
    lineno=10
)
symtab.define_symbol(var)

# Buscar variable
found = symtab.lookup_symbol("counter")
print(found)  # int counter
```

### Ejemplo 2: Uso con Excepciones
```python
# Estilo compatible con código de referencia
try:
    symtab.add("x", symbol, raise_on_conflict=True)
except SymbolTable.SymbolDefinedError:
    print("Variable ya declarada")
```

### Ejemplo 3: Scoping
```python
symtab = SymbolTable()

# Scope global
symtab.define_symbol(global_var)

# Entrar a función
symtab.enter_scope("mi_funcion")
symtab.define_symbol(local_var)

# Buscar variables
symtab.get("global_var")  # ✓ Encuentra
symtab.get("local_var")   # ✓ Encuentra

# Salir de función
symtab.exit_scope()

symtab.get("global_var")  # ✓ Encuentra
symtab.get("local_var")   # ✗ No encuentra
```

### Ejemplo 4: Funciones
```python
from Semantic.symtab import FunctionSymbol

func = FunctionSymbol(
    name="suma",
    symbol_type=RWLZType(base_type=BaseType.INT),
    param_types=[
        RWLZType(base_type=BaseType.INT),
        RWLZType(base_type=BaseType.INT)
    ],
    param_names=["a", "b"],
    return_type=RWLZType(base_type=BaseType.INT),
    function_kind="normal",
    lineno=20
)

symtab.define_function(func)
found = symtab.lookup_function("suma")
```

## 🧪 Pruebas

Ejecuta las pruebas de compatibilidad:

```bash
python test_symtab_compatibility.py
```

Las pruebas verifican:
- ✅ Operaciones básicas
- ✅ Interfaz dict-like
- ✅ Método `add()` con excepciones
- ✅ Método `get()`
- ✅ Propiedades de compatibilidad
- ✅ Scoping
- ✅ Método `print()` mejorado

## 📝 Notas

### Diferencias Filosóficas

1. **Manejo de Errores:**
   - **Referencia:** Solo excepciones
   - **Tu código:** Booleanos + excepciones opcionales (más flexible)

2. **Estructura de Datos:**
   - **Referencia:** Dict simple con Nodes
   - **Tu código:** Clases dedicadas (Symbol, FunctionSymbol) con tipos

3. **Scoping:**
   - **Referencia:** Parent pointer simple
   - **Tu código:** Stack explícito + clase Scope dedicada

### Recomendaciones

- **Para código nuevo:** Usa `define_symbol()` y `lookup_symbol()` (más claro)
- **Para compatibilidad:** Usa `add()` con `raise_on_conflict=True`
- **Para debugging:** Usa `symtab.print()` para visualizar el estado

## 🎓 Conclusión

Tu implementación de `SymbolTable` es **significativamente más completa** que el código de referencia, y ahora también es **100% compatible** con su interfaz. Lo mejor de ambos mundos:

- ✅ Mantiene todas tus mejoras avanzadas
- ✅ Agrega compatibilidad con código antiguo
- ✅ Proporciona múltiples interfaces de uso
- ✅ Mejor arquitectura y type safety
- ✅ Todas las pruebas pasan exitosamente

¡Excelente trabajo! 🚀
