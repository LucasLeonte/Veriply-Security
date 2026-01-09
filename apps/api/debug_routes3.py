import sys
sys.path.insert(0, '.')

# Print when verified_qa is imported
original_import = __builtins__.__import__

def tracked_import(name, *args, **kwargs):
    if 'verified_qa' in name:
        print(f'IMPORTING: {name}')
    return original_import(name, *args, **kwargs)

__builtins__.__import__ = tracked_import

# Now import main
from app import main

print(f'\nFinal routes: {len(main.app.routes)}')
v = [r for r in main.app.routes if hasattr(r,'path') and 'verified' in r.path]
print(f'Verified routes: {len(v)}')
