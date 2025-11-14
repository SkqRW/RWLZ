"""
LLVM Compiler for RWLZ Language
Handles compilation of LLVM IR to machine code and executable generation.

Responsibility: Convert LLVM IR to object files and link to executables.
Does NOT handle IR generation from AST.
"""

from llvmlite import binding as llvm
from typing import Optional
import subprocess
import platform
import os


class LLVMCompiler:
    """
    Compiles LLVM IR to native executables.
    
    Responsibilities:
    - Parse and verify LLVM IR
    - Compile IR to object files
    - Link object files to executables
    - Handle platform-specific compilation flags
    - Manage intermediate files
    
    Does NOT handle:
    - AST to IR conversion
    - Code generation
    - Type checking
    """
    
    def __init__(self):
        """Initialize the LLVM compiler with native target support."""
        # Initialize LLVM native target and assembly printer
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        
        # Create target machine for current platform
        self.target = llvm.Target.from_default_triple()
        self.target_machine = self.target.create_target_machine()
        
        # Detect current platform
        self.platform = platform.system()
    
    def compile_ir_to_object(self, ir_code: str, obj_filename: str) -> None:
        """
        Compile LLVM IR code to an object file.
        
        Args:
            ir_code: LLVM IR as a string
            obj_filename: Output object file path
            
        Raises:
            RuntimeError: If IR is invalid or compilation fails
        """
        # Parse the IR code
        try:
            mod = llvm.parse_assembly(ir_code)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to parse LLVM IR: {e}")
        
        # Verify the module
        try:
            mod.verify()
        except RuntimeError as e:
            raise RuntimeError(f"LLVM IR verification failed: {e}")
        
        # Compile to object file
        obj_code = self.target_machine.emit_object(mod)
        
        # Write object file
        with open(obj_filename, 'wb') as f:
            f.write(obj_code)
    
    def link_to_executable(self, obj_filename: str, output_filename: str, 
                          cleanup: bool = True) -> None:
        """
        Link object file to executable using system linker.
        
        Args:
            obj_filename: Input object file path
            output_filename: Output executable path
            cleanup: Whether to remove intermediate object file after linking
            
        Raises:
            subprocess.CalledProcessError: If linking fails
            RuntimeError: If platform is unsupported
        """
        # Platform-specific linking
        if self.platform == "Linux":
            # Use gcc with -no-pie flag for Linux
            link_cmd = ['gcc', obj_filename, '-o', output_filename, '-no-pie']
        
        elif self.platform == "Darwin":  # macOS
            # Use clang for macOS
            link_cmd = ['clang', obj_filename, '-o', output_filename]
        
        elif self.platform == "Windows":
            # Use gcc with .exe extension for Windows
            if not output_filename.endswith('.exe'):
                output_filename += '.exe'
            link_cmd = ['gcc', obj_filename, '-o', output_filename]
        
        else:
            raise RuntimeError(f"Unsupported platform: {self.platform}")
        
        # Execute linker command
        try:
            subprocess.run(link_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Linking failed: {e.stderr}")
        
        # Clean up object file if requested
        if cleanup and os.path.exists(obj_filename):
            os.remove(obj_filename)
    
    def compile_to_executable(self, ir_code: str, output_filename: str, 
                             ir_filename: Optional[str] = None,
                             keep_object: bool = False) -> str:
        """
        Full compilation pipeline: IR -> object file -> executable.
        
        Args:
            ir_code: LLVM IR as a string
            output_filename: Output executable path
            ir_filename: Optional path to save IR file (for debugging)
            keep_object: Whether to keep intermediate object file
            
        Returns:
            Path to the generated executable
            
        Raises:
            RuntimeError: If compilation or linking fails
        """
        # Save IR to file if requested (for debugging)
        if ir_filename:
            with open(ir_filename, 'w') as f:
                f.write(ir_code)
        
        # Generate object file name
        obj_filename = output_filename + ".o"
        
        # Compile IR to object file
        self.compile_ir_to_object(ir_code, obj_filename)
        
        # Link to executable
        self.link_to_executable(obj_filename, output_filename, cleanup=not keep_object)
        
        return output_filename
    
    def save_ir_to_file(self, ir_code: str, filename: str) -> None:
        """
        Save LLVM IR code to a file.
        
        Args:
            ir_code: LLVM IR as a string
            filename: Output file path
        """
        with open(filename, 'w') as f:
            f.write(ir_code)
    
    @staticmethod
    def get_platform_info() -> dict:
        """
        Get information about the current platform.
        
        Returns:
            Dictionary with platform information
        """
        return {
            'system': platform.system(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'llvm_triple': llvm.get_default_triple()
        }
