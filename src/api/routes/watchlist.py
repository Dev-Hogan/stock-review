"""
自选股相关路由
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.data.storage import Database
from src.data.fetcher import StockFetcher
from src.data.cache import StockDataCache

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

db = Database()
fetcher = StockFetcher(db)
cache = StockDataCache()


class WatchlistItem(BaseModel):
    code: str
    name: Optional[str] = None
    category: str = "默认"


class WatchlistResponse(BaseModel):
    code: str
    name: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None


class AddWatchlistRequest(BaseModel):
    code: str
    category: str = "默认"


class UpdateCategoryRequest(BaseModel):
    code: str
    category: str


@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(category: Optional[str] = None):
    """获取自选股列表"""
    items = db.get_watchlist(category)
    result = []
    for watch_item, stock in items:
        result.append(WatchlistResponse(
            code=stock.code,
            name=stock.name,
            industry=stock.industry,
            market_cap=stock.market_cap
        ))
    return result


@router.post("/", response_model=WatchlistResponse)
async def add_watchlist(req: AddWatchlistRequest):
    """添加自选股"""
    stock = db.get_stock(req.code)
    if not stock:
        stock_info = fetcher.fetch_stock_info(req.code)
        if not stock_info:
            raise HTTPException(status_code=404, detail="股票不存在")
        db.save_stock(req.code, stock_info.name, stock_info.industry, stock_info.market_cap)
        name = stock_info.name
    else:
        name = stock.name

    watch = db.add_watchlist(req.code, req.category)
    return WatchlistResponse(
        code=watch.stock_code,
        name=name
    )


@router.delete("/{code}")
async def remove_watchlist(code: str):
    """删除自选股"""
    success = db.remove_watchlist(code)
    if not success:
        raise HTTPException(status_code=404, detail="自选股不存在")
    return {"success": True}


@router.put("/category")
async def update_category(req: UpdateCategoryRequest):
    """更新自选股分类"""
    success = db.update_watchlist_category(req.code, req.category)
    if not success:
        raise HTTPException(status_code=404, detail="自选股不存在")
    return {"success": True}
