"""
数据缓存层
"""
import time
import logging
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    ttl: Optional[int] = None

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


@dataclass
class DataCache:
    """内存数据缓存"""
    _instance: Optional["DataCache"] = None
    _lock = Lock()

    _cache: Dict[str, CacheEntry] = field(default_factory=dict)
    _default_ttl: int = 300

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, default_ttl: int = 300):
        if self._initialized:
            return
        self._cache = {}
        self._default_ttl = default_ttl
        self._initialized = True
        self._lock = Lock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            if entry.is_expired():
                del self._cache[key]
                return None
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        with self._lock:
            self._cache[key] = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl if ttl is not None else self._default_ttl
            )

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: Optional[int] = None
    ) -> Any:
        """获取缓存，如果没有则调用 fetch_func 并缓存结果"""
        cached = self.get(key)
        if cached is not None:
            return cached

        value = fetch_func()
        self.set(key, value, ttl)
        return value

    def invalidate_pattern(self, pattern: str) -> int:
        """根据模式批量删除缓存"""
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)


class StockDataCache:
    """股票数据专用缓存"""

    STOCK_INFO_TTL = 3600
    REALTIME_QUOTE_TTL = 30
    DAILY_KLINE_TTL = 300
    MINUTE_KLINE_TTL = 60

    def __init__(self, cache: DataCache = None):
        self.cache = cache or DataCache()

    def get_stock_info(self, code: str) -> Optional[dict]:
        """获取股票信息缓存"""
        return self.cache.get(f"stock_info:{code}")

    def set_stock_info(self, code: str, info: dict) -> None:
        """设置股票信息缓存"""
        self.cache.set(f"stock_info:{code}", info, self.STOCK_INFO_TTL)

    def get_realtime_quote(self, code: str) -> Optional[dict]:
        """获取实时行情缓存"""
        return self.cache.get(f"realtime_quote:{code}")

    def set_realtime_quote(self, code: str, quote: dict) -> None:
        """设置实时行情缓存"""
        self.cache.set(f"realtime_quote:{code}", quote, self.REALTIME_QUOTE_TTL)

    def get_daily_klines(self, code: str, start_date: str, end_date: str) -> Optional[list]:
        """获取日K线缓存"""
        return self.cache.get(f"daily_klines:{code}:{start_date}:{end_date}")

    def set_daily_klines(self, code: str, start_date: str, end_date: str, klines: list) -> None:
        """设置日K线缓存"""
        self.cache.set(f"daily_klines:{code}:{start_date}:{end_date}", klines, self.DAILY_KLINE_TTL)

    def get_minute_klines(self, code: str, date: str, period: str) -> Optional[list]:
        """获取分钟K线缓存"""
        return self.cache.get(f"minute_klines:{code}:{date}:{period}")

    def set_minute_klines(self, code: str, date: str, period: str, klines: list) -> None:
        """设置分钟K线缓存"""
        self.cache.set(f"minute_klines:{code}:{date}:{period}", klines, self.MINUTE_KLINE_TTL)

    def invalidate_stock(self, code: str) -> None:
        """使某股票相关缓存失效"""
        self.cache.invalidate_pattern(f":{code}:")

    def invalidate_all_quotes(self) -> int:
        """使所有实时行情缓存失效"""
        return self.cache.invalidate_pattern("realtime_quote:")
