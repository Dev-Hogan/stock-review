"""
baostock 数据获取层
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Iterator

import baostock as bs

logger = logging.getLogger(__name__)


class BaoStockFetcher:
    """baostock 数据获取器"""

    def __init__(self):
        self._logged_in = False

    def _ensure_login(self):
        """确保已登录"""
        if not self._logged_in:
            bs.login()
            self._logged_in = True

    def _logout(self):
        """登出"""
        if self._logged_in:
            bs.logout()
            self._logged_in = False

    def _query_to_list(self, rs) -> List[Dict]:
        """将 baostock 结果集转换为列表"""
        data = []
        while rs.error_code == '0' and rs.next():
            row = dict(zip(rs.fields, rs.get_row_data()))
            data.append(row)
        return data

    def fetch_stock_list(self) -> List[Dict]:
        """获取 A 股股票列表"""
        logger.info("Fetching A-share stock list via baostock...")
        self._ensure_login()

        rs = bs.query_all_stock(day=date.today().strftime('%Y-%m-%d'))
        stocks = []
        for row in self._query_to_list(rs):
            code = row.get('code', '')
            name = row.get('code_name', '')
            status = row.get('tradeStatus', '')

            if code and name and status == '1':
                if code.startswith(('sh.6', 'sz.0', 'sz.3')):
                    stocks.append({
                        'code': code.split('.')[1],
                        'name': name,
                        'industry': None,
                        'market_cap': None
                    })

        logger.info(f"Fetched {len(stocks)} stocks via baostock")
        return stocks

    def fetch_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        logger.info(f"Fetching info for {stock_code} via baostock...")
        self._ensure_login()

        bs_code = f"sh.{stock_code}" if stock_code.startswith('6') else f"sz.{stock_code}"
        rs = bs.query_stock_basic(code=bs_code)

        for row in self._query_to_list(rs):
            return {
                'code': stock_code,
                'name': row.get('code_name', ''),
                'industry': None,
                'market_cap': None
            }

        return None

    def fetch_daily_klines(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        adjust: str = "qfq"
    ) -> List[Dict]:
        """获取日 K 线数据"""
        logger.info(f"Fetching daily klines for {stock_code} via baostock...")
        self._ensure_login()

        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')

        bs_code = f"sh.{stock_code}" if stock_code.startswith('6') else f"sz.{stock_code}"
        adjustflag = '1' if adjust == 'qfq' else ('2' if adjust == 'hfq' else '3')

        rs = bs.query_history_k_data_plus(
            code=bs_code,
            fields='date,open,high,low,close,volume,amount',
            start_date=start_date,
            end_date=end_date,
            frequency='d',
            adjustflag=adjustflag
        )

        klines = []
        for row in self._query_to_list(rs):
            try:
                klines.append({
                    'stock_code': stock_code,
                    'date': datetime.strptime(row['date'], '%Y-%m-%d').date(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(float(row['volume'])),
                    'amount': int(float(row['amount'])) if row['amount'] else 0
                })
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping invalid kline: {row}, error: {e}")
                continue

        logger.info(f"Fetched {len(klines)} daily klines for {stock_code}")
        return klines

    def fetch_minute_klines(
        self,
        stock_code: str,
        start_date: str = None,
        end_date: str = None,
        period: str = "1"
    ) -> List[Dict]:
        """获取分钟 K 线数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期
            period: 周期 "1", "5", "15", "30", "60"
        """
        logger.info(f"Fetching {period}min klines for {stock_code} via baostock...")
        self._ensure_login()

        if not end_date:
            end_date = date.today().strftime('%Y%m%d')
        if not start_date:
            start_date = (date.today() - timedelta(days=5)).strftime('%Y%m%d')

        bs_code = f"sh.{stock_code}" if stock_code.startswith('6') else f"sz.{stock_code}"

        rs = bs.query_history_k_data_plus(
            code=bs_code,
            fields='date,time,open,high,low,close,volume',
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', ''),
            frequency=period,
            adjustflag='3'
        )

        klines = []
        for row in self._query_to_list(rs):
            try:
                dt_str = row['date'] + ' ' + row['time'][:4]
                klines.append({
                    'stock_code': stock_code,
                    'datetime': datetime.strptime(dt_str, '%Y-%m-%d %H%M'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(float(row['volume'])),
                    'amount': 0
                })
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping invalid minute kline: {row}, error: {e}")
                continue

        logger.info(f"Fetched {len(klines)} minute klines for {stock_code}")
        return klines
