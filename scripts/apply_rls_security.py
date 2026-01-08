"""
Script to add RLS context setting to all API endpoints.
This ensures tenant isolation at the database level.

Usage: python scripts/apply_rls_security.py
"""

import re
from pathlib import Path

# Files to update with RLS context
FILES_TO_UPDATE = [
    "apps/api/app/api/v1/bots.py",
    "apps/api/app/api/v1/documents.py", 
    "apps/api/app/api/v1/groups.py",
    "apps/api/app/api/v1/profile.py",
    "apps/api/app/api/v1/folders.py",
    "apps/api/app/api/v1/bot_access.py",
    "apps/api/app/api/v1/review_queue.py",
    "apps/api/app/api/routes/hitl.py",
    "apps/api/app/api/routes/integrations.py",
    "apps/api/app/api/routes/chat.py",
    "apps/api/app/api/routes/feedback.py",
    "apps/api/app/api/routes/analytics.py",
    "apps/api/app/api/routes/verified_qa.py",
]

# Pattern to match endpoints that need RLS context
ENDPOINT_PATTERN = re.compile(
    r'(@router\.(get|post|put|patch|delete).*?\n)'
    r'(async def \w+\([^)]*)'
    r'(current_user[^)]*)'
    r'(.*?\n.*?""".*?""".*?\n)'
    r'(.*?try:.*?\n)',
    re.DOTALL
)

RLS_CONTEXT_SNIPPET = """        # SECURITY: Set RLS context for tenant isolation
        await set_tenant_context(db, current_user.tenant_id)
        
"""

def add_rls_import(content: str) -> str:
    """Add set_tenant_context import if not present."""
    if "from app.core.database import" in content:
        if "set_tenant_context" not in content:
            content = content.replace(
                "from app.core.database import get_db",
                "from app.core.database import get_db, set_tenant_context"
            )
    return content

def add_rls_context(file_path: Path) -> bool:
    """Add RLS context to endpoints in a file."""
    if not file_path.exists():
        print(f"⚠️  File not found: {file_path}")
        return False
    
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    
    # Add import if missing
    content = add_rls_import(content)
    
    # Count endpoints modified
    modifications = 0
    
    # Find all async functions with current_user and try block
    lines = content.split("\n")
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Look for "try:" after an async def with current_user
        if line.strip() == "try:":
            # Check if we're in an endpoint function
            # Look back to see if this is right after docstring
            if i >= 2 and '"""' in lines[i-1]:
                # Check if function has current_user parameter
                func_start = i - 10  # Look back up to 10 lines
                found_current_user = False
                
                for j in range(max(0, func_start), i):
                    if "current_user" in lines[j] and "Depends(get_current_user)" in lines[j]:
                        found_current_user = True
                        break
                
                if found_current_user:
                    # Check if RLS context already exists
                    if i + 1 < len(lines) and "set_tenant_context" not in lines[i+1]:
                        # Add RLS context
                        new_lines.append("        # SECURITY: Set RLS context for tenant isolation")
                        
                        # Determine tenant_id parameter
                        # Check if it's User object or dict
                        has_user_object = False
                        for j in range(max(0, func_start), i):
                            if "User = Depends(get_current_user)" in lines[j]:
                                has_user_object = True
                                break
                        
                        if has_user_object:
                            # Check if db is named 'db' or 'session'
                            db_name = "db"
                            for j in range(max(0, func_start), i):
                                if "session: AsyncSession" in lines[j]:
                                    db_name = "session"
                                    break
                            
                            new_lines.append(f"        await set_tenant_context({db_name}, current_user.tenant_id)")
                        else:
                            # Dict-based current_user
                            db_name = "db"
                            for j in range(max(0, func_start), i):
                                if "session: AsyncSession" in lines[j]:
                                    db_name = "session"
                                    break
                            new_lines.append(f"        await set_tenant_context({db_name}, UUID(current_user['tenant_id']))")
                        
                        new_lines.append("")
                        modifications += 1
        
        i += 1
    
    if modifications > 0:
        file_path.write_text("\n".join(new_lines), encoding="utf-8")
        print(f"✅ {file_path.name}: Added RLS context to {modifications} endpoints")
        return True
    elif content != original_content:
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ {file_path.name}: Updated imports")
        return True
    else:
        print(f"⏭️  {file_path.name}: No changes needed")
        return False

def main():
    """Apply RLS security to all endpoint files."""
    print("🔒 Applying RLS Security Context to API Endpoints")
    print("=" * 60)
    
    repo_root = Path(__file__).parent.parent
    modified_count = 0
    
    for file_rel_path in FILES_TO_UPDATE:
        file_path = repo_root / file_rel_path
        if add_rls_context(file_path):
            modified_count += 1
    
    print("=" * 60)
    print(f"✅ Complete! Modified {modified_count} files")
    print("\n📝 Next steps:")
    print("1. Review changes with: git diff")
    print("2. Test endpoints to ensure RLS is working")
    print("3. Run security test suite")

if __name__ == "__main__":
    main()
