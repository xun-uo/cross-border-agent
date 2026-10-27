@echo off
title Cross-border CS Agent - Demo
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_web.ps1"
pause
