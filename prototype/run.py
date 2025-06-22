"""
Kelime Oyunu - Main entry point
-------------------------------
Run this file to start the application
"""
import sys
import os

# Add the project root directory to Python's module search path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main function
from app.main import main

if __name__ == "__main__":
    main() 