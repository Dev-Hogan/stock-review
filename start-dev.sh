#!/bin/bash
# 启动开发环境

echo "启动后端服务..."
python -m uvicorn src.api.app:app --reload --port 8000 &
echo "后端服务已启动：http://localhost:8000"

sleep 2

echo "启动前端服务..."
cd web
npm run dev
