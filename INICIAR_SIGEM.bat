@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [SIGEM] Criando ambiente virtual...
    py -m venv .venv
)

call ".venv\Scripts\activate.bat"

if not exist ".env" (
    echo.
    echo [SIGEM] .env nao encontrado.
    echo Copie .env.example para .env e gere as credenciais com:
    echo     python scripts\security.py
    echo.
    pause
    exit /b 1
)

echo [SIGEM] Instalando/validando dependencias...
python -m pip install -r requirements.txt

echo [SIGEM] Iniciando...
python app.py

endlocal
