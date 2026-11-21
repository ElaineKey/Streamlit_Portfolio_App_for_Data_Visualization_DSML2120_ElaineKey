# Retail Sales Explorer

Multipage Streamlit app: `app.py` is the home page and every file in `pages/` appears in the sidebar automatically.

```
app.py   pages/{bio,charts,dashboard,future_work}.py   data/   assets/   requirements.txt
```

Run: `pip install -r requirements.txt` then `streamlit run app.py` (from the repo root).

- **Data:** real M5 (Walmart) data, a stratified sample of 200 of the 3,049 items (all 10 stores, 2011-01-29 to 2016-05-21, complete weeks only). Built by `data/prepare_m5.py` from the competition files (`calendar.csv`, `sell_prices.csv`, `sales_train_evaluation.csv`). To rebuild or change the sample size: put the three files in `data/raw/` (download from Kaggle, or from a GitHub mirror) and run `python data/prepare_m5.py --items 200`. Update `REFRESHED` in `pages/dashboard.py` afterwards.
- **Attribution:** M5 Forecasting - Accuracy, Makridakis Open Forecasting Center (University of Nicosia) with Walmart data: https://www.kaggle.com/c/m5-forecasting-accuracy
- **Year-over-year:** only complete years are compared, so the growth chart covers 2012-2015.
- **Before submitting:** edit your name and links (top of each page), the bio text, `assets/profile.svg` and its alt text, and the Lab 4.3 reflection.
- **Revenue** is computed as `units * sell_price`. SNAP comparisons are within each state. Store comparisons use an index against state peers (1.00 = peer average).
