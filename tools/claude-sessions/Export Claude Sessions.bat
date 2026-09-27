@echo off
REM Double-click to copy every Claude Code / VS Code conversation into Google Drive.
REM Safe to run any time: only new or changed sessions are rewritten, nothing is deleted.
cd /d "%~dp0"
where python >nul 2>nul && (python export_claude_sessions.py) || (py export_claude_sessions.py)
echo.
pause
