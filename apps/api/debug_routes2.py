import sys
sys.path.insert(0, '.')

# Import the verified_qa module directly
from app.api.routes import verified_qa

print(f'verified_qa.router: {verified_qa.router}')
print(f'Routes: {len(verified_qa.router.routes)}')
for r in verified_qa.router.routes:
    print(f'  {r.path}')

# Check if router has verified-qa path
has_verified = any(hasattr(r,'path') and 'verified' in r.path for r in verified_qa.router.routes)
print(f'Has verified path: {has_verified}')

# Now let's see what main.py uses
print('\n--- Loading main.py ---')
# Import main's verified_qa
import importlib.util
spec = importlib.util.spec_from_file_location("main_module", "app/main.py")
# Actually just import it
from app.main import app

# Re-check verified_qa
from app.api.routes import verified_qa as vqa2
print(f'\nAfter main import:')
print(f'Same object: {vqa2.router is verified_qa.router}')
print(f'Routes: {len(vqa2.router.routes)}')
