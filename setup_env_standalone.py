import subprocess
import sys
import os
import shutil

def setup_environment():
    os.chdir(r'c:\kortana')
    python_exe = r'C:\Program Files\Python311\python.exe'
    venv_path = r'.kortana_config_test_env'
    
    # Check if venv exists
    if os.path.exists(venv_path):
        print(f"Removing existing venv at {venv_path}...")
        try:
            # Try to remove it
            for attempt in range(3):
                try:
                    shutil.rmtree(venv_path)
                    print("Venv removed successfully")
                    break
                except Exception as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    import time
                    time.sleep(1)
        except Exception as e:
            print(f"Could not remove venv: {e}")
            return False
    
    # Create new venv
    print("Creating new virtual environment...")
    try:
        result = subprocess.run([python_exe, '-m', 'venv', venv_path], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Failed to create venv: {result.stderr}")
            return False
        print("Venv created successfully")
    except Exception as e:
        print(f"Error creating venv: {e}")
        return False
    
    # Upgrade pip
    print("Upgrading pip...")
    pip_exe = os.path.join(venv_path, 'Scripts', 'python.exe')
    try:
        result = subprocess.run([pip_exe, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Warning: pip upgrade had issues: {result.stderr}")
    except Exception as e:
        print(f"Error upgrading pip: {e}")
    
    # Install requirements
    print("Installing requirements...")
    try:
        result = subprocess.run([pip_exe, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"Failed to install requirements: {result.stderr}")
            return False
        print("Requirements installed successfully")
    except Exception as e:
        print(f"Error installing requirements: {e}")
        return False
    
    # Install test dependencies
    print("Installing test dependencies...")
    test_packages = ['pytest', 'pytest-asyncio', 'pytest-mock']
    try:
        result = subprocess.run([pip_exe, '-m', 'pip', 'install'] + test_packages, 
                              capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Failed to install test deps: {result.stderr}")
            return False
        print("Test dependencies installed successfully")
    except Exception as e:
        print(f"Error installing test dependencies: {e}")
        return False
    
    print("\n" + "="*50)
    print("SUCCESS: Environment ready!")
    print("="*50)
    return True

if __name__ == '__main__':
    success = setup_environment()
    sys.exit(0 if success else 1)
