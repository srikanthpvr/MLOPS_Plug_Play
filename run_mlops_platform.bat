@echo off
echo =====================================================================
echo   Autonomous MLOps Build Agent Suite - Plug and Play Launcher
echo   LangChain, LangSmith, LangGraph, Azure Architecture
echo =====================================================================
echo.

set ROOT_DIR=%~dp0

echo [1/3] Generating sample baseline and drifted datasets...
python "%ROOT_DIR%MLOPS_Plug_Play\backend\data\generate_sample_data.py"

echo.
echo [2/3] Starting FastAPI Backend on http://localhost:8000 ...
start "MLOps-Backend-API" cmd /k "cd /d %ROOT_DIR%MLOPS_Plug_Play && set PYTHONPATH=. && python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo [3/3] Starting React 19 Frontend Console on http://localhost:5173 ...
start "MLOps-Frontend-Cockpit" cmd /k "cd /d %ROOT_DIR%MLOPS_Plug_Play\frontend && npm run dev"

echo.
echo =====================================================================
echo   MLOps Platform is now RUNNING!
echo   - Frontend Operations Cockpit: http://localhost:5173
echo   - FastAPI Backend & Swagger:   http://localhost:8000/docs
echo   - Interactive HLD Diagram:     %ROOT_DIR%MLOPS_Plug_Play\mlops_suite_hld_architecture.html
echo =====================================================================
echo.
pause
