# ============================================================================
# IMMEDIATE FIX FOR "TOO MANY CONNECTIONS" ERROR
# ============================================================================

## Problem Identified:
- Multiple API server processes running (3 uvicorn + 5 python processes)
- Each process holds up to 30 database connections (pool_size=10 + max_overflow=20)
- Total: potentially 240 connections!
- PostgreSQL default max_connections is typically 100

## SOLUTION STEPS:

### Step 1: Kill All API Processes
Run this in PowerShell:
```powershell
# Kill all uvicorn processes
Get-Process uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force

# Kill Python processes related to the API (be careful!)
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*Veriply*"} | Stop-Process -Force
```

OR manually kill them:
```powershell
taskkill /F /PID 4904
taskkill /F /PID 21180
taskkill /F /PID 33560
taskkill /F /PID 424
taskkill /F /PID 6596
taskkill /F /PID 18668
taskkill /F /PID 21080
taskkill /F /PID 31696
```

### Step 2: Reduce Connection Pool Settings
Create or update your .env file with safer settings:

```env
# Reduced connection pool settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
# Total: 15 connections per process (much safer!)
```

### Step 3: Restart PostgreSQL (if needed)
If connections are still stuck, restart PostgreSQL:

**On your Ubuntu database server (10.2.160.214):**
```bash
sudo systemctl restart postgresql
```

### Step 4: Start API Server (Only Once!)
```powershell
cd "C:\Users\tahri\Desktop\IT project\Veriply"
.\.venv\Scripts\Activate.ps1
cd apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Additional Fixes:

### Fix Pydantic V2 Warning:
Search for models using `orm_mode = True` and change to `from_attributes = True`

Example:
```python
# OLD (Pydantic V1):
class Config:
    orm_mode = True

# NEW (Pydantic V2):
model_config = ConfigDict(from_attributes=True)
```

## Prevention:
1. Always stop existing API server before starting a new one
2. Use only ONE terminal for the API server
3. Monitor running processes: `Get-Process uvicorn`
4. Use Docker Compose to avoid multiple instances

## Diagnostic Script:
Run to check connection status:
```powershell
python fix_connection_pool.py
```
