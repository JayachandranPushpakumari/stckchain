import pandas as pd

df = pd.read_excel('fundamentals.xlsx')
df.columns = df.columns.str.strip().str.lower()
df.rename(columns={'stockname': 'symbol'}, inplace=True)

print(f'Total rows: {len(df)}')
print(f'Unique symbols: {df["symbol"].nunique()}')

dupes = df[df.duplicated(subset=['symbol'], keep=False)]
print(f'Duplicate symbols: {len(dupes)}')

if len(dupes) > 0:
    print('\nDuplicate symbols:')
    print(dupes[['symbol']].sort_values('symbol'))
