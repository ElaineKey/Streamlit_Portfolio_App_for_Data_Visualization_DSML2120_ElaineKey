import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

#you can set the color as any palette you want!
#this is a built feature in streamlit

#COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7", "#000000"]
COLORS = ["#6B8E5A", "#C8782A", "#8C5A3C", "#3F6C7A", "#D4A94A", "#A8483A", "#4A4036"]

SOURCE = "https://www.kaggle.com/c/m5-forecasting-accuracy"
#REFRESHED = "2026-11-17"


#a bunch of these are built for a broken tab at the bottom of this page, this is still a work in progress
#at some point this will get updated with the information to have that final tab work

@st.cache_data
def load():

    #Claude root read fix
    w = pd.read_csv(ROOT / "data/weekly_item_store.csv", parse_dates=["week_start"])
    w = w.sort_values(["item_id", "store_id", "week_start"])
    w["year"] = w.week_start.dt.year
    w["revenue"] = w.units * w.sell_price
    g = w.groupby(["item_id", "store_id"])
    w["price_change"] = g.sell_price.pct_change(fill_method=None)
    w["changed"] = w.price_change.abs() > 0.005
    prev4 = g.units.transform(lambda s: s.shift().rolling(4).mean())
    w["units_change"] = (w.units / prev4 - 1) * 100
    w["price_move"] = np.select([w.price_change < -0.005, w.price_change > 0.005], ["Price cut", "Price rise"], "No change")
    w.loc[w.price_change.isna(), "price_move"] = None

    #Claude root read  fix
    d = pd.read_csv(ROOT / "data/daily_store_category.csv", parse_dates=["date"])
    d["year"] = d.date.dt.year
    return w.replace([np.inf, -np.inf], np.nan), d


w, d = load()

st.title("Dashboard")
st.caption("M5 Competition Walmart Retail Sales Explorer · Elaine Key")

# filters for everything
st.sidebar.header("Filters")
states = st.sidebar.multiselect("State", sorted(w.state_id.unique()), default=sorted(w.state_id.unique()))
cats = st.sidebar.multiselect("Category", sorted(w.cat_id.unique()), default=sorted(w.cat_id.unique()))
yrs = st.sidebar.slider("Years", int(w.year.min()), int(w.year.max()), (int(w.year.min()), int(w.year.max())))

#this ignores the year slider, which is needed for year over year growth
base = w[w.state_id.isin(states) & w.cat_id.isin(cats)]
f = base[base.year.between(*yrs)]
fd = d[d.state_id.isin(states) & d.cat_id.isin(cats) & d.year.between(*yrs)]
if f.empty:
    st.warning("No data, Select at least one state and category.")
    st.stop()

# KPI stuff
k = st.columns(4)

#total rev
k[0].metric("Revenue (USD)", f"${f.revenue.sum():,.0f}")
#total units sold
k[1].metric("Units sold", f"{f.units.sum():,.0f}")
#num unique products
k[2].metric("Items", f"{f.item_id.nunique()}")
#total num of price changes
k[3].metric("Price changes", f"{int(f.changed.sum()):,}")

tabs = st.tabs(["1 Price changes", "2 Stores vs peers", "3 SNAP days", "4 Departments"])
insights = []

# tab for price changes
with tabs[0]:
    top = (f.groupby(["item_id", "cat_id"]).changed.mean().mul(52).rename("changes_per_year").reset_index()
           .nlargest(15, "changes_per_year").sort_values("changes_per_year"))
    resp = f.dropna(subset=["price_move", "units_change"]).groupby("price_move").units_change.median().reset_index()
    a, b = st.columns(2)

    #chart on the left, horizontal bars of top 15 items
    a.plotly_chart(px.bar(top, x="changes_per_year", y="item_id", color="cat_id", orientation="h", color_discrete_sequence=COLORS,
                          title="Top 15 items by price changes per store per year",
                          labels={"changes_per_year": "Changes per store per year", "item_id": "Item", "cat_id": "Category"}),
                   width="stretch")

    #right chart median unit change for price cut, no change, price increase
    b.plotly_chart(px.bar(resp, x="price_move", y="units_change", text_auto=".0f", color_discrete_sequence=COLORS,
                          category_orders={"price_move": ["Price cut", "No change", "Price rise"]},
                          title="Median change in units vs previous month average",
                          labels={"price_move": "Price movement that week", "units_change": "Median change in units (%)"}),
                   width="stretch")

#turn resp into a lookup for price move to median units changed
    r = resp.set_index("price_move").units_change
    insights.append(f"`{top.item_id.iloc[-1]}` changes price most often ({top.changes_per_year.iloc[-1]:.1f} times per store per year).")

    if {"Price cut", "Price rise"} <= set(r.index):
        insights.append(f"Median units are {r['Price cut']:+.0f}% vs the prior 4 weeks in price-cut weeks and {r['Price rise']:+.0f}% in price-rise weeks.")

#tab for store comparison
with tabs[1]:

    #total revenue per store within each cateogry
    r = f.groupby(["state_id", "store_id", "cat_id"]).revenue.sum().reset_index()

    #group by state and category so each store is compared to its state
    grp = r.groupby(["state_id", "cat_id"]).revenue
    n = grp.transform("count")

    #need at least one store as a peer to run the comparison
    r = r[n > 1].copy()

    #average revenue of the other stores, (group total - this store)
    r["peer_avg"] = (grp.transform("sum") - r.revenue) / (n - 1)
    r["index"] = r.revenue / r.peer_avg


    if r.empty:
        st.info("Select a state with at least two stores to compare.")

    else:

        #one row per store, total rev total peer rev and mean cat index
        s = r.groupby(["state_id", "store_id"]).agg(rev=("revenue", "sum"), peer=("peer_avg", "sum"), adjusted=("index", "mean")).reset_index()
        s["raw"] = s.rev / s.peer

        long = s.melt(id_vars=["state_id", "store_id"], value_vars=["raw", "adjusted"], var_name="measure", value_name="index")
        long["measure"] = long.measure.map({"raw": "Raw (total revenue)", "adjusted": "Category-mix adjusted"})
        a, b = st.columns(2)

#left is grouped bars of raw vs adjusted index for each store
        fig = px.bar(long, x="store_id", y="index", color="measure", barmode="group", color_discrete_sequence=COLORS,
                     title="Store revenue index vs state peers", labels={"store_id": "Store", "index": "Index (peers = 1.00)"})
        fig.add_hline(y=1, line_dash="dash")
        a.plotly_chart(fig, width="stretch")

#right heatmap of index for every store category combination
        b.plotly_chart(px.imshow(r.pivot(index="store_id", columns="cat_id", values="index"), text_auto=".2f",
                                 color_continuous_scale="Cividis", aspect="auto", title="Category index by store, peers = 1.00",
                                 labels={"x": "Category", "y": "Store", "color": "Index"}), width="stretch")

        st.caption("1.00 = average of the other stores in the same state. "
                   "a store is not credited only for having more sales in the biggest category.")

#best and worst stores by adjusted index
        best, worst = s.loc[s.adjusted.idxmax()], s.loc[s.adjusted.idxmin()]
        insights.append(f"After adjusting for category mix, {best.store_id} leads, ({best.adjusted:.2f}) and {worst.store_id} trails ({worst.adjusted:.2f}).")

#tab for SNAP benefit stuff
with tabs[2]:
    s = fd.groupby(["state_id", "cat_id", "snap"]).revenue.mean().unstack()

    #simple percentage lift on snap days vs non snap days.
    #the math for this is just the index times 100, used pretty frequently in terms of lift as a metric
    lift = ((s[1] / s[0] - 1) * 100).rename("lift").reset_index()

#grouped bar chart for one group a category, one bar per state.
    st.plotly_chart(px.bar(lift, x="cat_id", y="lift", color="state_id", barmode="group", text_auto=".1f",
                           color_discrete_sequence=COLORS, title="SNAP-day revenue lift vs non-SNAP days, within each state",
                           labels={"cat_id": "Category", "lift": "Lift in daily revenue (%)", "state_id": "State"}),
                    width="stretch")

    st.caption("Average daily revenue per store on SNAP days compared with non-SNAP days grouped by state.")

#these are broken I wanted to try to be impressive
  #  c = lift.groupby("cat_id").lift.mean()
  #  insights.append("Average SNAP-day lift: " + ", ".join(f"{k.title()} {v:.1f}%" for k, v in c.items()) + ".")

# tab for departments
#with tabs[3]:
 #   y = base.groupby(["dept_id", "year"]).revenue.sum().reset_index()
  #  weeks = base.groupby("year").week_start.nunique()
  #  y = y[y.year.isin(weeks[weeks >= 50].index)]                               # full years only
  #  y["yoy"] = y.groupby("dept_id").revenue.pct_change(fill_method=None) * 100
  #  a, b = st.columns(2)
  #  fig = px.line(y, x="year", y="revenue", color="dept_id", markers=True, color_discrete_sequence=COLORS,
  #                title="Annual revenue by department", labels={"year": "Year", "revenue": "Revenue (USD)", "dept_id": "Department"})
  #  a.plotly_chart(fig.update_xaxes(dtick=1), width="stretch")
  #  last = y.dropna(subset=["yoy"])
  #  last = last[last.year == last.year.max()] if not last.empty else last
  #  if not last.empty:
  #      last = last.assign(trend=np.where(last.yoy >= 0, "Growing", "Shrinking"))
  #      b.plotly_chart(px.bar(last.sort_values("yoy"), x="yoy", y="dept_id", orientation="h", color="trend", text_auto=".1f",
  #                            color_discrete_map={"Growing": "#0072B2", "Shrinking": "#D55E00"},
  #                            title=f"Year-over-year revenue growth, {int(last.year.iloc[0])}",
  #                            labels={"yoy": "Change vs prior year (%)", "dept_id": "Department", "trend": ""}), width="stretch")
  #      insights.append(f"Fastest-growing department: {last.loc[last.yoy.idxmax(), 'dept_id']} ({last.yoy.max():+.1f}%); "
  #                      f"fastest-shrinking: {last.loc[last.yoy.idxmin(), 'dept_id']} ({last.yoy.min():+.1f}%).")
  #  else:
  #      b.info("Year-over-year growth needs two full years of data.")
  #  rev = f.groupby("item_id").revenue.sum().sort_values(ascending=False)
  #  share = rev.iloc[:int(np.ceil(len(rev) * .1))].sum() / rev.sum()
  #  st.metric("Share of revenue from the top 10% of items", f"{share:.0%}")
  #  st.caption("Growth panels ignore the year slider so growth can be computed. Revenue = units × weekly sell price.")
  #  insights.append(f"The top 10% of items generate {share:.0%} of revenue in the current selection.")

#narrative stuff
st.divider()
st.subheader("What the data say")
st.markdown("\n".join(f"- {i}" for i in insights))

st.markdown("- **Limitations:** results are descriptive, not causal. Price changes, SNAP days and sales can all move with season and paydays, "
            "and the data cover a sample.")

st.info("**Ethics & limitations.** These are aggregated store sales with no individual shoppers. SNAP-day comparisons describe "
        "store-level patterns only and say nothing about people who receive benefits. The data are a 200-item sample of the M5 (Walmart) competition data and may not generalise to other retailers.")

st.markdown(f"[![Data source](https://img.shields.io/badge/data-M5%20Walmart%20sample-0072B2)]({SOURCE})  \n"
            f"<small>Last refreshed: {REFRESHED} · {len(w):,} weekly rows, {len(d):,} daily rows</small>", unsafe_allow_html=True)
