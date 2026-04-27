param (
    [string]$ServerAddress,
    [string]$SyncToken
)

if (-not $ServerAddress) {
    $ServerAddress = Read-Host "Introduce la dirección SSH (ej: shark@192.168.1.50)"
}

$SERVER   = $ServerAddress
$DEST_DIR = "~/shark-contabilidad"

Write-Host ""
Write-Host "[DEPLOY] Shark Contabilidad"
Write-Host "================================"

# 1. Comprimir todo en un archivo zip localmente (para no pedirte contraseña 10 veces)
Write-Host ""
Write-Host "[1/3] Preparando los archivos (y sincronizando Base de Datos)..."

$DB_PATH = Join-Path $env:USERPROFILE "Shark Contabilidad\budget_app.db"
$HAS_DB = $false
if (Test-Path $DB_PATH) {
    Copy-Item $DB_PATH ".\budget_app.db" -Force
    $HAS_DB = $true
    Write-Host "      -> Base de datos local detectada. Se enviará para sincronizar el servidor." -ForegroundColor Cyan
}

if (Test-Path "app.tar.gz") { Remove-Item "app.tar.gz" }

$ITEMS_TO_PACK = @("Dockerfile", "docker-compose.yml", ".dockerignore", "requirements-web.txt", "controllers", "database", "models", "utils", "locales", "web_app")
if ($HAS_DB) {
    $ITEMS_TO_PACK += "budget_app.db"
}

$TAR_ARGS = $ITEMS_TO_PACK -join " "
Invoke-Expression "tar.exe -czf app.tar.gz $TAR_ARGS"

if (Test-Path ".\budget_app.db") { Remove-Item ".\budget_app.db" }

# 2. Subir el archivo al servidor (SOLO 1 PROMPT DE CONTRASEÑA)
Write-Host "[2/3] Subiendo al servidor..."
Write-Host ">>> TE VA A PEDIR LA CONTRASEÑA DE shark <<<" -ForegroundColor Yellow
scp app.tar.gz ${SERVER}:~/

# 3. Descomprimir y lanzar Docker Compose (SOLO 1 PROMPT DE CONTRASEÑA)
Write-Host "[3/3] Desplegando en el servidor..."
Write-Host ">>> TE VA A PEDIR LA CONTRASEÑA OTRA VEZ <<<" -ForegroundColor Yellow

$INJECT_SECRETKEY = ""
if (-not $SyncToken) {
    $SyncToken = [guid]::NewGuid().ToString("N")
}
Write-Host "     SYNC_TOKEN: $SyncToken" -ForegroundColor Cyan

$INJECT_SECRETKEY = "if grep -q '^SECRET_KEY=' .env; then :; else echo `"SECRET_KEY=`$(openssl rand -hex 32)`" >> .env; fi &&"
$INJECT_TOKEN = "if grep -q '^SYNC_TOKEN=' .env; then sed -i 's/^SYNC_TOKEN=.*/SYNC_TOKEN=$SyncToken/' .env; else echo `"SYNC_TOKEN=$SyncToken`" >> .env; fi &&"

$SSH_COMMAND = @"
    mkdir -p $DEST_DIR &&
    mv ~/app.tar.gz $DEST_DIR/ &&
    cd $DEST_DIR &&
    tar -xzf app.tar.gz &&
    rm app.tar.gz &&
    $INJECT_SECRETKEY
    $INJECT_TOKEN
    docker compose up -d --build &&
    if [ -f budget_app.db ]; then
        echo "Cargando base de datos sincronizada..." &&
        docker cp budget_app.db shark-contabilidad:/data/budget_app.db &&
        docker exec -u root shark-contabilidad chown shark:shark /data/budget_app.db &&
        docker restart shark-contabilidad &&
        rm budget_app.db
    fi
"@

ssh $SERVER $SSH_COMMAND

# Limpiar localmente
if (Test-Path "app.tar.gz") { Remove-Item "app.tar.gz" }

Write-Host ""
Write-Host "[OK] Despliegue completado."
$HOST_ONLY = ($SERVER -split "@")[-1]
Write-Host "     App disponible en: http://${HOST_ONLY}:5000"
Write-Host ""
