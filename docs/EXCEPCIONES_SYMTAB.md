# 🎯 Excepciones Mejoradas - SymbolTable

## 📋 Resumen

Las excepciones `SymbolDefinedError` y `SymbolConflictError` ahora están **completamente implementadas** con información detallada para facilitar el debugging y reportar errores más precisos.

---

## 🔧 Implementación

### 1. `SymbolDefinedError`

**Propósito:** Se lanza cuando se intenta agregar un símbolo que ya existe con el **mismo tipo**.

**Atributos:**
```python
class SymbolDefinedError(Exception):
    symbol_name: str      # Nombre del símbolo duplicado
    lineno: int          # Línea donde ocurrió el error
    scope_name: str      # Nombre del scope donde está definido
```

**Constructor:**
```python
def __init__(self, symbol_name: str, lineno: int = 0, scope_name: str = ""):
```

**Ejemplo de mensaje:**
```
Symbol 'contador' is already defined in scope 'global' (line 25)
```

---

### 2. `SymbolConflictError`

**Propósito:** Se lanza cuando se intenta agregar un símbolo que ya existe con **tipo diferente**.

**Atributos:**
```python
class SymbolConflictError(Exception):
    symbol_name: str      # Nombre del símbolo en conflicto
    existing_type: Type   # Tipo existente
    new_type: Type        # Tipo que se intentó asignar
    lineno: int          # Línea donde ocurrió el error
    scope_name: str      # Nombre del scope
```

**Constructor:**
```python
def __init__(self, symbol_name: str, existing_type, new_type, 
             lineno: int = 0, scope_name: str = ""):
```

**Ejemplo de mensaje:**
```
Symbol 'valor' already exists with type 'int', cannot redefine as 'float' in scope 'global' (line 30)
```

---

## 💡 Uso

### Ejemplo 1: Capturar SymbolDefinedError

```python
from Semantic.symtab import SymbolTable, Symbol
from Semantic.typesys import RWLZType, BaseType

symtab = SymbolTable()

# Primera declaración
var1 = Symbol(
    name="x",
    symbol_type=RWLZType(base_type=BaseType.INT),
    lineno=10
)
symtab.add("x", var1, raise_on_conflict=True)

# Intento de redeclaración con mismo tipo
var2 = Symbol(
    name="x",
    symbol_type=RWLZType(base_type=BaseType.INT),
    lineno=25
)

try:
    symtab.add("x", var2, raise_on_conflict=True)
except SymbolTable.SymbolDefinedError as e:
    print(f"Error en línea {e.lineno}: {str(e)}")
    # Output: Error en línea 25: Symbol 'x' is already defined in scope 'global' (line 25)
```

### Ejemplo 2: Capturar SymbolConflictError

```python
# Primera declaración (int)
var1 = Symbol(
    name="valor",
    symbol_type=RWLZType(base_type=BaseType.INT),
    lineno=15
)
symtab.add("valor", var1, raise_on_conflict=True)

# Intento de redeclaración con tipo diferente (float)
var2 = Symbol(
    name="valor",
    symbol_type=RWLZType(base_type=BaseType.FLOAT),
    lineno=30
)

try:
    symtab.add("valor", var2, raise_on_conflict=True)
except SymbolTable.SymbolConflictError as e:
    print(f"Error en línea {e.lineno}:")
    print(f"  Símbolo: {e.symbol_name}")
    print(f"  Tipo existente: {e.existing_type}")
    print(f"  Tipo nuevo: {e.new_type}")
    # Output:
    # Error en línea 30:
    #   Símbolo: valor
    #   Tipo existente: int
    #   Tipo nuevo: float
```

### Ejemplo 3: Uso en SemanticChecker

```python
class SemanticChecker:
    def visit_VarDecl(self, node: VarDecl) -> None:
        # Crear símbolo
        symbol = Symbol(
            name=node.name,
            symbol_type=tipo_parseado,
            is_const=node.is_const,
            is_initialized=node.value is not None,
            lineno=node.lineno
        )
        
        # Intentar agregar
        try:
            self.symtab.add(node.name, symbol, raise_on_conflict=True)
        except SymbolTable.SymbolDefinedError as e:
            error(f"Variable '{e.symbol_name}' ya declarada", e.lineno)
            self.errors += 1
        except SymbolTable.SymbolConflictError as e:
            error(
                f"Variable '{e.symbol_name}' ya declarada con tipo '{e.existing_type}', "
                f"no se puede redefinir como '{e.new_type}'",
                e.lineno
            )
            self.errors += 1
```

---

## 🎨 Características

### ✅ Mensajes Informativos

Los mensajes de error se construyen automáticamente con toda la información disponible:

- **Básico:** `Symbol 'x' is already defined`
- **Con línea:** `Symbol 'x' is already defined (line 42)`
- **Completo:** `Symbol 'x' is already defined in scope 'mi_funcion' (line 42)`

### ✅ Atributos Accesibles

Puedes acceder a todos los atributos de la excepción:

```python
try:
    # ... código que puede fallar
except SymbolTable.SymbolConflictError as e:
    # Acceso a atributos
    nombre = e.symbol_name
    tipo_viejo = e.existing_type
    tipo_nuevo = e.new_type
    linea = e.lineno
    scope = e.scope_name
```

### ✅ Compatibilidad Total

Las excepciones son compatibles con el código de referencia:

```python
# Código de referencia (funciona igual)
try:
    symtab.add(name, symbol)
except SymbolTable.SymbolDefinedError:
    print("Ya existe")
except SymbolTable.SymbolConflictError:
    print("Conflicto de tipos")
```

---

## 📊 Comparación

| Característica | Antes | Ahora |
|----------------|-------|-------|
| Excepción declarada | ✅ | ✅ |
| Constructor con parámetros | ❌ | ✅ |
| Atributos accesibles | ❌ | ✅ |
| Mensaje informativo | ❌ | ✅ |
| Información de línea | ❌ | ✅ |
| Información de scope | ❌ | ✅ |
| Tipo existente vs nuevo | ❌ | ✅ |

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests específicos de excepciones
python test_excepciones.py

# Tests de compatibilidad general
python test_symtab_compatibility.py
```

### Tests Incluidos

El archivo `test_excepciones.py` incluye:

1. ✅ **Test 1:** SymbolDefinedError con información detallada
2. ✅ **Test 2:** SymbolConflictError con información detallada
3. ✅ **Test 3:** Excepciones en diferentes scopes
4. ✅ **Test 4:** Verificación de atributos
5. ✅ **Test 5:** Mensajes de error informativos

**Resultado:** ✅ Todos los tests pasan

---

## 📝 Casos de Uso

### Caso 1: Variable Redeclarada (mismo tipo)

```python
# Declaración original
int x = 10;  // línea 10

# Intento de redeclaración
int x = 20;  // línea 25

# Resultado:
# SymbolDefinedError: Symbol 'x' is already defined in scope 'global' (line 25)
```

### Caso 2: Variable con Tipo Diferente

```python
# Declaración original
int contador = 0;  // línea 15

# Intento con tipo diferente
float contador = 0.0;  // línea 30

// Resultado:
// SymbolConflictError: Symbol 'contador' already exists with type 'int',
//                      cannot redefine as 'float' in scope 'global' (line 30)
```

### Caso 3: Variables en Diferentes Scopes

```python
int global_x = 100;

function void test() {
    int local_y = 5;    // línea 20
    float local_y = 5.5; // línea 25 - ERROR
}

// Resultado:
// SymbolConflictError: Symbol 'local_y' already exists with type 'int',
//                      cannot redefine as 'float' in scope 'test' (line 25)
```

---

## 🎯 Ventajas

### Para el Desarrollador
- ✅ Mensajes de error claros y precisos
- ✅ Información completa para debugging
- ✅ Acceso programático a detalles del error

### Para el Usuario Final
- ✅ Errores más informativos
- ✅ Indica exactamente dónde está el problema
- ✅ Explica qué tipos están en conflicto

### Para el Compilador
- ✅ Mejor tracking de errores
- ✅ Reportes más útiles
- ✅ Facilita el análisis de errores múltiples

---

## 🔍 Debugging

### Inspeccionar Excepción Completa

```python
try:
    symtab.add("x", symbol, raise_on_conflict=True)
except SymbolTable.SymbolConflictError as e:
    print(f"ERROR DETECTADO:")
    print(f"  Símbolo: {e.symbol_name}")
    print(f"  Tipo existente: {e.existing_type}")
    print(f"  Tipo nuevo: {e.new_type}")
    print(f"  Línea: {e.lineno}")
    print(f"  Scope: {e.scope_name}")
    print(f"  Mensaje completo: {str(e)}")
```

### Logging de Errores

```python
import logging

logger = logging.getLogger(__name__)

try:
    symtab.add("x", symbol, raise_on_conflict=True)
except SymbolTable.SymbolDefinedError as e:
    logger.error(
        f"Symbol already defined: {e.symbol_name} "
        f"at line {e.lineno} in scope {e.scope_name}"
    )
except SymbolTable.SymbolConflictError as e:
    logger.error(
        f"Type conflict for {e.symbol_name}: "
        f"{e.existing_type} vs {e.new_type} "
        f"at line {e.lineno}"
    )
```

---

## ✅ Checklist de Implementación

- [x] Declaración de excepciones
- [x] Constructor con parámetros
- [x] Atributos accesibles
- [x] Mensajes informativos automáticos
- [x] Información de línea
- [x] Información de scope
- [x] Tipos en conflicto
- [x] Tests completos
- [x] Documentación
- [x] Compatible con código de referencia

---

## 📚 Referencias

- **Archivo:** `src/Semantic/symtab.py` (líneas 91-130)
- **Tests:** `test_excepciones.py`
- **Tests de compatibilidad:** `test_symtab_compatibility.py`
- **Documentación:** `EXCEPCIONES_SYMTAB.md` (este archivo)

---

## 🎉 Resultado Final

Las excepciones ahora están **completamente implementadas** con:

✅ Información detallada  
✅ Mensajes claros  
✅ Atributos accesibles  
✅ Tests pasando (100%)  
✅ Compatible con código de referencia  
✅ Documentación completa

**Estado:** ✅ Producción  
**Versión:** 2.1 (Excepciones implementadas)
