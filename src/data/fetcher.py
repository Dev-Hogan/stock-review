"""
股票数据获取层
支持 baostock（主）和 akshare（备）
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

import akshare as ak
import pandas as pd

from .storage import Database
from .models import StockInfo
from .baostock import BaoStockFetcher

logger = logging.getLogger(__name__)


class StockFetcher:
    """股票数据获取器"""

    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, db: Database = None):
        self.db = db or Database()
        self._bao = BaoStockFetcher()

    def _retry_call(self, func, *args, **kwargs) -> Any:
        """带重试的函数调用"""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY)
        logger.error(f"All {self.MAX_RETRIES} attempts failed")
        raise last_error

    def _try_bao(self, func, *args, **kwargs):
        """尝试使用 baostock"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"BaoStock failed: {e}, trying akshare...")
            raise

    def fetch_stock_list(self) -> List[Dict]:
        """获取 A 股股票列表"""
        logger.info("Fetching A-share stock list...")

        try:
            return self._bao.fetch_stock_list()
        except Exception as e:
            logger.warning(f"BaoStock failed: {e}, falling back to akshare...")

        def _fetch():
            df = ak.stock_zh_a_spot_em()
            return df

        df = self._retry_call(_fetch)

        stocks = []
        for _, row in df.iterrows():
            try:
                code = str(row.get("代码", ""))
                name = str(row.get("名称", ""))
                if code and name and code.startswith(("0", "3", "6")):
                    stocks.append({
                        "code": code,
                        "name": name,
                        "industry": str(row.get("行业", "")) if pd.notna(row.get("行业")) else None,
                        "market_cap": float(row.get("总市值", 0)) if pd.notna(row.get("总市值")) else None
                    })
            except Exception as e:
                logger.debug(f"Skipping row: {e}")
                continue

        logger.info(f"Fetched {len(stocks)} stocks")
        return stocks

    def save_stock_list(self) -> int:
        """获取并保存股票列表"""
        stocks = self.fetch_stock_list()
        count = 0
        for stock in stocks:
            self.db.save_stock(**stock)
            count += 1
        return count

    def fetch_stock_info(self, stock_code: str) -> Optional[StockInfo]:
        """获取股票基本信息"""
        logger.info(f"Fetching info for stock {stock_code}")

        try:
            info = self._bao.fetch_stock_info(stock_code)
            if info:
                return StockInfo(**info)
        except Exception as e:
            logger.warning(f"BaoStock failed for {stock_code}: {e}")

        def _fetch():
            df = ak.stock_individual_info_em(symbol=stock_code)
            return df

        try:
            df = self._retry_call(_fetch)
            info = StockInfo(code=stock_code, name="")

            for _, row in df.iterrows():
                item = row.get("item", "")
                value = row.get("value", "")
                if "股票名称" in item or "名称" in item:
                    info.name = str(value)
                elif "行业" in item:
                    info.industry = str(value)
                elif "总市值" in item:
                    try:
                        info.market_cap = float(value)
                    except:
                        pass

            if not info.name:
                stock = self.db.get_stock(stock_code)
                if stock:
                    info.name = stock.name
                    info.industry = stock.industry
                    info.market_cap = stock.market_cap

            return info
        except Exception as e:
            logger.error(f"Failed to fetch info for {stock_code}: {e}")
            return None

    def fetch_daily_klines(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> List[Dict]:
        """获取日 K 线数据"""
        logger.info(f"Fetching daily klines for {stock_code}")

        try:
            return self._bao.fetch_daily_klines(stock_code, start_date, end_date, adjust)
        except Exception as e:
            logger.warning(f"BaoStock failed for daily klines: {e}")

        if end_date is None:
            end_date = date.today().strftime("%Y%m%d")
        if start_date is None:
            start_date = (date.today() - timedelta(days=365)).strftime("%Y%m%d")

        def _fetch():
            df = ak.stock_zh_a_hist_em(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            return df

        try:
            df = self._retry_call(_fetch)

            klines = []
            for _, row in df.iterrows():
                klines.append({
                    "stock_code": stock_code,
                    "date": pd.to_datetime(row["日期"]).date(),
                    "open": float(row["开盘"]),
                    "high": float(row["最高"]),
                    "low": float(row["最低"]),
                    "close": float(row["收盘"]),
                    "volume": int(row["成交量"]),
                    "amount": int(row["成交额"]) if "成交额" in row else 0
                })

            logger.info(f"Fetched {len(klines)} daily klines for {stock_code}")
            return klines
        except Exception as e:
            logger.error(f"Failed to fetch daily klines for {stock_code}: {e}")
            return []

    def save_daily_klines(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> int:
        """获取并保存日 K 线数据"""
        klines = self.fetch_daily_klines(stock_code, start_date, end_date, adjust)
        if klines:
            return self.db.save_daily_klines(klines)
        return 0

    def fetch_minute_klines(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "1",
        adjust: str = "qfq"
    ) -> List[Dict]:
        """获取分钟 K 线数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            period: 周期 ("1", "5", "15", "30", "60")
            adjust: 复权类型 ("qfq", "hfq", "")
        """
        logger.info(f"Fetching {period}min klines for {stock_code}")

        try:
            return self._bao.fetch_minute_klines(stock_code, start_date, end_date, period)
        except Exception as e:
            logger.warning(f"BaoStock failed for minute klines: {e}")

        if end_date is None:
            end_date = date.today().strftime("%Y%m%d")
        if start_date is None:
            start_date = (date.today() - timedelta(days=5)).strftime("%Y%m%d")

        def _fetch():
            df = ak.stock_zh_a_hist_min_em(
                symbol=stock_code,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            return df

        try:
            df = self._retry_call(_fetch)

            klines = []
            for _, row in df.iterrows():
                try:
                    klines.append({
                        "stock_code": stock_code,
                        "datetime": pd.to_datetime(row["时间"]),
                        "open": float(row["开盘"]),
                        "high": float(row["最高"]),
                        "low": float(row["最低"]),
                        "close": float(row["收盘"]),
                        "volume": int(row["成交量"]) if pd.notna(row["成交量"]) else 0,
                        "amount": int(row["成交额"]) if "成交额" in row and pd.notna(row["成交额"]) else 0
                    })
                except Exception as e:
                    logger.debug(f"Skipping kline row: {e}")
                    continue

            logger.info(f"Fetched {len(klines)} minute klines for {stock_code}")
            return klines
        except Exception as e:
            logger.error(f"Failed to fetch minute klines for {stock_code}: {e}")
            return []

    def save_minute_klines(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "1",
        adjust: str = "qfq"
    ) -> int:
        """获取并保存分钟 K 线数据"""
        klines = self.fetch_minute_klines(stock_code, start_date, end_date, period, adjust)
        if klines:
            return self.db.save_minute_klines(klines)
        return 0

    def fetch_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情（优先 baostock）"""
        logger.info(f"Fetching realtime quote for {stock_code}")

        try:
            info = self._bao.fetch_stock_info(stock_code)
            if info:
                klines = self._bao.fetch_daily_klines(stock_code, 
                    start_date=(date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
                    end_date=date.today().strftime('%Y-%m-%d'))
                if klines:
                    latest = klines[-1]
                    prev = klines[-2] if len(klines) > 1 else latest
                    change = latest['close'] - prev['close']
                    change_percent = (change / prev['close'] * 100) if prev['close'] else 0
                    return {
                        "code": stock_code,
                        "name": info.get('name', ''),
                        "open": latest['open'],
                        "high": latest['high'],
                        "low": latest['low'],
                        "close": latest['close'],
                        "volume": latest['volume'],
                        "amount": latest['amount'],
                        "price_change": change,
                        "change_percent": change_percent
                    }
        except Exception as e:
            logger.warning(f"BaoStock failed for realtime quote: {e}")

        def _fetch():
            df = ak.stock_zh_a_spot_em()
            return df

        try:
            df = self._retry_call(_fetch)
            row = df[df["代码"] == stock_code]
            if row.empty:
                return None

            row = row.iloc[0]
            return {
                "code": str(row["代码"]),
                "name": str(row["名称"]),
                "open": float(row["开盘"]) if pd.notna(row["开盘"]) else 0,
                "high": float(row["最高"]) if pd.notna(row["最高"]) else 0,
                "low": float(row["最低"]) if pd.notna(row["最低"]) else 0,
                "close": float(row["收盘"]) if pd.notna(row["收盘"]) else 0,
                "volume": int(row["成交量"]) if pd.notna(row["成交量"]) else 0,
                "amount": int(row["成交额"]) if pd.notna(row["成交额"]) else 0,
                "price_change": float(row["涨跌额"]) if pd.notna(row["涨跌额"]) else 0,
                "change_percent": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else 0,
            }
        except Exception as e:
            logger.error(f"Failed to fetch realtime quote for {stock_code}: {e}")
            return None

    def batch_update_stocks(
        self,
        stock_codes: List[str] = None,
        include_daily: bool = True,
        include_minute: bool = False
    ) -> Dict:
        """批量更新股票数据"""
        if stock_codes is None:
            stocks = self.db.get_all_stocks()
            stock_codes = [s.code for s in stocks]

        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }

        def update_single(code: str):
            try:
                if include_daily:
                    self.save_daily_klines(code)
                if include_minute:
                    self.save_minute_klines(code)
                return code, True, None
            except Exception as e:
                return code, False, str(e)

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(update_single, code): code for code in stock_codes}
            for future in as_completed(futures):
                code, success, error = future.result()
                if success:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({"code": code, "error": error})

        return results

    def update_stock_with_latest_data(
        self,
        stock_code: str,
        include_minute: bool = True
    ) -> bool:
        """更新单只股票最新数据"""
        try:
            self.fetch_stock_info(stock_code)
            self.save_daily_klines(stock_code)
            if include_minute:
                self.save_minute_klines(stock_code)
            return True
        except Exception as e:
            logger.error(f"Failed to update {stock_code}: {e}")
            return False
