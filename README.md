# USA Stock Analyzing - Real-time Stock Prediction System

A comprehensive system for detecting market events, analyzing financial news, and predicting stock price movements based on sentiment analysis and technical indicators.

## Project Overview

This project analyzes major US news and community information to:
1. **Detect Events**: Identify earnings announcements, contracts, acquisitions, and other market-moving news
2. **Analyze Sentiment**: Assess positive/negative sentiment from news and social media
3. **Predict Prices**: Generate real-time stock price direction and range predictions
4. **Visualize Results**: Display predictions and analysis on an interactive web dashboard

## Phases

### Phase 1: Data Collection & Event Detection ✅
- Fetch financial news from NewsAPI
- Detect market events (earnings, contracts, acquisitions, etc.)
- Extract and validate stock tickers from news
- Collect historical stock data and technical indicators
- **Status**: Complete

### Phase 2: Sentiment Analysis & Feature Engineering (Next)
- NLP-based sentiment analysis using transformers
- Community sentiment from Reddit, StockTwits
- Technical indicator calculations
- Feature engineering for ML models

### Phase 3: Machine Learning Models
- Binary classification: Stock direction (up/down)
- Regression: Price range prediction (±%)
- Model training and backtesting
- Feature importance analysis

### Phase 4: Real-time Pipeline
- APScheduler for hourly updates
- FastAPI for manual trigger endpoints
- Event notification system
- Historical prediction tracking

### Phase 5: Web Dashboard
- FastAPI backend
- React/Vue.js frontend
- Real-time prediction updates
- News and sentiment visualization
- Stock performance comparison

## Setup

### Prerequisites
- Python 3.9+
- NewsAPI key (free at https://newsapi.org)
- Optional: Alpha Vantage API key for additional data

### Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd USA-stock-analyzing
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

### Running Phase 1

```bash
python main.py
```

This will:
1. Fetch latest financial news
2. Detect market events
3. Extract affected stock tickers
4. Fetch current stock data and technical indicators
5. Save results to `phase1_results_*.json`

## Project Structure

```
USA-stock-analyzing/
├── config/
│   ├── __init__.py
│   └── config.py              # Configuration and constants
├── data_collection/
│   ├── __init__.py
│   ├── news_fetcher.py        # NewsAPI integration
│   ├── stock_data_fetcher.py  # yfinance integration
│   └── event_detector.py      # Event detection logic
├── models/                    # ML models (Phase 3)
├── database/                  # Database layer (Phase 4)
├── utils/
│   ├── __init__.py
│   └── logger.py              # Logging configuration
├── main.py                    # Phase 1 main script
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

### Event Keywords (config.py)

The system detects the following event types:
- **earnings**: Quarterly/annual earnings reports
- **acquisition**: Mergers and acquisitions
- **contract**: New contracts and partnerships
- **product**: Product launches and releases
- **regulatory**: FDA approvals and regulatory news
- **bankruptcy**: Bankruptcy filings
- **executive**: Executive changes and resignations

### Stock Ticker Extraction

The system uses multiple strategies to extract tickers:
1. Explicit `$TICKER` format in text
2. Uppercase letter sequences (2-5 letters)
3. Filtering common English words
4. Title prioritization for accuracy

## API Keys

### NewsAPI (Required)
- Sign up at: https://newsapi.org
- Free tier: 100 requests/day
- Add to `.env`: `NEWS_API_KEY=your_key_here`

### Alpha Vantage (Optional)
- Sign up at: https://www.alphavantage.co
- Free tier: 5 requests/min, 500/day
- Add to `.env`: `ALPHA_VANTAGE_API_KEY=your_key_here`

## Output Format

Phase 1 generates JSON output with:

```json
{
  "timestamp": "2026-04-30T...",
  "detected_events": [
    {
      "event_type": "earnings",
      "title": "Apple Reports Q2 Earnings",
      "tickers": ["AAPL"],
      "published_at": "2026-04-30T...",
      "url": "..."
    }
  ],
  "stocks_by_event_type": {
    "earnings": ["AAPL", "MSFT"],
    "acquisition": ["GOOG"]
  },
  "stock_data": {
    "AAPL": {
      "current_price": 150.25,
      "company_name": "Apple Inc.",
      "technical_indicators": {...}
    }
  }
}
```

## Logging

Logs are written to:
- Console: Real-time event logging
- File: `logs/app.log`

Log level configured in `.env`: `LOG_LEVEL=INFO`

## Development

### Adding New Features

1. **New Data Source**: Extend `NewsFetcher` class
2. **New Event Type**: Add keywords to `Config.EVENT_KEYWORDS`
3. **New Technical Indicator**: Add method to `StockDataFetcher`

### Testing

```bash
python main.py --test  # Test mode (optional, to be implemented)
```

## Next Steps

1. **Phase 2**: Implement sentiment analysis with transformers and community data
2. **Phase 3**: Build ML models for prediction
3. **Phase 4**: Set up real-time pipeline with APScheduler
4. **Phase 5**: Develop interactive web dashboard

## License

MIT

## Support

For issues or questions, check logs in `logs/app.log`

---

**Last Updated**: 2026-04-30
**Current Phase**: 1 (Data Collection & Event Detection)
