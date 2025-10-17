# RWLZ Semantic Analyzer Documentation

## Overview

The RWLZ semantic analyzer performs comprehensive type checking and semantic validation for the RWLZ programming language. It ensures that programs are semantically correct before code generation.

## Architecture

The semantic analyzer consists of three main components:

### 1. Type System (`typesys.py`)

Manages type checking and type compatibility rules.

**Key Features:**
- Strong type checking with explicit types
- Type promotion rules (e.g., int → float)
- Array type management
- Support for const qualifiers
- Operator type compatibility checking

**Supported Types:**
- `int` - Integer numbers
- `float` - Floating-point numbers
- `bool` - Boolean values
- `char` - Single characters
- `string` - Text strings
- `void` - No return value
- `auto` - Type inference (limited)
- `array <type>` - Arrays of any base type

**Type Compatibility Rules:**
- Exact type match is always compatible
- Integers can be promoted to floats
- Chars can be promoted to int or float
- Arrays require exact type match (no coercion)
- String concatenation allowed with `+` operator

### 2. Symbol Table (`symtab.py`)

Manages variable and function declarations with proper scoping.

**Key Features:**
- Hierarchical scope management
- Symbol lookup with scope chain traversal
- Function symbol storage with signatures
- Const variable tracking
- Initialization tracking

**Scope Levels:**
- Global scope: Functions and global declarations
- Function scope: Parameters and local variables
- Block scope: Variables in `{ }` blocks
- Loop scope: For loop initialization variables

### 3. Semantic Checker (`checker.py`)

Main visitor that performs all semantic analysis.

**Checks Performed:**

#### Variable Declarations
- ✅ No duplicate declarations in same scope
- ✅ Const variables must be initialized
- ✅ Type compatibility in initialization
- ✅ Array size must be integer
- ✅ Array element types must match

#### Assignments
- ✅ Variable must be declared before use
- ✅ Cannot assign to const variables
- ✅ Type compatibility in assignment
- ✅ Array indices must be integers
- ✅ Compound assignment type checking (`+=`, `-=`, etc.)

#### Function Calls
- ✅ Function must be declared
- ✅ Correct number of arguments
- ✅ Argument types must match parameters
- ✅ Return type checking

#### Control Flow
- ✅ Condition expressions must be boolean
- ✅ `break`/`continue` only inside loops
- ✅ Return statements match function return type
- ✅ Non-void functions should return a value

#### Expressions
- ✅ Binary operators type checking
- ✅ Unary operators type checking
- ✅ Array access type checking
- ✅ Increment/decrement only on numeric types

#### Type Checking
- ✅ Arithmetic operations on numeric types
- ✅ Comparison operations on compatible types
- ✅ Logical operations on boolean types
- ✅ String concatenation with `+`

## Usage

### Command Line Interface

```bash
# Perform semantic analysis only
python rwlz.py --check <filename.rwlz>

# Show symbol table
python rwlz.py --sym <filename.rwlz>

# Both semantic analysis and symbol table
python rwlz.py --check --sym <filename.rwlz>
```

### Programmatic Usage

```python
from Semantic.checker import SemanticChecker
from Parser.parser import LizardParser
from Lexer.lexer import LizardLexer

# Parse the source code
lexer = LizardLexer()
parser = LizardParser()
ast = parser.parse(lexer.tokenize(source_code))

# Run semantic analysis
checker = SemanticChecker()
success = checker.check(ast)

# Get statistics
stats = checker.get_statistics()
print(f"Errors: {stats['errors']}")
print(f"Warnings: {stats['warnings']}")

# Print symbol table
checker.print_symbol_table()
```

## Error Messages

The semantic analyzer provides clear error messages with line numbers:

### Example Errors

```
Error on line 15: Variable 'x' is already defined in this scope
Error on line 23: Cannot assign 'float' to 'int'
Error on line 31: Function 'foo' expects 2 arguments, got 1
Error on line 45: Break statement outside of loop
Error on line 52: Return type 'float' does not match function return type 'int'
```

### Example Warnings

```
Warning on line 18: Variable 'y' may not be initialized
Warning on line 62: Function 'calculate' should return a value of type 'int'
```

## Testing

### Valid Test Cases

Location: `Test/valid_tests/`

- `semantic_test_good.rwlz` - Comprehensive valid semantics test
- `good_*.rwlz` - Additional valid test cases

### Invalid Test Cases

Location: `Test/invalid_tests/`

- `semantic_test_bad.rwlz` - Tests various semantic errors
- `bad_*.rwlz` - Additional invalid test cases

### Running Tests

```bash
# Test valid program
python rwlz.py --check Test/valid_tests/semantic_test_good.rwlz

# Test invalid program (should show errors)
python rwlz.py --check Test/invalid_tests/semantic_test_bad.rwlz

# Test with symbol table display
python rwlz.py --sym Test/ComplexLizard.rwlz
```

## Common Semantic Errors

### 1. Type Mismatch
```c
int x = 3.14;  // Error: Cannot assign float to int
```

### 2. Undeclared Variable
```c
int y = x + 5;  // Error: x is not declared
```

### 3. Const Modification
```c
const int MAX = 100;
MAX = 200;  // Error: Cannot assign to const variable
```

### 4. Invalid Array Access
```c
array int arr = [1, 2, 3];
int val = arr[3.14];  // Error: Array index must be integer
```

### 5. Wrong Function Arguments
```c
int add(int a, int b) { return a + b; }
int result = add(5);  // Error: Expected 2 arguments, got 1
```

### 6. Break Outside Loop
```c
int foo() {
    break;  // Error: Break statement outside of loop
    return 0;
}
```

### 7. Type in Boolean Context
```c
int x = 5;
if (x + 10) {  // Error: Condition must be boolean
    // ...
}
```

### 8. Incompatible Operation
```c
bool flag = true;
int x = flag + 5;  // Error: Cannot add bool and int
```

## Advanced Features

### Type Promotion

The type system supports automatic type promotion:

```c
int x = 5;
float y = x;  // OK: int promotes to float

char c = 'A';
int n = c;    // OK: char promotes to int
```

### Array Type Checking

Arrays are strongly typed:

```c
array int numbers = [1, 2, 3];     // OK
array int mixed = [1, 2.5, 3];     // Error: float in int array
```

### Const Correctness

Const variables cannot be modified:

```c
const int LIMIT = 100;    // Must be initialized
LIMIT += 10;              // Error: Cannot modify const
```

### Scope Rules

Variables are properly scoped:

```c
int x = 10;  // Global scope

int foo() {
    int x = 20;  // Function scope (shadows global)
    
    for (int i = 0; i < 5; ++i) {
        int x = 30;  // Block scope (shadows function)
    }
    
    return x;  // Returns 20 (function scope)
}
```

## Future Enhancements

- [ ] Support for user-defined types/structs
- [ ] More sophisticated type inference
- [ ] Flow analysis for uninitialized variables
- [ ] Dead code detection
- [ ] Unused variable warnings
- [ ] More detailed BepInEx special expression checking

## Implementation Details

### Visitor Pattern

The semantic checker uses the visitor pattern to traverse the AST:

```python
def visit_VarDecl(self, node: VarDecl) -> None:
    # Check for duplicate declaration
    # Check type compatibility
    # Add to symbol table
    # ...
```

### Two-Pass Analysis

1. **First Pass**: Collect all function declarations
2. **Second Pass**: Check function bodies and semantics

This allows forward references to functions.

### Error Recovery

The semantic analyzer continues checking after errors to find multiple errors in one pass. It uses a special `ERROR` type for error recovery.

## Contributing

When adding new semantic checks:

1. Add the check to `SemanticChecker` class
2. Create test cases (both valid and invalid)
3. Update this documentation
4. Ensure error messages are clear and helpful

## License

Part of the RWLZ compiler project.
