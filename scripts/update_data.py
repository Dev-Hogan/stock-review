"""
盘后批量更新脚本

用于在交易时间结束后批量更新股票数据
"""
import sys
import os
import argparse
import logging
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.storage import Database
from src.data.fetcher import StockFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def update_all_stocks(fetcher: StockFetcher, include_minute: bool = False) -> dict:
    """更新所有股票数据"""
    logger.info("Starting batch update for all stocks...")

    stocks = fetcher.db.get_all_stocks()
    total = len(stocks)
    logger.info(f"Total stocks to update: {total}")

    results = {
        "total": total,
        "success": 0,
        "failed": 0,
        "errors": []
    }

    def update_single(code: str):
        try:
            fetcher.update_stock_with_latest_data(code, include_minute=include_minute)
            return code, True, None
        except Exception as e:
            return code, False, str(e)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(update_single, s.code): s.code for s in stocks}

        for i, future in enumerate(as_completed(futures), 1):
            code, success, error = future.result()
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["errors"].append({"code": code, "error": error})

            if i % 50 == 0 or i == total:
                logger.info(f"Progress: {i}/{total}, Success: {results['success']}, Failed: {results['failed']}")

    return results


def update_watchlist_stocks(fetcher: StockFetcher, include_minute: bool = False) -> dict:
    """仅更新自选股"""
    logger.info("Updating watchlist stocks only...")

    watchlist_items = fetcher.db.get_watchlist()
    codes = [w[0].stock_code for w in watchlist_items]

    results = {
        "total": len(codes),
        "success": 0,
        "failed": 0,
        "errors": []
    }

    for code in codes:
        try:
            fetcher.update_stock_with_latest_data(code, include_minute=include_minute)
            results["success"] += 1
            logger.info(f"Updated {code}")
        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"code": code, "error": str(e)})
            logger.error(f"Failed to update {code}: {e}")

    return results


def refresh_stock_list(fetcher: StockFetcher) -> dict:
    """刷新股票列表"""
    logger.info("Refreshing stock list...")
    try:
        count = fetcher.save_stock_list()
        logger.info(f"Stock list refreshed: {count} stocks")
        return {"success": True, "count": count}
    except Exception as e:
        logger.error(f"Failed to refresh stock list: {e}")
        return {"success": False, "error": str(e)}


def update_history_for_stock(fetcher: StockFetcher, stock_code: str, days: int = 365) -> dict:
    """更新单只股票历史数据"""
    logger.info(f"Updating historical data for {stock_code}...")

    end_date = date.today().strftime("%Y%m%d")
    start_date = (date.today() - timedelta(days=days)).strftime("%Y%m%d")

    try:
        klines = fetcher.fetch_daily_klines(stock_code, start_date, end_date)
        if klines:
            saved = fetcher.db.save_daily_klines(klines)
            logger.info(f"Saved {saved} daily klines for {stock_code}")
            return {"success": True, "saved": saved}
        return {"success": False, "error": "No klines fetched"}
    except Exception as e:
        logger.error(f"Failed to update history for {stock_code}: {e}")
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="盘后批量更新股票数据")
    parser.add_argument(
        "--mode",
        choices=["all", "watchlist", "refresh", "history"],
        default="watchlist",
        help="更新模式"
    )
    parser.add_argument(
        "--include-minute",
        action="store_true",
        help="包含分钟K线数据"
    )
    parser.add_argument(
        "--code",
        type=str,
        help="股票代码 (用于 history 模式)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="历史数据天数"
    )

    args = parser.parse_args()

    db = Database()
    fetcher = StockFetcher(db)

    start_time = datetime.now()
    logger.info(f"Update started at {start_time}")

    if args.mode == "all":
        results = update_all_stocks(fetcher, args.include_minute)
    elif args.mode == "watchlist":
        results = update_watchlist_stocks(fetcher, args.include_minute)
    elif args.mode == "refresh":
        results = refresh_stock_list(fetcher)
    elif args.mode == "history":
        if not args.code:
            logger.error("Stock code required for history mode")
            return
        results = update_history_for_stock(fetcher, args.code, args.days)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info(f"Update completed in {duration:.2f} seconds")
    logger.info(f"Results: {results}")

    if results.get("errors"):
        error_file = f"update_errors_{date.today().strftime('%Y%m%d')}.log"
        with open(error_file, "w") as f:
            for err in results["errors"]:
                f.write(f"{err}\n")
        logger.info(f"Errors written to {error_file}")


if __name__ == "__main__":
    main()
