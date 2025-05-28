"""
Quick syntax error diagnostic and fix script
"""
import ast
import os
import sys

def check_syntax_errors(file_path):
    """Check for syntax errors in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Try to parse the AST
        ast.parse(source)
        return None  # No syntax errors
        
    except SyntaxError as e:
        return {
            'file': file_path,
            'line': e.lineno,
            'column': e.offset,
            'message': e.msg,
            'text': e.text
        }
    except Exception as e:
        return {
            'file': file_path,
            'error': str(e),
            'type': 'Other'
        }

def scan_src_directory():
    """Scan src directory for syntax errors"""
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    errors = []
    
    for root, dirs, files in os.walk(src_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                error = check_syntax_errors(file_path)
                if error:
                    errors.append(error)
    
    return errors

if __name__ == "__main__":
    print("🔍 Scanning for syntax errors...")
    errors = scan_src_directory()
    
    if errors:
        print(f"❌ Found {len(errors)} syntax errors:")
        for error in errors:
            print(f"   File: {error.get('file', 'Unknown')}")
            print(f"   Line: {error.get('line', 'Unknown')}")
            print(f"   Error: {error.get('message', error.get('error', 'Unknown'))}")
            if 'text' in error and error['text']:
                print(f"   Text: {error['text'].strip()}")
            print()
    else:
        print("✅ No syntax errors found!")
