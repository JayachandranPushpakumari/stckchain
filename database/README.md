# Database Migrations

## Fundamental Scores Table

### Setup

1. Run the migration to create the `fundamental_scores` table:
```bash
python database/run_migration.py
```

### Table Schema

The `fundamental_scores` table stores the results of fundamental screening with the following structure:

- **symbol**: Stock symbol
- **latest_close**: Latest closing price
- **total_score**: Total fundamental score (0-100)
- **screened_at**: Timestamp when screening was performed

For each screening criterion, the table stores:
- **actual_value**: The actual metric value
- **threshold**: The threshold used for comparison
- **score**: Points awarded (0 or 10)

Criteria tracked:
1. ROE (Return on Equity)
2. ROCE (Return on Capital Employed)
3. ROE 3 Years Average
4. ROCE 3 Year Consistency
5. Debt to Equity Ratio
6. Sales Growth 3 Years
7. Profit Growth 3 Years
8. Stock Price CAGR 3 Years
9. PE vs EPS 3 Years Average
10. Pledged Promoter Holding

### Usage

The `calculate_fundamental_score()` function now automatically saves results to the database by default:

```python
from services.fundamentals import calculate_fundamental_score

# Save to database (default behavior)
result = calculate_fundamental_score()

# Skip database save
result = calculate_fundamental_score(save_to_db=False)
```

### Querying Saved Data

```sql
-- Get latest screening results for all stocks
SELECT DISTINCT ON (symbol) *
FROM fundamental_scores
ORDER BY symbol, screened_at DESC;

-- Get top scoring stocks from latest screening
SELECT symbol, total_score, latest_close, screened_at
FROM fundamental_scores
WHERE screened_at = (SELECT MAX(screened_at) FROM fundamental_scores)
ORDER BY total_score DESC;

-- Track score changes over time for a specific stock
SELECT symbol, total_score, screened_at
FROM fundamental_scores
WHERE symbol = 'RELIANCE'
ORDER BY screened_at DESC;
```
