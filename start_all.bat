@echo off
start "" cmd /k "cd /d c:\PostG\backend && python run_server.py"
start "" cmd /k "cd /d c:\PostG\frontend && npm run dev"
