import sys
import logging

# Clear any cached modules
for mod in list(sys.modules.keys()):
    if 'app' in mod:
        del sys.modules[mod]

logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s: %(message)s')

try:
    import app.main
    app = app.main.app
    print('\n✓ app loaded')
    
    hitl_routes = [r.path for r in app.routes if 'hitl' in r.path.lower()]
    if hitl_routes:
        print(f'✓ HITL routes registered: {hitl_routes}')
    else:
        print('✗ NO HITL routes')
        
except Exception as e:
    print(f'\n✗ Error: {e}')
    import traceback
    traceback.print_exc()
