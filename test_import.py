import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Try to import from the query module
try:
    from src.query import create_output_directory

    print('Successfully imported create_output_directory from src.query')
except ImportError as e:
    print(f'Import error: {e}')

# Try to run a function from the module
try:
    from src.query import run_query

    print('Successfully imported run_query from src.query')
except ImportError as e:
    print(f'Import error: {e}')
