@echo off
setlocal

echo Activating virtual environment...
call venv\Scripts\activate

if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Failed to install dependencies.
    exit /b 1
)

echo Running project...
python -m src.run_all

if errorlevel 1 (
    echo Project run failed.
    exit /b 1
)

echo Project completed successfully.
endlocal