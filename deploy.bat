@echo off

for /f "tokens=2 delims='" %%a in ('findstr /c:"BUILD_VERSION = " service_tool_app\config.py') do set BUILD_VERSION=%%a

echo.
echo Building Device Configuration Tool v%BUILD_VERSION%

pyinstaller -n cert_flashing_v%BUILD_VERSION% --noconfirm --clean --log-level=WARN ^
--noconsole ^
--onefile ^
--add-data="resources\service_tool.ui;resources" ^
--add-data="resources\ca.pem;resources" ^
--add-data="resources\cc.pem;resources" ^
--add-data="resources\ck.pem;resources" ^
--add-data="resources\accolade-logo.png;resources" ^
service_tool.py

if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete: dist\service_tool_v%BUILD_VERSION%.exe