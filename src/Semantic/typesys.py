"""
Type System for RWLZ Language
Handles type checking, type compatibility, and type conversions.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class BaseType(Enum):
    """Basic types in RWLZ language"""
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    CHAR = "char"
    STRING = "string"
    VOID = "void"
    AUTO = "auto" # Placeholder
    ERROR = "error"  # Special type for error recovery
    NULL = "null"  # Special type for null values, not implemented yet

@dataclass
class RWLZType:
    base_type: BaseType
    is_array: bool = False
    is_const: bool = False
    
    def __str__(self):
        prefix = "const " if self.is_const else ""
        array_suffix = "[]" if self.is_array else ""
        return f"{prefix}{self.base_type.value}{array_suffix}"
    
    # This is just for be allow to do RWLZType() == RWLZType()
    def __eq__(self, other):
        if not isinstance(other, RWLZType):
            return False
        return (self.base_type == other.base_type and 
                self.is_array == other.is_array)

    # Not sure, but probably need in the future if i need to do a hash in a dict or set probably
    def __hash__(self):
        return hash((self.base_type, self.is_array))


class TypeSystem:
    """
    Manages type checking and type compatibility rules for RWLZ.
    """
    
    # Arithmetic operations compatibility
    ARITHMETIC_OPS = {'+', '-', '*', '/', '%'}  
    COMPARISON_OPS = {'==', '!=', '<', '>', '<=', '>='}
    LOGICAL_OPS = {'&&', '||'}
    
    # Type promotion rules (from -> to)
    PROMOTION_RULES = {
        BaseType.INT: {BaseType.FLOAT},
        BaseType.FLOAT: {BaseType.INT},  # Allow implicit float to int conversion (with truncation)
        BaseType.CHAR: {BaseType.INT, BaseType.STRING},
        BaseType.BOOL: {BaseType.INT},  
    }
    
    @staticmethod
    def parse_type_name(type_name: str) -> RWLZType:
        """
        Parse a type name string into a RWLZType object.
        Examples: "int", "array int", "const float"
        """
        is_const = False
        is_array = False
        
        parts = type_name.strip().split()
        
        if "const" in parts:
            is_const = True
            parts.remove("const")
        
        if "array" in parts:
            is_array = True
            parts.remove("array")
        
        # Get the base type name
        base_name = parts[0] if parts else "error"
        
        try:
            base_type = BaseType(base_name)
        except ValueError:
            base_type = BaseType.ERROR
        
        return RWLZType(base_type=base_type, is_array=is_array, is_const=is_const)
    
    @staticmethod
    def is_numeric(type_obj: RWLZType) -> bool:
        """Check if a type is numeric (int or float)"""
        return type_obj.base_type in {BaseType.INT, BaseType.FLOAT} and not type_obj.is_array
    
    @staticmethod
    def is_integer(type_obj: RWLZType) -> bool:
        """Check if a type is integer"""
        return type_obj.base_type == BaseType.INT and not type_obj.is_array
    
    @staticmethod
    def is_float(type_obj: RWLZType) -> bool:
        """Check if a type is float"""
        return type_obj.base_type == BaseType.FLOAT and not type_obj.is_array

    @staticmethod
    def is_boolean(type_obj: RWLZType) -> bool:
        """Check if a type is boolean"""
        return type_obj.base_type == BaseType.BOOL and not type_obj.is_array
    
    @staticmethod
    def is_compatible(type1: RWLZType, type2: RWLZType) -> bool:
        """
        Check if two types are compatible for assignment.
        Returns True if type2 can be assigned to type1.
        """
        # For error recovery, allow this
        if type1.base_type == BaseType.ERROR or type2.base_type == BaseType.ERROR:
            return True
        
        # Auto type accepts anything
        if type1.base_type == BaseType.AUTO:
            return True
        
        if type1 == type2:
            return True
        
        # Array compatibility - only exact match
        if type1.is_array or type2.is_array:
            return type1.is_array == type2.is_array and type1.base_type == type2.base_type
        
        # Check type promotion rules
        if type2.base_type in TypeSystem.PROMOTION_RULES:
            if type1.base_type in TypeSystem.PROMOTION_RULES[type2.base_type]:
                return True
        
        return False
    
    @staticmethod
    def check_arithmetic_operation(op: str, left_type: RWLZType, right_type: RWLZType) -> Optional[RWLZType]:
        """
        Check if an arithmetic operation is valid and return the result type.
        Returns None if the operation is invalid.
        """
        # Arrays cannot participate in arithmetic operations directly
        if left_type.is_array or right_type.is_array:
            return None
        
        # String concatenation with +, also allow chars :D
        if op == '+':
            if left_type.base_type == BaseType.STRING or right_type.base_type == BaseType.STRING:
                return RWLZType(base_type=BaseType.STRING)
            if left_type.base_type == BaseType.CHAR and right_type.base_type == BaseType.CHAR:
                return RWLZType(base_type=BaseType.STRING)
            if (left_type.base_type == BaseType.STRING and right_type.base_type == BaseType.CHAR):
                return RWLZType(base_type=BaseType.STRING)

        # Numeric operations
        if op in TypeSystem.ARITHMETIC_OPS:
            # Clowns on me if i ever allow char sums with ascii :leditoroverhead:
            if TypeSystem.is_numeric(left_type) and TypeSystem.is_numeric(right_type):
                # Result is float if either operand is float
                # Boooored, but i not gonna cry with doubles for now
                if left_type.base_type == BaseType.FLOAT or right_type.base_type == BaseType.FLOAT:
                    return RWLZType(base_type=BaseType.FLOAT)
                return RWLZType(base_type=BaseType.INT)
        
        return None
    
    @staticmethod
    def check_comparison_operation(op: str, left_type: RWLZType, right_type: RWLZType) -> Optional[RWLZType]:
        """
        Check if a comparison operation is valid and return bool type.
        Returns None if the operation is invalid.
        """
        # Arrays cannot be compared directly
        # USE A FOR NOT BE LAZY YOU FREAK WHO INVENTED THE STOI C++ FUNCTION
        if left_type.is_array or right_type.is_array:
            return None
        
        # Equality operations work on same types
        if op in {'==', '!='}:
            if TypeSystem.is_compatible(left_type, right_type) or TypeSystem.is_compatible(right_type, left_type):
                return RWLZType(base_type=BaseType.BOOL)
        
        # Ordering operations work on numeric, char, and string types
        if op in {'<', '>', '<=', '>='}:
            # Numeric types
            if TypeSystem.is_numeric(left_type) and TypeSystem.is_numeric(right_type):
                return RWLZType(base_type=BaseType.BOOL)
            
            # Char comparison (by ASCII value)
            # Not gonna allow war crimes and allow to the (a-'0' + 'Z' - 14), what is that char btw?, use a var please
            if left_type.base_type == BaseType.CHAR and right_type.base_type == BaseType.CHAR:
                return RWLZType(base_type=BaseType.BOOL)
            
            # String comparison (lexicographic)
            # But this yes, sad olders versions of c++ havent
            if left_type.base_type == BaseType.STRING and right_type.base_type == BaseType.STRING:
                return RWLZType(base_type=BaseType.BOOL)
        
        return None
    
    @staticmethod
    def check_logical_operation(op: str, left_type: RWLZType, right_type: RWLZType) -> Optional[RWLZType]:
        """
        Check if a logical operation is valid and return bool type.
        Accepts both boolean and numeric types (like C: 0=false, non-zero=true).
        Returns None if the operation is invalid.
        """
        if op in TypeSystem.LOGICAL_OPS:
            # Accept both boolean and numeric types for logical operations
            left_valid = TypeSystem.is_boolean(left_type) or TypeSystem.is_numeric(left_type)
            right_valid = TypeSystem.is_boolean(right_type) or TypeSystem.is_numeric(right_type)
            
            if left_valid and right_valid and not left_type.is_array and not right_type.is_array:
                return RWLZType(base_type=BaseType.BOOL)
        
        return None
    
    @staticmethod
    def check_unary_operation(op: str, operand_type: RWLZType) -> Optional[RWLZType]:
        """
        Check if a unary operation is valid and return the result type.
        Returns None if the operation is invalid.
        """
        if operand_type.is_array:
            return None

        # Logical NOT - accepts boolean or numeric types (like C: 0=false, non-zero=true)
        if op == '!':
            if TypeSystem.is_boolean(operand_type) or TypeSystem.is_numeric(operand_type):
                return RWLZType(base_type=BaseType.BOOL)
        
        # Unary minus/plus - requires numeric
        # not the same as ++, --, those have his own checks
        if op in {'-', '+'}:
            if TypeSystem.is_numeric(operand_type):
                return operand_type
        
        return None
    
    @staticmethod
    def check_increment_decrement(var_type: RWLZType) -> bool:
        """
        Check if increment/decrement operations are valid for a type.
        Only numeric types can be incremented/decremented.
        """
        return TypeSystem.is_numeric(var_type) and not var_type.is_array
    
    @staticmethod
    def get_array_element_type(array_type: RWLZType) -> Optional[RWLZType]:
        """
        Get the element type of an array type.
        Returns None if not an array.
        """
        if not array_type.is_array:
            return None
        
        return RWLZType(base_type=array_type.base_type, is_array=False)
    
    @staticmethod
    def create_array_type(element_type: RWLZType) -> RWLZType:
        """
        Create an array type from an element type.
        """
        # ARRAY [][][][][][][][W]
        return RWLZType(base_type=element_type.base_type, is_array=True, is_const=element_type.is_const)
