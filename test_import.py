import traceback; import sys; try: from kortana.config.schema import KortanaConfig; print('Import successful'); except Exception as e: print(f'Import error: {e}'); traceback.print_exc()  
