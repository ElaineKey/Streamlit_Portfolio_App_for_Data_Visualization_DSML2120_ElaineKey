# Retail Sales Explorer

`app.py` is the home page and every file in `pages/` appears in the sidebar automatically.

```
app.py   pages/{bio,charts,dashboard,future_work}.py   data/   assets/   requirements.txt
```

Run: `pip install -r requirements.txt` then `streamlit run app.py` (from the repo root).

- **Data:** real M5 (Walmart) data, a stratified sample of 200 of the 3,049 items (all 10 stores, complete weeks only). Built by `data/prepare_m5.py` from the competition files (`calendar.csv`, `sell_prices.csv`, `sales_train_evaluation.csv`). Update `REFRESHED` in `pages/dashboard.py` afterwards.
- **Attribution:** M5 Forecasting - Accuracy, Makridakis Open Forecasting Center (University of Nicosia) with Walmart data: https://www.kaggle.com/c/m5-forecasting-accuracy
- **Year-over-year:** only complete years are compared, so the growth chart covers 2012-2015.
- **Revenue** is computed as `units * sell_price`. SNAP comparisons are within each state. Store comparisons use an index against state peers.
- **AI Acknowledgement** Ai content appears throughout this project in multiple bug fixes, and as an information aggregation tool.
