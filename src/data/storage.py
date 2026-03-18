"""
SQLite 数据库存储层
"""
import os
from datetime import datetime, date
from typing import List, Optional, Tuple
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base, Stock, DailyKline, MinuteKline, Watchlist, Config

logger = logging.getLogger(__name__)


class Database:
    """数据库管理类"""

    _instance: Optional["Database"] = None

    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return

        if db_path is None:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "stock_review.db"
            )

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False)
        self._initialized = True
        self._create_tables()

    def _create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_db(self):
        """初始化数据库"""
        self._create_tables()

    def save_stock(self, code: str, name: str, industry: str = None,
                   market_cap: float = None) -> Stock:
        """保存股票基本信息"""
        with self.get_session() as session:
            stock = session.query(Stock).filter(Stock.code == code).first()
            if stock:
                stock.name = name
                stock.industry = industry
                stock.market_cap = market_cap
                stock.updated_at = datetime.now()
            else:
                stock = Stock(
                    code=code,
                    name=name,
                    industry=industry,
                    market_cap=market_cap,
                    updated_at=datetime.now()
                )
                session.add(stock)
            return stock

    def get_stock(self, code: str) -> Optional[Stock]:
        """获取股票基本信息"""
        with self.get_session() as session:
            return session.query(Stock).filter(Stock.code == code).first()

    def get_all_stocks(self) -> List[Stock]:
        """获取所有股票"""
        with self.get_session() as session:
            return session.query(Stock).order_by(Stock.code).all()

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Stock]:
        """搜索股票"""
        with self.get_session() as session:
            query = session.query(Stock)
            if keyword:
                keyword_pattern = f"%{keyword}%"
                query = query.filter(
                    (Stock.code.like(keyword_pattern)) |
                    (Stock.name.like(keyword_pattern))
                )
            return query.limit(limit).all()

    def save_daily_klines(self, klines: List[dict]) -> int:
        """批量保存日 K 线数据"""
        if not klines:
            return 0

        saved_count = 0
        with self.get_session() as session:
            for kline_data in klines:
                stock_code = kline_data["stock_code"]
                kline_date = kline_data["date"]

                existing = session.query(DailyKline).filter(
                    and_(
                        DailyKline.stock_code == stock_code,
                        DailyKline.date == kline_date
                    )
                ).first()

                if existing:
                    existing.open = kline_data["open"]
                    existing.high = kline_data["high"]
                    existing.low = kline_data["low"]
                    existing.close = kline_data["close"]
                    existing.volume = kline_data["volume"]
                    existing.amount = kline_data["amount"]
                else:
                    kline = DailyKline(**kline_data)
                    session.add(kline)
                saved_count += 1
        return saved_count

    def get_daily_klines(
        self,
        stock_code: str,
        start_date: date = None,
        end_date: date = None,
        limit: int = None
    ) -> List[DailyKline]:
        """获取日 K 线数据"""
        with self.get_session() as session:
            query = session.query(DailyKline).filter(DailyKline.stock_code == stock_code)

            if start_date:
                query = query.filter(DailyKline.date >= start_date)
            if end_date:
                query = query.filter(DailyKline.date <= end_date)

            query = query.order_by(DailyKline.date.desc())

            if limit:
                query = query.limit(limit)

            return query.all()

    def save_minute_klines(self, klines: List[dict]) -> int:
        """批量保存分钟 K 线数据"""
        if not klines:
            return 0

        saved_count = 0
        with self.get_session() as session:
            for kline_data in klines:
                stock_code = kline_data["stock_code"]
                kline_datetime = kline_data["datetime"]

                existing = session.query(MinuteKline).filter(
                    and_(
                        MinuteKline.stock_code == stock_code,
                        MinuteKline.datetime == kline_datetime
                    )
                ).first()

                if existing:
                    existing.open = kline_data["open"]
                    existing.high = kline_data["high"]
                    existing.low = kline_data["low"]
                    existing.close = kline_data["close"]
                    existing.volume = kline_data["volume"]
                    existing.amount = kline_data["amount"]
                else:
                    kline = MinuteKline(**kline_data)
                    session.add(kline)
                saved_count += 1
        return saved_count

    def get_minute_klines(
        self,
        stock_code: str,
        date: date = None,
        start_datetime: datetime = None,
        end_datetime: datetime = None
    ) -> List[MinuteKline]:
        """获取分钟 K 线数据"""
        with self.get_session() as session:
            query = session.query(MinuteKline).filter(MinuteKline.stock_code == stock_code)

            if date:
                query = query.filter(MinuteKline.datetime >= datetime.combine(date, datetime.min.time()))
                query = query.filter(MinuteKline.datetime < datetime.combine(date, datetime.max.time()))
            else:
                if start_datetime:
                    query = query.filter(MinuteKline.datetime >= start_datetime)
                if end_datetime:
                    query = query.filter(MinuteKline.datetime <= end_datetime)

            return query.order_by(MinuteKline.datetime).all()

    def add_watchlist(self, stock_code: str, category: str = "默认") -> Watchlist:
        """添加自选股"""
        with self.get_session() as session:
            existing = session.query(Watchlist).filter(Watchlist.stock_code == stock_code).first()
            if existing:
                return existing

            max_order = session.query(Watchlist).filter(
                Watchlist.category == category
            ).count()

            watchlist = Watchlist(
                stock_code=stock_code,
                category=category,
                sort_order=max_order
            )
            session.add(watchlist)
            return watchlist

    def remove_watchlist(self, stock_code: str) -> bool:
        """删除自选股"""
        with self.get_session() as session:
            watchlist = session.query(Watchlist).filter(
                Watchlist.stock_code == stock_code
            ).first()
            if watchlist:
                session.delete(watchlist)
                return True
            return False

    def get_watchlist(self, category: str = None) -> List[Tuple[Watchlist, Stock]]:
        """获取自选股列表"""
        with self.get_session() as session:
            query = session.query(Watchlist, Stock).join(
                Stock, Watchlist.stock_code == Stock.code
            )
            if category:
                query = query.filter(Watchlist.category == category)
            return query.order_by(Watchlist.sort_order).all()

    def update_watchlist_category(self, stock_code: str, category: str) -> bool:
        """更新自选股分类"""
        with self.get_session() as session:
            watchlist = session.query(Watchlist).filter(
                Watchlist.stock_code == stock_code
            ).first()
            if watchlist:
                watchlist.category = category
                return True
            return False

    def get_config(self, key: str) -> Optional[str]:
        """获取配置"""
        with self.get_session() as session:
            config = session.query(Config).filter(Config.key == key).first()
            return config.value if config else None

    def set_config(self, key: str, value: str) -> Config:
        """设置配置"""
        with self.get_session() as session:
            config = session.query(Config).filter(Config.key == key).first()
            if config:
                config.value = value
                config.updated_at = datetime.now()
            else:
                config = Config(key=key, value=value, updated_at=datetime.now())
                session.add(config)
            return config

    def get_latest_daily_kline_date(self, stock_code: str) -> Optional[date]:
        """获取某股票最新日 K 线日期"""
        with self.get_session() as session:
            kline = session.query(DailyKline).filter(
                DailyKline.stock_code == stock_code
            ).order_by(DailyKline.date.desc()).first()
            return kline.date if kline else None

    def get_latest_minute_kline_datetime(self, stock_code: str, trade_date: date = None) -> Optional[datetime]:
        """获取某股票最新分钟 K 线时间"""
        with self.get_session() as session:
            query = session.query(MinuteKline).filter(
                MinuteKline.stock_code == stock_code
            )
            if trade_date:
                query = query.filter(
                    MinuteKline.datetime >= datetime.combine(trade_date, datetime.min.time())
                )
            kline = query.order_by(MinuteKline.datetime.desc()).first()
            return kline.datetime if kline else None
