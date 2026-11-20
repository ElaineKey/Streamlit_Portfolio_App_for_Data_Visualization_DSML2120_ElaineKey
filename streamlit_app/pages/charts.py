import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


#color palette stuff
COLORS = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7"]


@st.cache_data
def load():
    w = pd.read_csv("data/weekly_item_store.csv", parse_dates=["week_start"])
    w = w.sort_values(["item_id", "store_id", "week_start"])

#target is units, so computing revenue
    w["revenue"] = w.units * w.sell_price
    g = w.groupby(["item_id", "store_id"])
    w["price_change"] = g.sell_price.pct_change(fill_method=None)
    w["changed"] = w.price_change.abs() > 0.005

#items own average of the previous four weeks
    prev4 = g.units.transform(lambda s: s.shift().rolling(4).mean())

    w["units_change"] = (w.units / prev4 - 1) * 100
    w["price_move"] = np.select([w.price_change < -0.005, w.price_change > 0.005], ["Price cut", "Price rise"], "No change")
    w.loc[w.price_change.isna(), "price_move"] = None
    d = pd.read_csv("data/daily_store_category.csv", parse_dates=["date"])
    return w.replace([np.inf, -np.inf], np.nan), d


w, d = load()
st.title("EDA Gallery")
st.caption("Retail Sales Explorer · Your Name · [LinkedIn](https://www.linkedin.com/in/your-handle) · four interactive charts: hover for details")

# bar chart for items changing their price

st.header("Item Price Change by Frequency")
st.markdown("Item Price Change by Frequency")

top = (w.groupby(["item_id", "cat_id"]).changed.mean().mul(52).rename("changes_per_year").reset_index()
       .nlargest(15, "changes_per_year").sort_values("changes_per_year"))

fig = px.bar(top, x="changes_per_year", y="item_id", color="cat_id", orientation="h", color_discrete_sequence=COLORS,
             title="Top 15 items by price changes per store per year",
             labels={"changes_per_year": "Price changes per store per year", "item_id": "Item", "cat_id": "Category"})

st.plotly_chart(fig, width="stretch")

with st.expander("How to read this chart", expanded=True):
    st.markdown("- Each bar is one item; a longer bar means its price changes more often.\n"
                "- The x-axis is price changes per store per year (a move of more than 0.5% week to week).\n"
                "- Colour shows category. Hover to see exact values.")

all_rates = w.groupby("item_id").changed.mean() * 52
st.markdown(f"- `{top.item_id.iloc[-1]}` changes price about {top.changes_per_year.iloc[-1]:.1f} times per store per year, the most of any item.\n"

            f"- The median item changes price {all_rates.median():.1f} times per year.\n"
            f"- {(all_rates == 0).sum()} of {len(all_rates)} items never changed price.\n"
            f"- The most common category in the top 15 is {top.cat_id.mode()[0].title()}.")

# BAR CHART How do weekly units differ when prices fall rise or stay the same?
st.header("2. Weekly units by price as they rise, fall, or stay the same")

x = w.dropna(subset=["price_move", "units_change"])
x = x.sample(min(30000, len(x)), random_state=1)

order = ["Price cut", "No change", "Price rise"]
fig = px.box(x, x="price_move", y="units_change", color="price_move", points=False, category_orders={"price_move": order},
             color_discrete_sequence=[COLORS[0], COLORS[4], COLORS[3]], title="Change in weekly units vs previous 4-week average",
             labels={"price_move": "Price movement that week", "units_change": "Change in units (%)"})

fig.update_yaxes(range=[-100, 200]).update_layout(showlegend=False)
st.plotly_chart(fig, width="stretch")

st.caption(f"Based on a random sample of {len(x):,} item-store weeks; y-axis limited to -100% to +200% for readability.")

with st.expander("How to read this chart", expanded=True):
    st.markdown("- The line in each box is the median; the box covers the middle 50% of weeks.\n"
                "- Left to right: weeks with a price cut, no change, and a price rise.\n"
                "- The y-axis is the % change in units compared with the item's average over the previous four weeks.")

med = x.groupby("price_move").units_change.median()
q = x[x.price_move == "No change"].units_change.quantile([.25, .75])

st.markdown(f"- Median units change is {med['Price cut']:+.0f}% in price-cut weeks, {med['No change']:+.0f}% in no-change weeks and {med['Price rise']:+.0f}% in price-rise weeks.\n"
            f"- Even with no price change, the middle 50% of weeks range from {q.iloc[0]:+.0f}% to {q.iloc[1]:+.0f}%, which is normal week-to-week variation.\n"
            f"- The sample holds {(x.price_move == 'Price cut').sum():,} cut weeks and {(x.price_move == 'Price rise').sum():,} rise weeks.")

#HEATMAP do snap days lift sales more in some catgories and states
st.header("3. SNAP Benefit days and sales affect.")

s = d.groupby(["state_id", "cat_id", "snap"]).revenue.mean().unstack()
lift = ((s[1] / s[0] - 1) * 100).unstack()                                   # rows = state, columns = category
fig = px.imshow(lift, text_auto=".1f", color_continuous_scale="Cividis", aspect="auto",
                title="Daily revenue on SNAP days vs non-SNAP days (% difference)",
                labels={"x": "Category", "y": "State", "color": "% difference"})

st.plotly_chart(fig, width="stretch")

with st.expander("How to read this chart", expanded=True):
    st.markdown("- Rows are states and columns are product categories.\n"
                "- Each cell is the % difference in average daily store revenue on SNAP days vs non-SNAP days in the same state.\n"
                "- Lighter cells are higher, darker cells are lower, and the number is printed in the cell.")

st.markdown(f"- The largest difference is {lift.max().max():.1f}% and the smallest is {lift.min().min():.1f}%.\n"
            f"- Average difference by category: " + ", ".join(f"{c.title()} {v:.1f}%" for c, v in lift.mean().items()) + ".\n"
            "- Each state is compared only with its own non-SNAP days, because states issue benefits on different days.")

#HISTOGRAM how is total revenue spread across items (planning question)
st.header("4. Histogram of revenue spread across items")

rev = w.groupby("item_id").revenue.sum().sort_values(ascending=False)
fig = px.histogram(rev.reset_index(), x="revenue", nbins=30, color_discrete_sequence=COLORS,
                   title="Distribution of total item revenue",
                   labels={"revenue": "Total revenue per item, all stores and years (USD)"})

fig.update_yaxes(title_text="Number of items")
st.plotly_chart(fig, width="stretch")

with st.expander("How to read this chart", expanded=True):
    st.markdown("- Each bar counts the items whose total revenue falls in that range.\n"
                "- The x-axis is dollars of revenue (units × sell price); the y-axis is the number of items.\n"
                "- Tall bars on the left with a long right tail mean many low earners and a few big ones.")

top10 = rev.iloc[:int(np.ceil(len(rev) * .1))].sum() / rev.sum()
st.markdown(f"- Median item revenue is ${rev.median():,.0f} while the mean is ${rev.mean():,.0f}.\n"
            f"- The top item earns ${rev.iloc[0]:,.0f}, about {rev.iloc[0] / rev.median():.0f} times the median.\n"
            f"- The top 10% of items earn {top10:.0%} of total revenue.")

st.divider()
st.info("**Ethics & limitations.** These are aggregated store sales with no individual shoppers. SNAP-day comparisons "
        "describe store-level patterns only and say nothing about people who receive benefits. The data are a sample "
        "from one retailer and may not generalise; patterns are descriptive, not causal.")
