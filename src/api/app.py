"""
FastAPI 应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import config, llm, data, watchlist

app = FastAPI(
    title="Stock Review API",
    description="股票筛选与分析工具 API",
    version="0.1.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(config.router, prefix="/api")
app.include_router(llm.router, prefix="/api")
app.include_router(data.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Stock Review API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
