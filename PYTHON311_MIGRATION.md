# Switching to Python 3.11

This guide will help you switch your Kor'tana project from Python 3.13 to Python 3.11.

## Prerequisites

- You need to have Python 3.11 installed on your system
- If not installed, download it from [Python 3.11.6 Download Page](https://www.python.org/downloads/release/python-3116/)

## Steps to Switch

1. **Run the migration script**:
   ```
   switch_to_python311.bat
   ```

2. The script will:
   - Check if Python 3.11 is available
   - Create a new virtual environment called `venv311`
   - Install all dependencies from your requirements.txt file
   - Activate the new environment

3. **After migration**:
   - Your new virtual environment will be in the `venv311` directory
   - To activate it in the future: `venv311\Scripts\activate.bat`
   - To deactivate: `deactivate`

## Troubleshooting

- If the script fails to find Python 3.11, make sure it's installed and in your PATH
- You might need to close and reopen your command prompt after installing Python 3.11
- If any packages fail to install, you can try installing them manually with:
  ```
  pip install package_name
  ```

## Additional Steps

After switching to Python 3.11, you may need to:

1. Update any configuration files that reference specific Python versions
2. Re-test your application to ensure compatibility with Python 3.11
3. Update your `.gitignore` to include the new virtual environment directory
