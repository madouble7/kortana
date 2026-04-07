import re

with open('backend/src/kortana/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add import
if 'matrix_ws,' not in content:
    content = content.replace('live_exerciser,', 'live_exerciser,\n        matrix_ws,')

# Add router mounting
if 'app.include_router(consciousness.router)' in content and 'app.include_router(matrix_ws.router, prefix="/api/matrix")' not in content:
    content = content.replace('app.include_router(consciousness.router)', 'app.include_router(consciousness.router)\n        app.include_router(matrix_ws.router, prefix="/api/matrix", tags=["matrix"])')

with open('backend/src/kortana/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated main.py locally')
