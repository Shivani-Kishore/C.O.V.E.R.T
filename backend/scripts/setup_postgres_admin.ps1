# C.O.V.E.R.T - PostgreSQL Setup Script
# -----------------------------------------------
# Run this ONE TIME as Administrator in PowerShell:
#   1. Press Win+X -> "Windows PowerShell (Admin)" or "Terminal (Admin)"
#   2. cd "E:\COVERT\C.O.V.E.R.T"
#   3. Set-ExecutionPolicy -Scope Process Bypass
#   4. .\backend\scripts\setup_postgres_admin.ps1

$pgData = "C:\Program Files\PostgreSQL\18\data"
$pgBin  = "C:\Program Files\PostgreSQL\18\bin"
$psql   = "$pgBin\psql.exe"
$pgCtl  = "$pgBin\pg_ctl.exe"
$hba    = "$pgData\pg_hba.conf"
$hbaBak = "$pgData\pg_hba.conf.bak"

Write-Host "=== C.O.V.E.R.T PostgreSQL Setup ===" -ForegroundColor Cyan

# ── Step 1: Backup pg_hba.conf ──────────────────────────────────────────────
Write-Host "`n[1/5] Backing up pg_hba.conf..."
Copy-Item $hba $hbaBak -Force
Write-Host "      OK: $hbaBak"

# ── Step 2: Inject trust line for postgres ───────────────────────────────────
Write-Host "[2/5] Injecting temporary trust rule for postgres user..."
$original = Get-Content $hba -Raw
# Insert a trust rule that only matches postgres user, right before the scram rules
$trustRule = "host    all             postgres        127.0.0.1/32            trust`r`n"
$patched   = $original -replace "(# IPv4 local connections:\r?\n)", "`$1$trustRule"
[System.IO.File]::WriteAllText($hba, $patched)
Write-Host "      OK."

# ── Step 3: Reload pg_hba.conf (no connection needed) ───────────────────────
Write-Host "[3/5] Reloading PostgreSQL config (pg_ctl reload)..."
& $pgCtl reload -D $pgData
if ($LASTEXITCODE -ne 0) {
    Write-Host "      pg_ctl reload failed! Check if PostgreSQL service is running." -ForegroundColor Red
    # Restore backup before exiting
    Copy-Item $hbaBak $hba -Force
    exit 1
}
Start-Sleep -Milliseconds 800   # Give PG a moment to apply the new rules

# ── Step 4: Create role and database ────────────────────────────────────────
Write-Host "[4/5] Creating covert_user and covert_db..."

# 4a: Create/update role
& $psql -U postgres -h 127.0.0.1 -p 5432 -d postgres -c @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'covert_user') THEN
        CREATE ROLE covert_user WITH LOGIN PASSWORD 'covert_password';
        RAISE NOTICE 'Created role covert_user';
    ELSE
        ALTER  ROLE covert_user WITH LOGIN PASSWORD 'covert_password';
        RAISE NOTICE 'Updated password for existing role covert_user';
    END IF;
END
`$`$;
"@
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Failed to create/update role! Restoring pg_hba.conf..." -ForegroundColor Red
    Copy-Item $hbaBak $hba -Force
    & $pgCtl reload -D $pgData | Out-Null
    exit 1
}

# 4b: Create database (CREATE DATABASE can't run inside PL/pgSQL, run conditionally)
$dbExists = & $psql -U postgres -h 127.0.0.1 -p 5432 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='covert_db';"
if ([string]::IsNullOrWhiteSpace($dbExists) -or $dbExists.Trim() -ne "1") {
    & $psql -U postgres -h 127.0.0.1 -p 5432 -d postgres -c "CREATE DATABASE covert_db OWNER covert_user ENCODING 'UTF8';"
    Write-Host "      Created database covert_db."
} else {
    Write-Host "      Database covert_db already exists."
}

# 4c: Grant privileges
& $psql -U postgres -h 127.0.0.1 -p 5432 -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE covert_db TO covert_user;"
& $psql -U postgres -h 127.0.0.1 -p 5432 -d covert_db -c @"
GRANT ALL ON SCHEMA public TO covert_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO covert_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO covert_user;
"@
Write-Host "      Granted privileges."

# ── Step 5: Restore pg_hba.conf ─────────────────────────────────────────────
Write-Host "[5/5] Restoring original pg_hba.conf..."
Copy-Item $hbaBak $hba -Force
& $pgCtl reload -D $pgData
Start-Sleep -Milliseconds 500
Write-Host "      OK — trust rule removed."

# ── Done ─────────────────────────────────────────────────────────────────────
Write-Host "`n=== Setup complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Verify with:" -ForegroundColor Yellow
Write-Host "  `$env:PGPASSWORD='covert_password'; psql -U covert_user -h localhost -p 5432 -d covert_db -c '\conninfo'"
Write-Host ""
Write-Host "Then (from backend/ with venv active):" -ForegroundColor Yellow
Write-Host "  alembic upgrade head"
Write-Host "  uvicorn app.main:app --reload --port 8000"
