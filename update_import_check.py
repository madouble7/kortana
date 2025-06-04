# Create or update the audit package

# First, try fixing imports
python fix_imports.py

# Then run an updated import check
import sys
sys.path.insert(0, 'src')
try:
    import kortana
    print(f"kortana imported from: {kortana.__file__}")
    
    import pkg_resources
    console_scripts = [e.name for e in pkg_resources.iter_entry_points('console_scripts') 
                       if 'kortana' in e.name]
    print(f"console scripts: {console_scripts}")
except Exception as e:
    print(f"Error importing kortana: {e}")
    print(f"sys.path: {sys.path}")
