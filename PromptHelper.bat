@echo off
setlocal

echo ============================================
echo  PromptHelper - Starting Streamlit App
echo ============================================
echo.

echo [1/3] Changing to app directory...
cd /d "C:\Users\I568274\OneDrive - SAP SE\_PRIVATE\Python\PromptHelper"
if errorlevel 1 (
    echo ERROR: Could not change to app directory.
    pause
    exit /b 1
)
echo.

echo [2/3] Locating Chrome browser...
set "CHROME_PATH="
if exist "%PROGRAMFILES%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"
) else if exist "%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"
) else if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
)

if defined CHROME_PATH (
    echo       Found: %CHROME_PATH%
) else (
    echo       Chrome not found - will use default browser.
)
echo.

echo [3/3] Starting Streamlit server...

if defined CHROME_PATH (
    start "PromptHelper Server" python -m streamlit run app.py --server.headless true
    echo       Waiting for server to initialize...
    timeout /t 3 /nobreak > nul
    echo       Opening in Chrome...
    start "" "%CHROME_PATH%" "http://localhost:8501"
    echo.
    echo  App running at: http://localhost:8501
    echo  To stop the server, close the "PromptHelper Server" window.
) else (
    python -m streamlit run app.py
)

endlocal
