@echo off
cd C:\project-kortana
echo Running import test...
.test_env\Scripts\python.exe -c "import sys; print('--- sys.path ---'); [print(p) for p in sys.path]; print('--- end sys.path ---')" > import_test_output.txt 2>&1
.test_env\Scripts\python.exe -c "try: from kortana.config import load_config; print('\nSuccessfully imported load_config from kortana.config'); except Exception as e: print(f'\nError: {e}')" >> import_test_output.txt 2>&1
echo Test completed. See import_test_output.txt for results.
type import_test_output.txt
