import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class StockDataFetcher:
    """Fetch stock price data and technical indicators."""

    def __init__(self):
        self.cache = {}

    def get_stock_data(self, ticker: str, period: str = "1mo") -> Optional[pd.DataFrame]:
        """
        Get historical stock data.

        Args:
            ticker: Stock ticker symbol
            period: Period to fetch ('1d', '5d', '1mo', '3mo', '1y', etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)

            if hist.empty:
                logger.warning(f"No data found for {ticker}")
                return None

            logger.info(f"Fetched {len(hist)} days of data for {ticker}")
            return hist

        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current stock price."""
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")

            if data.empty:
                logger.warning(f"Cannot fetch current price for {ticker}")
                return None

            return float(data["Close"].iloc[-1])

        except Exception as e:
            logger.error(f"Error fetching current price for {ticker}: {e}")
            return None

    def get_stock_info(self, ticker: str) -> Dict:
        """Get general stock information."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            return {
                "ticker": ticker,
                "company_name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }

        except Exception as e:
            logger.error(f"Error fetching stock info for {ticker}: {e}")
            return {}

    def calculate_technical_indicators(self, hist: pd.DataFrame) -> Dict:
        """
        Calculate basic technical indicators.

        Returns:
            Dictionary with indicator values
        """
        try:
            if hist is None or hist.empty:
                return {}

            close = hist["Close"]
            volume = hist["Volume"]

            # Calculate indicators
            rsi = self._calculate_rsi(close)
            macd, signal = self._calculate_macd(close)
            bb_high, bb_mid, bb_low = self._calculate_bollinger_bands(close)

            return {
                "rsi": rsi,
                "macd": macd,
                "macd_signal": signal,
                "bollinger_high": bb_high,
                "bollinger_mid": bb_mid,
                "bollinger_low": bb_low,
                "sma_20": close.rolling(window=20).mean().iloc[-1],
                "sma_50": close.rolling(window=50).mean().iloc[-1],
                "volume_avg": volume.mean(),
                "current_volume": volume.iloc[-1],
            }

        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}

    @staticmethod
    def _calculate_rsi(prices, period=14):
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not rsi.empty else None

    @staticmethod
    def _calculate_macd(prices, fast=12, slow=26, signal=9):
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()

        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()

        return macd.iloc[-1] if not macd.empty else None, \
               macd_signal.iloc[-1] if not macd_signal.empty else None

    @staticmethod
    def _calculate_bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        bb_high = sma + (std * std_dev)
        bb_low = sma - (std * std_dev)

        return bb_high.iloc[-1] if not bb_high.empty else None, \
               sma.iloc[-1] if not sma.empty else None, \
               bb_low.iloc[-1] if not bb_low.empty else None
