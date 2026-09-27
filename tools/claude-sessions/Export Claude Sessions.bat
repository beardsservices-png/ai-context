@echo off
REM Double-click to copy every Claude Code / VS Code conversation into Google Drive,
REM then check every change those sessions made against GitHub.
REM Safe to run any time: nothing is deleted, no repo is changed.
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
%PY% export_claude_sessions.py
echo.
echo Checking every session's changes against GitHub...
%PY% verify_sessions.py
echo.
pause
