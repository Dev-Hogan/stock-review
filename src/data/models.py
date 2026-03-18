"""
数据模型定义
"""
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Date, Numeric, Text, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


@dataclass
class Stock(Base):
    """股票基本信息"""
    __tablename__ = "stocks"

    code: str = Column(String(10), primary_key=True)
    name: str = Column(String(50), nullable=False)
    industry: Optional[str] = Column(String(50))
    market_cap: Optional[float] = Column(Numeric(20, 2))
    updated_at: datetime = Column(DateTime, default=datetime.now)


@dataclass
class DailyKline(Base):
    """日 K 线数据"""
    __tablename__ = "daily_klines"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    stock_code: str = Column(String(10), nullable=False)
    date: date = Column(Date, nullable=False)
    open: float = Column(Numeric(10, 2), nullable=False)
    high: float = Column(Numeric(10, 2), nullable=False)
    low: float = Column(Numeric(10, 2), nullable=False)
    close: float = Column(Numeric(10, 2), nullable=False)
    volume: int = Column(BigInteger, nullable=False)
    amount: int = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_daily_klines_stock_date", "stock_code", "date", unique=True),
        Index("idx_daily_klines_date", "date"),
    )


@dataclass
class MinuteKline(Base):
    """分钟 K 线数据（用于回放）"""
    __tablename__ = "minute_klines"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    stock_code: str = Column(String(10), nullable=False)
    datetime: datetime = Column(DateTime, nullable=False)
    open: float = Column(Numeric(10, 2), nullable=False)
    high: float = Column(Numeric(10, 2), nullable=False)
    low: float = Column(Numeric(10, 2), nullable=False)
    close: float = Column(Numeric(10, 2), nullable=False)
    volume: int = Column(BigInteger, nullable=False)
    amount: int = Column(BigInteger, nullable=False)

    __table_args__ = (
        Index("idx_minute_klines_stock_datetime", "stock_code", "datetime", unique=True),
        Index("idx_minute_klines_datetime", "datetime"),
    )


@dataclass
class Watchlist(Base):
    """自选股"""
    __tablename__ = "watchlists"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    stock_code: str = Column(String(10), nullable=False, unique=True)
    category: str = Column(String(50), default="默认")
    sort_order: int = Column(Integer, default=0)


@dataclass
class Config(Base):
    """配置表"""
    __tablename__ = "configs"

    key: str = Column(String(100), primary_key=True)
    value: str = Column(Text)
    updated_at: datetime = Column(DateTime, default=datetime.now, onupdate=datetime.now)


@dataclass
class KlineRequest:
    """K 线数据请求参数"""
    stock_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    adjust: str = "qfq"


@dataclass
class StockInfo:
    """股票信息响应"""
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
