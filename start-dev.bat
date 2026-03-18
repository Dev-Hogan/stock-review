@echo off
REM 启动开发环境

echo 启动后端服务...
start "Backend" cmd /k "python -m uvicorn src.api.app:app --reload --port 8000"

timeout /t 3 /nobreak >nul

echo 启动前端服务...
cd web
npm run dev
