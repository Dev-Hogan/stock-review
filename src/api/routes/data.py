"""
数据查询相关路由
"""

from datetime import datetime, date, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.data.storage import Database
from src.data.fetcher import StockFetcher
from src.data.cache import StockDataCache

router = APIRouter(prefix="/data", tags=["data"])

db = Database()
fetcher = StockFetcher(db)
cache = StockDataCache()


class StockInfoResponse(BaseModel):
    code: str
    name: str
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    amount: Optional[int] = None
    price_change: Optional[float] = None
    change_percent: Optional[float] = None


class DailyKlineResponse(BaseModel):
    stock_code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: int
    turnover: Optional[float] = None


class MinuteKlineResponse(BaseModel):
    stock_code: str
    datetime: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: int


class RealtimeQuoteResponse(BaseModel):
    code: str
    name: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: int
    price_change: float
    change_percent: float


def _format_date(d):
    """确保日期格式为 yyyy-mm-dd"""
    if hasattr(d, "isoformat"):
        return d.isoformat()
    if isinstance(d, str):
        if len(d) == 8 and d.isdigit():
            return f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        return d
    return str(d)


@router.get("/stocks/search")
async def search_stocks(
    keyword: str = Query("", description="搜索关键词"),
    limit: int = Query(20, ge=1, le=100),
):
    """搜索股票"""
    if not keyword:
        return []
    stocks = db.search_stocks(keyword, limit)
    return [
        {
            "code": s["code"],
            "name": s["name"],
            "industry": s.get("industry"),
            "market_cap": s.get("market_cap"),
        }
        for s in stocks
    ]


@router.get("/stocks/{code}/daily", response_model=List[DailyKlineResponse])
async def get_daily_klines(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    limit: int = Query(250, ge=1, le=1000),
):
    """获取日K线数据"""
    start = datetime.strptime(start_date, "%Y%m%d").date() if start_date else None
    end = datetime.strptime(end_date, "%Y%m%d").date() if end_date else None

    db_klines = db.get_daily_klines(code, start, end, limit)

    if not db_klines:
        klines = fetcher.fetch_daily_klines(code, start_date, end_date)
        if klines:
            db.save_daily_klines(klines)
            db_klines = db.get_daily_klines(code, start, end, limit)

    if not db_klines:
        return []

    return [
        DailyKlineResponse(
            stock_code=k["stock_code"],
            date=_format_date(k["date"]),
            open=float(k["open"]),
            high=float(k["high"]),
            low=float(k["low"]),
            close=float(k["close"]),
            volume=k["volume"],
            amount=k["amount"],
        )
        for k in db_klines
    ]


@router.get("/stocks/{code}/info", response_model=StockInfoResponse)
async def get_stock_info(code: str):
    """获取股票基本信息"""
    cached = cache.get_stock_info(code)
    if cached:
        return cached

    info = fetcher.fetch_stock_info(code)
    if not info:
        stock = db.get_stock(code)
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        return StockInfoResponse(
            code=stock["code"],
            name=stock["name"],
            industry=stock["industry"],
            market_cap=stock["market_cap"],
        )

    result = StockInfoResponse(
        code=info.code,
        name=info.name,
        industry=info.industry,
        market_cap=info.market_cap,
        open=info.open,
        high=info.high,
        low=info.low,
        close=info.close,
        volume=info.volume,
        amount=info.amount,
        price_change=info.price_change,
        change_percent=info.change_percent,
    )

    cache.set_stock_info(code, result.model_dump())
    return result


@router.get("/stocks/{code}/daily", response_model=List[DailyKlineResponse])
async def get_daily_klines(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    limit: int = Query(250, ge=1, le=1000),
    refresh: bool = Query(False, description="强制从网络刷新"),
):
    """获取日K线数据"""
    start = datetime.strptime(start_date, "%Y%m%d").date() if start_date else None
    end = datetime.strptime(end_date, "%Y%m%d").date() if end_date else None

    db_klines = db.get_daily_klines(code, start, end, limit)

    if not db_klines or refresh:
        klines = fetcher.fetch_daily_klines(code, start_date, end_date)
        if klines:
            if not db_klines:
                db.save_daily_klines(klines)
            result = [
                DailyKlineResponse(
                    stock_code=k["stock_code"],
                    date=_format_date(k["date"]),
                    open=float(k["open"]),
                    high=float(k["high"]),
                    low=float(k["low"]),
                    close=float(k["close"]),
                    volume=k["volume"],
                    amount=k["amount"],
                    turnover=k.get("turnover"),
                )
                for k in klines
            ]
            return result
        if db_klines:
            pass
        else:
            return []

    result = [
        DailyKlineResponse(
            stock_code=k["stock_code"],
            date=_format_date(k["date"]),
            open=float(k["open"]),
            high=float(k["high"]),
            low=float(k["low"]),
            close=float(k["close"]),
            volume=k["volume"],
            amount=k["amount"],
            turnover=k.get("turnover"),
        )
        for k in db_klines
    ]
    return result


@router.get("/stocks/{code}/minute", response_model=List[MinuteKlineResponse])
async def get_minute_klines(
    code: str,
    date: Optional[str] = Query(None, description="交易日期 YYYYMMDD"),
    period: str = Query("1", description="周期 1/5/15/30/60"),
    start_datetime: Optional[str] = Query(None, description="开始时间"),
    end_datetime: Optional[str] = Query(None, description="结束时间"),
):
    """获取分钟K线数据"""
    trade_date = datetime.strptime(date, "%Y%m%d").date() if date else None
    start_dt = datetime.fromisoformat(start_datetime) if start_datetime else None
    end_dt = datetime.fromisoformat(end_datetime) if end_datetime else None

    db_klines = db.get_minute_klines(code, trade_date, start_dt, end_dt)

    if not db_klines:
        start_str = date or (datetime.now() - timedelta(days=5)).strftime("%Y%m%d")
        end_str = date or datetime.now().strftime("%Y%m%d")

        klines = fetcher.fetch_minute_klines(code, start_str, end_str, period)
        if klines:
            db.save_minute_klines(klines)
            return [
                MinuteKlineResponse(
                    stock_code=k["stock_code"],
                    datetime=k["datetime"].isoformat(),
                    open=k["open"],
                    high=k["high"],
                    low=k["low"],
                    close=k["close"],
                    volume=k["volume"],
                    amount=k["amount"],
                )
                for k in klines
            ]
        return []

    return [
        MinuteKlineResponse(
            stock_code=k.stock_code,
            datetime=k.datetime.isoformat(),
            open=float(k.open),
            high=float(k.high),
            low=float(k.low),
            close=float(k.close),
            volume=k.volume,
            amount=k.amount,
        )
        for k in db_klines
    ]


@router.get("/stocks/{code}/realtime", response_model=RealtimeQuoteResponse)
async def get_realtime_quote(code: str):
    """获取实时行情"""
    cached = cache.get_realtime_quote(code)
    if cached:
        return cached

    quote = fetcher.fetch_realtime_quote(code)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    result = RealtimeQuoteResponse(**quote)
    cache.set_realtime_quote(code, quote)
    return result


@router.post("/stocks/refresh-list")
async def refresh_stock_list():
    """刷新股票列表"""
    try:
        count = fetcher.save_stock_list()
        return {"success": True, "count": count}
    except Exception as e:
        error_msg = str(e)
        if "ProxyError" in error_msg or "Unable to connect" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="网络连接失败：无法访问外部数据源，请检查网络代理配置",
            )
        if "timeout" in error_msg.lower():
            raise HTTPException(status_code=504, detail="请求超时，请稍后重试")
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/stocks/{code}/update")
async def update_stock_data(code: str, include_minute: bool = True):
    """更新单只股票数据"""
    try:
        success = fetcher.update_stock_with_latest_data(code, include_minute)
        if success:
            cache.invalidate_stock(code)
            return {"success": True}
        raise HTTPException(status_code=500, detail="Update failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from datetime import timedelta
