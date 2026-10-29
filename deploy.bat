@echo off

for /f "tokens=2 delims='" %%a in ('findstr /r "BUILD_VERSION=.[\d.]*" service_tool.py') do set BUILD_VERSION=%%a

echo.
echo Building Device Configuration Tool v%BUILD_VERSION%

pyinstaller -n service_tool_v%BUILD_VERSION% --noconfirm --clean --log-level=WARN ^
--noconsole ^
--onefile ^
--add-data="service_tool.ui;." ^
--add-data="resources\ca.pem;resources" ^
--add-data="resources\cc.pem;resources" ^
--add-data="resources\ck.pem;resources" ^
--add-data="resources\accolade-logo.png;resources" ^
service_tool.py

if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete: dist\service_tool_v%BUILD_VERSION%.exe