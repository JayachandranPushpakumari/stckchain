# Backtest UI Implementation Guide

## Overview
A new **Backtest Results** tab has been added to the StockChain frontend to display strategy performance metrics.

## Features

### 1. **New Tab: Backtest Results**
- Located alongside "Swing Screener" and "Breakouts" tabs
- Displays top-performing strategies based on backtest analysis

### 2. **Key Metrics Displayed**
Each strategy card shows:
- **Symbol**: Stock ticker
- **CAGR**: Compound Annual Growth Rate (%)
- **Win Rate**: Percentage of winning trades (%)
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Return**: Mean return per trade (%)
- **Max Drawdown**: Maximum peak-to-trough decline (%)
- **Total Trades**: Number of trades executed

### 3. **Color-Coded Metrics**
Metrics are color-coded for quick assessment:

**Win Rate:**
- 🟢 Excellent (≥60%): Green
- 🔵 Good (≥50%): Blue
- 🔴 Poor (<50%): Red

**Profit Factor:**
- 🟢 Excellent (≥2.0): Green
- 🔵 Good (≥1.5): Blue
- 🔴 Poor (<1.5): Red

**CAGR:**
- 🟢 Excellent (≥20%): Green
- 🔵 Good (≥10%): Blue
- 🔴 Poor (<10%): Red

**Max Drawdown:**
- 🟢 Excellent (≥-10%): Green
- 🔵 Good (≥-20%): Blue
- 🔴 Poor (<-20%): Red

### 4. **Run Backtest Button**
- Triggers a new backtest analysis on fundamentally strong stocks (Score ≥ 60)
- Shows loading state while running
- Automatically refreshes results when complete

## Backend Integration

### API Endpoints Used:
1. **GET /backtest/top-strategies** - Fetches top 20 strategies (Win Rate > 55%, Profit Factor > 1.5)
2. **GET /backtest/results** - Fetches all backtest results
3. **GET /backtest/breakout** - Runs a new backtest analysis

### Strategy Logic:
- Backtests the **breakout strategy** on stocks with fundamental scores ≥ 60
- Filters stocks with at least 250 days of price data
- Calculates comprehensive metrics using the `calculate_metrics` function

## Files Modified

### Frontend:
1. **swing.service.ts**
   - Added `BacktestResult` interface
   - Added methods: `getBacktestResults()`, `getTopStrategies()`, `runBacktest()`

2. **app.component.ts**
   - Added backtest state management
   - Added methods: `loadBacktestData()`, `runBacktestAnalysis()`, `getMetricClass()`
   - Updated `ScreenerTab` type to include 'backtest'

3. **app.component.html**
   - Added "Backtest Results" tab button
   - Added backtest section with strategy cards
   - Integrated metric display with color coding

4. **app.component.css**
   - Added styles for backtest section, cards, and metrics
   - Added color classes: `.metric-excellent`, `.metric-good`, `.metric-poor`

### Backend:
- **fundamentals.py** - Fixed duplicate key violation by deduplicating symbols before DB insert

## Usage

1. **Start the backend server:**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   ng serve
   ```

3. **Navigate to the Backtest tab:**
   - Click on "Backtest Results" tab
   - Click "Run Backtest" to analyze strategies
   - View top-performing strategies with color-coded metrics

## Design Highlights

- **Blue theme** for backtest section (distinct from green swing and breakout sections)
- **Grid layout** with responsive cards (min 320px width)
- **2-column metric grid** within each card for compact display
- **Gradient backgrounds** and subtle shadows for visual depth
- **Hover effects** for interactive feedback

## Future Enhancements

Potential improvements:
- Add filtering by metric thresholds
- Add sorting options (by CAGR, Win Rate, etc.)
- Add detailed trade history view per symbol
- Add equity curve visualization
- Add comparison between multiple strategies
- Export results to CSV/Excel
