"""
Windows compatibility module for PySpark.
This must be imported before any PySpark imports.
"""
import sys
import os

if sys.platform == 'win32':
    # Set environment variables before importing PySpark
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['PYSPARK_DRIVER_PYTHON'] = sys.executable
    
    # Patch socketserver before PySpark imports it
    import socketserver
    
    # Create a minimal UnixStreamServer class for Windows compatibility
    # PySpark's accumulators.py tries to reference this class
    if not hasattr(socketserver, 'UnixStreamServer'):
        # Create a class that satisfies PySpark's needs
        # It just needs to exist as a class, it won't actually be instantiated on Windows
        class UnixStreamServer:
            """Dummy UnixStreamServer for Windows compatibility."""
            pass
        
        # Add it to socketserver module
        socketserver.UnixStreamServer = UnixStreamServer

