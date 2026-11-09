# ============================================
# Скрипт для автоматического тестирования API
# Вариант 15: Стоматология «Улыбка»
# Задание 5: API заметок
# ============================================

param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$Help
)

# --------------------------------------------
# Справочная информация
# --------------------------------------------
if ($Help) {
    Write-Host "`nИспользование:" -ForegroundColor Cyan
    Write-Host "  .\run_tests.ps1              - Запуск всех тестов" -ForegroundColor White
    Write-Host "  .\run_tests.ps1 -Help        - Показать справку" -ForegroundColor White
    Write-Host "`nПараметры:" -ForegroundColor Cyan
    Write-Host "  -BaseUrl URL   - URL сервера API (по умолчанию: http://127.0.0.1:8000)" -ForegroundColor White
    Write-Host "`nТребования:" -ForegroundColor Cyan
    Write-Host "  1. Newman установлен: npm install -g newman" -ForegroundColor White
    Write-Host "  2. PostgreSQL запущен" -ForegroundColor White
    Write-Host "  3. FastAPI сервер запущен" -ForegroundColor White
    Write-Host "`n"
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CollectionPath = Join-Path $ScriptDir "api_collection.postman_collection.json"
$EnvironmentPath = Join-Path $ScriptDir "environment.json"
$ResultsDir = Join-Path $ScriptDir "test_results"

# --------------------------------------------
# Цветовые константы
# --------------------------------------------
$ColorSuccess = "Green"
$ColorError = "Red"
$ColorInfo = "Cyan"
$ColorWarning = "Yellow"

# --------------------------------------------
# Функции
# --------------------------------------------
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $ColorInfo
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK]   $Message" -ForegroundColor $ColorSuccess
}

function Write-Error-Msg {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $ColorError
}

function Write-Warning-Msg {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor $ColorWarning
}

# --------------------------------------------
# Проверка требований
# --------------------------------------------
Write-Info "============================================"
Write-Info "  Тестирование API - Стоматология Улыбка"
Write-Info "============================================"
Write-Info ""

# Проверка 1: Newman установлен
Write-Info "Проверка Newman..."
$newman = Get-Command newman -ErrorAction SilentlyContinue
if (-not $newman) {
    Write-Error-Msg "Newman не установлен!"
    Write-Info "Установите: npm install -g newman"
    exit 1
}
Write-Success "Newman установлен"

# Проверка 2: Коллекция существует
Write-Info "Проверка коллекции..."
if (-not (Test-Path $CollectionPath)) {
    Write-Error-Msg "Файл коллекции не найден: $CollectionPath"
    exit 1
}
Write-Success "Коллекция найдена"

# Проверка 3: Сервер доступен
Write-Info "Проверка сервера ($BaseUrl)..."
try {
    $response = Invoke-WebRequest -Uri "$BaseUrl/" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Success "Сервер доступен"
    } else {
        Write-Warning-Msg "Сервер вернул статус $($response.StatusCode)"
    }
} catch {
    Write-Warning-Msg "Сервер недоступен ($BaseUrl)"
    Write-Info "Запустите: python src/api_server.py"
    Write-Info "Продолжаю тестирование..."
}

Write-Info ""

# --------------------------------------------
# Запуск тестов
# --------------------------------------------
Write-Info "Запуск тестов..."
Write-Info ""

# Создаём директорию для результатов
if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir | Out-Null
}

# Формируем параметры для Newman
$newmanArgs = @(
    "run",
    "`"$CollectionPath`""
)

if (Test-Path $EnvironmentPath) {
    $newmanArgs += "-e"
    $newmanArgs += "`"$EnvironmentPath`""
}

# Newman HTML reporter
$htmlPath = Join-Path $ResultsDir "report_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
$newmanArgs += "-r"
$newmanArgs += "html"
$newmanArgs += "--reporter-html-export"
$newmanArgs += "`"$htmlPath`""

# Запуск Newman
Write-Info "Выполнение: newman $($newmanArgs -join ' ')"
Write-Info ""

$newmanOutput = newman @newmanArgs 2>&1

# Вывод результатов
Write-Info ""
Write-Info "============================================"
Write-Info "  Результаты тестирования"
Write-Info "============================================"

# Парсим результаты из вывода Newman
if ($newmanOutput) {
    foreach ($line in $newmanOutput) {
        if ($line -match "(\d+) passing") {
            Write-Success "Тестов прошло: $($matches[1])"
        } elseif ($line -match "(\d+) failing") {
            Write-Error-Msg "Тестов не прошло: $($matches[1])"
        } elseif ($line -match "total") {
            Write-Info "$line"
        } else {
            Write-Host "$line"
        }
    }
}

Write-Info ""
Write-Info "HTML отчёт сохранён в: $htmlPath"
Write-Info ""

# --------------------------------------------
# Альтернативный запуск через Python
# --------------------------------------------
Write-Info "============================================"
Write-Info "  Альтернативное тестирование через Python"
Write-Info "============================================"
Write-Info ""

$PythonTestScript = Join-Path $ScriptDir "..\tests\test_api_python.py"

if (Test-Path $PythonTestScript) {
    Write-Info "Запуск Python-тестов..."
    try {
        python $PythonTestScript -BaseUrl $BaseUrl
        Write-Success "Python-тесты завершены"
    } catch {
        Write-Warning-Msg "Python-тесты не доступны"
    }
} else {
    Write-Info "Python-скрипт тестов не найден: $PythonTestScript"
    Write-Info "Создайте его для автоматизации через pytest"
}

Write-Info ""
Write-Info "============================================"
Write-Info "  Готово!"
Write-Info "============================================"
