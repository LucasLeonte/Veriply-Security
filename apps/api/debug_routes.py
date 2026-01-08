import sys
sys.path.insert(0, '.')

# First, check if main.py is cached
print('Checking module cache before import...')
main_cached = 'app.main' in sys.modules
print(f'app.main in cache: {main_cached}')

# Clear it if present  
if main_cached:
    del sys.modules['app.main']

# Now patch BEFORE import
from fastapi import FastAPI
original_include = FastAPI.include_router
call_count = 0

def traced_include(self, router, *args, **kwargs):
    global call_count
    call_count += 1
    prefix = kwargs.get('prefix', '')
    has_verified = any(hasattr(r,'path') and 'verified' in r.path for r in router.routes)
    print(f'Call #{call_count}: prefix="{prefix}", verified={has_verified}')
    return original_include(self, router, *args, **kwargs)

FastAPI.include_router = traced_include

# Import fresh
from app import main
print(f'\nTotal calls: {call_count}')
print(f'Total routes: {len(main.app.routes)}')
