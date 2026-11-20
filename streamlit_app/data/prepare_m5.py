"""Convert the REAL Kaggle M5 (Walmart) files into the two CSVs the app reads.

1. Download from https://www.kaggle.com/c/m5-forecasting-accuracy/data (free Kaggle account) and put these in data/raw/:
       calendar.csv   sell_prices.csv   sales_train_evaluation.csv   (sales_train_validation.csv also works)
2. Run from the repo root:   python data/prepare_m5.py            (optional: --items 200 --raw path/to/folder)
3. It overwrites data/weekly_item_store.csv and data/daily_store_category.csv. Then update REFRESHED in pages/dashboard.py.

Why sample items? The full file is ~30k item-store series x 1,941 days (59M rows). A stratified random sample of items
(same share from every department) keeps the app fast and the CSVs small. The daily table is built from the same sample.
"""


import argparse
from pathlib import Path
import numpy as np, pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("--items", type=int, default=200, help="number of items to sample (of ~3,049)")
ap.add_argument("--raw", default=None, help="folder with the Kaggle files (default: data/raw)")
args = ap.parse_args()
HERE = Path(__file__).parent
RAW = Path(args.raw) if args.raw else HERE / "raw"

#parsing by date
cal = pd.read_csv(RAW / "calendar.csv", parse_dates=["date"])
#weekly price per store by item
prices = pd.read_csv(RAW / "sell_prices.csv")
#wide, one col per day
sales_file = next(f for f in ["sales_train_evaluation.csv", "sales_train_validation.csv"] if (RAW / f).exists())
sales = pd.read_csv(RAW / sales_file)

#same fraction of items so each department gets represented
items = sales[["item_id", "dept_id"]].drop_duplicates()
frac = min(1.0, args.items / len(items))
keep = items.groupby("dept_id").sample(frac=frac, random_state=42).item_id
sales = sales[sales.item_id.isin(keep)]

# one row per item per store per day, this is the long formatting for the data
id_cols = ["item_id", "dept_id", "cat_id", "store_id", "state_id"]
day_cols = [c for c in sales.columns if c.startswith("d_")]
long = sales.melt(id_vars=id_cols, value_vars=day_cols, var_name="d", value_name="units")
long = long.merge(cal[["d", "date", "wm_yr_wk", "snap_CA", "snap_TX", "snap_WI"]], on="d")

#only keep the same 7 day weeks, for simplicity I just cut the ones that were not 7 day weeks
days_per_week = cal[cal.d.isin(day_cols)].groupby("wm_yr_wk").size()
long = long[long.wm_yr_wk.isin(days_per_week[days_per_week == 7].index)]

# Snap flag simple 1 or 0. (snap or not)
long["snap"] = np.select([long.state_id == "CA", long.state_id == "TX", long.state_id == "WI"],
                         [long.snap_CA, long.snap_TX, long.snap_WI], 0)

# Attaching the weekly price the weekly price
long = long.merge(prices, on=["store_id", "item_id", "wm_yr_wk"], how="inner")
#price by unit
long["revenue"] = long.units * long.sell_price

#daily store / category / day
daily = (long.groupby(["date", "state_id", "store_id", "cat_id"], as_index=False)
         .agg(units=("units", "sum"), revenue=("revenue", "sum"), snap=("snap", "max")))
daily["revenue"] = daily.revenue.round(2)

# Weekly table, price is constant over week so we take first number of the week and keep it
# first calendar day of each M5 week
week_start = cal.groupby("wm_yr_wk").date.min().rename("week_start")
#agg units and merge
weekly = (long.groupby(id_cols + ["wm_yr_wk"], as_index=False)
          .agg(units=("units", "sum"), sell_price=("sell_price", "first"))
          .merge(week_start, on="wm_yr_wk"))
weekly = weekly[id_cols + ["week_start", "units", "sell_price"]].sort_values(["item_id", "store_id", "week_start"])

#saving csv with alterations on the set needed for visualizations
weekly.to_csv(HERE / "weekly_item_store.csv", index=False)
daily.to_csv(HERE / "daily_store_category.csv", index=False)
print(f"{sales.item_id.nunique()} items | weekly rows: {len(weekly):,} | daily rows: {len(daily):,}")
