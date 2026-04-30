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

### Phase 2: Sentiment Analysis & Feature Engineering ✅
- NLP-based sentiment analysis using VADER and FinBERT transformers
- Community sentiment from Reddit (via Pushshift API)
- Retail sentiment from StockTwits API
- Engagement metrics and momentum indicators
- Comprehensive feature engineering for ML models
- **Status**: Complete

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

### Running Phase 2

```bash
python phase2_main.py [phase1_results_file.json]
```

Or automatically use the latest Phase 1 results:
```bash
python phase2_main.py
```

This will:
1. Load Phase 1 event detection results
2. Analyze news sentiment (VADER + FinBERT)
3. Fetch Reddit discussion data and sentiment
4. Fetch StockTwits community sentiment
5. Calculate technical indicators
6. Create ML-ready feature vectors
7. Save results to `phase2_results_*.json` and `.csv`

**Output includes:**
- Sentiment scores (news, Reddit, StockTwits)
- Engagement metrics (posts, comments, likes)
- Technical indicators (RSI, MACD, Bollinger Bands)
- Combined sentiment score (weighted average)
- Momentum score (multi-factor indicator)

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

## Sentiment Analysis

### VADER (Valence Aware Dictionary and sEntiment Reasoner)
- Fast rule-based sentiment analysis
- Good for social media and informal text
- Returns scores: -1 (negative) to +1 (positive)

### FinBERT (Financial BERT)
- Transformer-based deep learning model
- Trained specifically on financial text
- More accurate for complex financial news
- Used when available, falls back to VADER

### Combined Score
- Weighted average: 40% VADER + 60% FinBERT
- Provides robust sentiment indicator

## Community Sentiment Sources

### Reddit (via Pushshift API)
- Subreddits: stocks, investing, wallstreetbets, stockmarket, etc.
- Metrics: post count, engagement, average scores
- Free API, no authentication needed

### StockTwits
- Real-time retail investor sentiment
- Bullish/bearish classification
- User influence based on follower count
- Engagement metrics (likes, replies)

## Feature Engineering

Created features for ML models:

### Event Features
- Presence of earnings, acquisition, contract, product launch, regulatory approval, etc.
- Recency of most recent event

### Sentiment Features
- News sentiment score and distribution
- Reddit engagement density
- StockTwits bullish/bearish ratios
- Combined weighted sentiment

### Technical Features
- RSI (overbought/oversold indicator)
- MACD (trend indicator)
- Bollinger Bands position
- Volume ratio vs. average
- SMA 20/50 crossover signals

### Derived Features
- Combined sentiment score (weighted multi-source)
- Momentum score (event recency + RSI + sentiment + volume)

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

1. ✅ **Phase 1**: Data Collection & Event Detection - COMPLETE
2. ✅ **Phase 2**: Sentiment Analysis & Feature Engineering - COMPLETE
3. **Phase 3**: Machine Learning Model Training
   - Binary classification: predict price direction (up/down)
   - Regression: predict price range (±%)
   - Model evaluation and backtesting
   - Feature importance analysis
4. **Phase 4**: Real-time Pipeline & Automation
   - APScheduler for hourly updates
   - FastAPI endpoints for manual triggers
   - Database storage for predictions
   - Alert system for significant predictions
5. **Phase 5**: Web Dashboard
   - Interactive visualization
   - Real-time prediction updates
   - Historical performance tracking
   - Sentiment heatmaps

## License

MIT

## Support

For issues or questions, check logs in `logs/app.log`

---

**Last Updated**: 2026-04-30
**Current Phase**: 1 (Data Collection & Event Detection)
