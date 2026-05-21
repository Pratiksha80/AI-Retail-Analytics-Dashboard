from __future__ import annotations

import calendar
from io import BytesIO

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="AI Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


NEON = {
    "cyan": "#35f2ff",
    "magenta": "#c77dff",
    "lime": "#00ff9a",
    "amber": "#ffb703",
    "bg0": "#050816",
    "bg1": "#070b1f",
    "bg2": "#091a3a",
    "card": "rgba(14, 24, 56, 0.72)",
    "border": "rgba(53, 242, 255, 0.22)",
    "grid": "rgba(110, 231, 255, 0.10)",
    "text": "rgba(245, 248, 255, 0.92)",
    "muted": "rgba(245, 248, 255, 0.72)",
}


def _inject_css() -> None:
    st.markdown(
        f"""
<style>
/* ---- App background (dark blue gradient) ---- */
[data-testid="stAppViewContainer"] {{
  background: radial-gradient(1200px 600px at 15% 10%, rgba(53,242,255,0.14), transparent 60%),
              radial-gradient(900px 500px at 85% 15%, rgba(199,125,255,0.12), transparent 55%),
              radial-gradient(1000px 600px at 50% 85%, rgba(0,255,154,0.08), transparent 60%),
              linear-gradient(135deg, {NEON["bg0"]} 0%, {NEON["bg1"]} 40%, {NEON["bg2"]} 100%);
  color: {NEON["text"]};
}}

/* ---- Sidebar styling ---- */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, rgba(7,11,31,0.98) 0%, rgba(5,8,22,0.98) 100%);
  border-right: 1px solid rgba(53,242,255,0.18);
}}

/* ---- Remove extra top padding ---- */
.block-container {{
  padding-top: 1.2rem;
  padding-bottom: 2rem;
}}

/* ---- Hide Streamlit default menu/footer ---- */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* ---- Typography ---- */
h1, h2, h3, h4, h5 {{
  color: {NEON["text"]};
  letter-spacing: 0.2px;
}}

/* ---- KPI cards ---- */
.kpi-grid {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}}
@media (max-width: 1100px) {{
  .kpi-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
}}
@media (max-width: 560px) {{
  .kpi-grid {{ grid-template-columns: 1fr; }}
}}
.kpi-card {{
  background: {NEON["card"]};
  border: 1px solid {NEON["border"]};
  border-radius: 16px;
  padding: 16px 16px 14px 16px;
  position: relative;
  overflow: hidden;
  box-shadow:
    0 0 0 1px rgba(53,242,255,0.08),
    0 12px 26px rgba(0,0,0,0.45),
    0 0 30px rgba(53,242,255,0.08);
  transition: transform 120ms ease, box-shadow 120ms ease;
}}
.kpi-card:hover {{
  transform: translateY(-2px);
  box-shadow:
    0 0 0 1px rgba(53,242,255,0.18),
    0 16px 34px rgba(0,0,0,0.55),
    0 0 42px rgba(53,242,255,0.14);
}}
.kpi-glow {{
  position: absolute;
  inset: -60% -30%;
  background: radial-gradient(circle at 30% 20%, rgba(53,242,255,0.22), transparent 45%),
              radial-gradient(circle at 70% 30%, rgba(199,125,255,0.18), transparent 50%),
              radial-gradient(circle at 40% 80%, rgba(0,255,154,0.10), transparent 55%);
  filter: blur(18px);
  pointer-events: none;
}}
.kpi-label {{
  font-size: 0.82rem;
  color: {NEON["muted"]};
  text-transform: uppercase;
  letter-spacing: 1.2px;
}}
.kpi-value {{
  font-size: 1.8rem;
  font-weight: 800;
  line-height: 1.1;
  margin-top: 6px;
}}
.kpi-sub {{
  margin-top: 8px;
  font-size: 0.86rem;
  color: {NEON["muted"]};
}}

/* ---- Section cards (chart containers) ---- */
.panel {{
  background: rgba(8, 14, 38, 0.55);
  border: 1px solid rgba(53,242,255,0.14);
  border-radius: 18px;
  padding: 10px 12px 6px 12px;
  box-shadow: 0 18px 42px rgba(0,0,0,0.45);
}}

/* ---- Title bar (Power BI-like) ---- */
.titlebar {{
  background: linear-gradient(180deg, rgba(8, 12, 28, 0.92), rgba(6, 10, 22, 0.86));
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 16px;
  padding: 14px 18px;
  box-shadow: 0 18px 42px rgba(0,0,0,0.55), 0 0 34px rgba(53,242,255,0.10);
  text-align: center;
}}
.titlebar .title {{
  font-size: 1.9rem;
  font-weight: 900;
  letter-spacing: 0.6px;
}}

/* ---- Filter row ---- */
.filterbar {{
  margin-top: 10px;
  margin-bottom: 8px;
  background: rgba(8, 14, 38, 0.42);
  border: 1px solid rgba(53,242,255,0.12);
  border-radius: 16px;
  padding: 10px 12px;
  box-shadow: 0 14px 32px rgba(0,0,0,0.35);
}}
</style>
        """,
        unsafe_allow_html=True,
    )


def _plotly_theme() -> dict:
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=NEON["text"]),
        margin=dict(l=10, r=10, t=55, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)",
            font=dict(color=NEON["muted"]),
        ),
    )


def style_axes(fig: go.Figure) -> go.Figure:
    fig.update_xaxes(gridcolor=NEON["grid"], zerolinecolor=NEON["grid"])
    fig.update_yaxes(gridcolor=NEON["grid"], zerolinecolor=NEON["grid"])
    return fig


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df


def _first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _month_sort_key(month_name: str) -> int:
    month_name = str(month_name).strip()
    try:
        return list(calendar.month_name).index(month_name)
    except ValueError:
        try:
            return list(calendar.month_abbr).index(month_name)
        except ValueError:
            return 13


def prepare(df_raw: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    """
    Returns a prepared dataframe and a mapping dict with canonical names:
    Region, Category, PaymentMode, Customer, Date, Month, Year, Quantity, UnitPrice, CostPrice, Sales, Profit
    """
    df = df_raw.copy()

    colmap: dict[str, str] = {}

    colmap["Region"] = _first_existing_col(df, ["Region", "region"])
    colmap["Category"] = _first_existing_col(df, ["Category", "category"])
    colmap["PaymentMode"] = _first_existing_col(
        df,
        ["Payment Mode", "PaymentMode", "Payment_Mode", "payment_mode", "Pay Mode", "Mode of Payment"],
    )
    colmap["Customer"] = _first_existing_col(
        df,
        ["Customer", "Customer Name", "CustomerName", "customer_name", "Client", "Buyer"],
    )

    # quantity / prices
    colmap["Quantity"] = _first_existing_col(df, ["Quantity", "Sum of Quantity", "Qty", "Order Quantity"])
    colmap["UnitPrice"] = _first_existing_col(df, ["UnitPrice", "Sum of UnitPrice", "Unit Price", "Price"])
    colmap["CostPrice"] = _first_existing_col(df, ["CostPrice", "Sum of CostPrice", "Cost Price", "Cost"])

    # sales / profit (may already be computed)
    colmap["Sales"] = _first_existing_col(
        df,
        ["Sales_Column", "Sales", "total sales (SUMX)", "Total Sales", "Revenue"],
    )
    colmap["Profit"] = _first_existing_col(df, ["profit", "Profit", "Sum of profit", "Total Profit"])

    # date parts (your dataset contains these)
    colmap["Year"] = _first_existing_col(df, ["Year", "year"])
    colmap["Month"] = _first_existing_col(df, ["Month", "month"])
    colmap["Day"] = _first_existing_col(df, ["Day", "day"])
    colmap["Date"] = _first_existing_col(df, ["Order Date", "OrderDate", "Date", "date"])

    # Create a usable Date column if possible
    if colmap["Date"] is None:
        if colmap["Year"] and colmap["Month"] and colmap["Day"]:
            # Month could be name (January) -> convert to month number
            month_num = df[colmap["Month"]].map(_month_sort_key).astype("Int64")
            df["_MonthNum"] = month_num
            df["Date"] = pd.to_datetime(
                dict(
                    year=df[colmap["Year"]].astype("Int64"),
                    month=df["_MonthNum"].astype("Int64"),
                    day=df[colmap["Day"]].astype("Int64"),
                ),
                errors="coerce",
            )
            colmap["Date"] = "Date"
        else:
            df["Date"] = pd.NaT
            colmap["Date"] = "Date"
    else:
        df["Date"] = pd.to_datetime(df[colmap["Date"]], errors="coerce")
        colmap["Date"] = "Date"

    # Create month label used in filters (YYYY-MMM)
    df["MonthLabel"] = df["Date"].dt.to_period("M").astype(str)
    df["MonthLabel"] = df["MonthLabel"].fillna("Unknown")

    # Ensure numeric columns
    for k in ["Quantity", "UnitPrice", "CostPrice", "Sales", "Profit"]:
        if colmap.get(k) and colmap[k] in df.columns:
            df[colmap[k]] = pd.to_numeric(df[colmap[k]], errors="coerce")

    # If columns do not exist, create:
    # Sales_Column = Quantity * UnitPrice
    if "Sales_Column" not in df.columns:
        if colmap["Quantity"] and colmap["UnitPrice"]:
            df["Sales_Column"] = df[colmap["Quantity"]] * df[colmap["UnitPrice"]]
        else:
            df["Sales_Column"] = pd.NA

    # profit = Sales_Column - (CostPrice * Quantity)
    if "profit" not in df.columns:
        if colmap["CostPrice"] and colmap["Quantity"]:
            df["profit"] = df["Sales_Column"] - (df[colmap["CostPrice"]] * df[colmap["Quantity"]])
        else:
            df["profit"] = pd.NA

    # Canonical preference: use existing Sales/Profit if present, else use computed
    if colmap["Sales"] is None:
        colmap["Sales"] = "Sales_Column"
    if colmap["Profit"] is None:
        colmap["Profit"] = "profit"

    return df, colmap


def money(x: float) -> str:
    if pd.isna(x):
        return "—"
    if abs(x) >= 1_000_000_000:
        return f"${x/1_000_000_000:,.2f}B"
    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"${x/1_000:,.2f}K"
    return f"${x:,.0f}"


def num(x: float) -> str:
    if pd.isna(x):
        return "—"
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:,.2f}M"
    if abs(x) >= 1_000:
        return f"{x/1_000:,.2f}K"
    return f"{x:,.0f}"


_inject_css()

st.markdown(
    """
<div class="titlebar">
  <div class="title">AI Retail Analytics Dashboard</div>
  <div style="margin-top:6px;color:rgba(245,248,255,0.72);">
    Executive BI layout • neon analytics • interactive insights
  </div>
</div>
    """,
    unsafe_allow_html=True,
)


df_raw = load_data("ssales_data.csv")
df, col = prepare(df_raw)

if df.empty:
    st.error("No data found in `ssales_data.csv`.")
    st.stop()


def safe_unique(series: pd.Series) -> list:
    if series is None or series.empty:
        return []
    vals = series.dropna().unique().tolist()
    return sorted(vals)

region_col = col.get("Region")
category_col = col.get("Category")
pay_col = col.get("PaymentMode")
year_col = col.get("Year")
quarter_col = _first_existing_col(df, ["Quarter", "quarter"])

regions = safe_unique(df[region_col]) if region_col else []
cats = safe_unique(df[category_col]) if category_col else []
payments = safe_unique(df[pay_col]) if pay_col else []
years = safe_unique(df[year_col]) if year_col else []
quarters = safe_unique(df[quarter_col]) if quarter_col else []
months = safe_unique(df["MonthLabel"])

# --- Top filter bar (Power BI-like) ---
st.markdown('<div class="filterbar">', unsafe_allow_html=True)
f1, f2, f3, f4, f5 = st.columns([1, 1, 1, 1, 1.2], gap="medium")
with f1:
    region_pick = st.selectbox("Region", options=["All"] + regions, index=0, disabled=not bool(regions))
with f2:
    category_pick = st.selectbox("Category", options=["All"] + cats, index=0, disabled=not bool(cats))
with f3:
    payment_pick = st.selectbox(
        "Payment Mode",
        options=["All"] + payments if payments else ["(Not available)"],
        index=0,
        disabled=not bool(payments),
    )
with f4:
    year_pick = st.selectbox("Year", options=["All"] + years, index=0, disabled=not bool(years))
with f5:
    month_pick = st.selectbox("Month", options=["All"] + months, index=0, disabled=not bool(months))
st.markdown("</div>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Export")
    st.caption("Download the filtered dataset.")


mask = pd.Series(True, index=df.index)
if region_col and region_pick != "All":
    mask &= df[region_col].eq(region_pick)
if category_col and category_pick != "All":
    mask &= df[category_col].eq(category_pick)
if pay_col and payments and payment_pick != "All":
    mask &= df[pay_col].eq(payment_pick)
if year_col and years and year_pick != "All":
    mask &= df[year_col].eq(year_pick)
if month_pick != "All":
    mask &= df["MonthLabel"].eq(month_pick)

fdf = df.loc[mask].copy()

sales_col = col["Sales"]
profit_col = col["Profit"]
qty_col = col.get("Quantity")

total_sales = float(pd.to_numeric(fdf[sales_col], errors="coerce").sum()) if sales_col in fdf else 0.0
total_profit = float(pd.to_numeric(fdf[profit_col], errors="coerce").sum()) if profit_col in fdf else 0.0
avg_sales = float(pd.to_numeric(fdf[sales_col], errors="coerce").mean()) if sales_col in fdf else 0.0
total_qty = float(pd.to_numeric(fdf[qty_col], errors="coerce").sum()) if qty_col and qty_col in fdf else float("nan")

st.markdown(
    f"""
<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-glow"></div>
    <div class="kpi-label">Total Sales</div>
    <div class="kpi-value" style="color:{NEON["cyan"]};">{money(total_sales)}</div>
    <div class="kpi-sub">Across selected filters</div>
  </div>
  <div class="kpi-card"><div class="kpi-glow"></div>
    <div class="kpi-label">Total Profit</div>
    <div class="kpi-value" style="color:{NEON["lime"]};">{money(total_profit)}</div>
    <div class="kpi-sub">Net profit (computed if missing)</div>
  </div>
  <div class="kpi-card"><div class="kpi-glow"></div>
    <div class="kpi-label">Average Sales</div>
    <div class="kpi-value" style="color:{NEON["magenta"]};">{money(avg_sales)}</div>
    <div class="kpi-sub">Per row within selection</div>
  </div>
  <div class="kpi-card"><div class="kpi-glow"></div>
    <div class="kpi-label">Total Quantity Sold</div>
    <div class="kpi-value" style="color:{NEON["amber"]};">{num(total_qty)}</div>
    <div class="kpi-sub">From Quantity column (if available)</div>
  </div>
</div>
    """,
    unsafe_allow_html=True,
)

csv_bytes = fdf.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    "Download filtered CSV",
    data=csv_bytes,
    file_name="filtered_sales_data.csv",
    mime="text/csv",
    use_container_width=True,
)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

plot_base = _plotly_theme()
colorway = [NEON["cyan"], NEON["magenta"], NEON["lime"], "#4cc9f0", "#f72585", "#ffd166", "#a0c4ff"]

st.markdown("### Executive Overview")
top1, top2 = st.columns([1.05, 1.55], gap="medium")
bot1, bot2 = st.columns([1.05, 1.55], gap="medium")

with top1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Sales by Region")
    if region_col:
        region_sales = (
            fdf.groupby(region_col, dropna=False)[sales_col].sum().sort_values(ascending=False).reset_index()
        )
        fig = px.pie(
            region_sales,
            names=region_col,
            values=sales_col,
            hole=0.62,
            color_discrete_sequence=colorway,
        )
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            marker=dict(line=dict(color="rgba(255,255,255,0.10)", width=1)),
            hovertemplate="<b>%{label}</b><br>Sales: %{value:,.0f}<br>Share: %{percent}<extra></extra>",
        )
        fig.update_layout(**plot_base, height=320)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Region column not found.")
    st.markdown("</div>", unsafe_allow_html=True)

with top2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Sales by Category")
    if category_col:
        cat_sales = (
            fdf.groupby(category_col, dropna=False)[sales_col].sum().sort_values(ascending=False).reset_index()
        )
        fig = px.bar(
            cat_sales,
            x=category_col,
            y=sales_col,
            color=category_col,
            color_discrete_sequence=colorway,
        )
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Sales: %{y:,.0f}<extra></extra>",
            marker_line_color="rgba(53,242,255,0.25)",
            marker_line_width=1,
        )
        fig.update_layout(**plot_base, height=320)
        style_axes(fig)
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Category column not found.")
    st.markdown("</div>", unsafe_allow_html=True)

with bot1:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Profit Analysis")
    ts_profit = (
        fdf.dropna(subset=["Date"])
        .assign(Month=lambda d: d["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", dropna=False)[profit_col]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    if not ts_profit.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ts_profit["Month"],
                y=ts_profit[profit_col],
                mode="lines+markers",
                line=dict(color=NEON["lime"], width=3),
                marker=dict(size=6, color=NEON["lime"], line=dict(color="rgba(255,255,255,0.16)", width=1)),
                hovertemplate="Month: %{x|%b %Y}<br>Profit: %{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(**plot_base, height=320)
        style_axes(fig)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No valid dates found for profit analysis.")
    st.markdown("</div>", unsafe_allow_html=True)

with bot2:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Monthly Sales Trend")
    ts_sales = (
        fdf.dropna(subset=["Date"])
        .assign(Month=lambda d: d["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", dropna=False)[sales_col]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    if not ts_sales.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ts_sales["Month"],
                y=ts_sales[sales_col],
                mode="lines",
                line=dict(color=NEON["cyan"], width=3),
                fill="tozeroy",
                fillcolor="rgba(53,242,255,0.14)",
                hovertemplate="Month: %{x|%b %Y}<br>Sales: %{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(**plot_base, height=320)
        style_axes(fig)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No valid dates found for monthly sales trend.")
    st.markdown("</div>", unsafe_allow_html=True)

with st.expander("More insights (optional)", expanded=False):
    row_a, row_b, row_c = st.columns([1.15, 1.7, 1.15], gap="medium")

with row_a:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Sales by Quarter")
    qcol = quarter_col
    if qcol:
        q = fdf.groupby(qcol, dropna=False)[sales_col].sum().reset_index().sort_values(qcol)
        fig = px.bar(
            q,
            x=qcol,
            y=sales_col,
            color_discrete_sequence=[NEON["cyan"]],
        )
        fig.update_traces(hovertemplate="<b>%{x}</b><br>Sales: %{y:,.0f}<extra></extra>")
        fig.update_layout(**plot_base, height=260)
        style_axes(fig)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Quarter column not found in this dataset.")
    st.markdown("</div>", unsafe_allow_html=True)

with row_b:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Monthly Profit Trend")
    ts_profit = (
        fdf.dropna(subset=["Date"])
        .assign(Month=lambda d: d["Date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month", dropna=False)[profit_col]
        .sum()
        .reset_index()
        .sort_values("Month")
    )
    if not ts_profit.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=ts_profit["Month"],
                y=ts_profit[profit_col],
                mode="lines",
                line=dict(color=NEON["lime"], width=3),
                fill="tozeroy",
                fillcolor="rgba(0,255,154,0.10)",
                hovertemplate="Month: %{x|%b %Y}<br>Profit: %{y:,.0f}<extra></extra>",
            )
        )
        fig.update_layout(**plot_base, height=260)
        style_axes(fig)
        fig.update_xaxes(title=None)
        fig.update_yaxes(title=None)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No valid dates found for profit trend.")
    st.markdown("</div>", unsafe_allow_html=True)

with row_c:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("#### Category Share (Treemap)")
    if category_col and region_col:
        tre = (
            fdf.groupby([category_col, region_col], dropna=False)[sales_col]
            .sum()
            .reset_index()
            .sort_values(sales_col, ascending=False)
        )
        fig = px.treemap(
            tre,
            path=[category_col, region_col],
            values=sales_col,
            color=sales_col,
            color_continuous_scale=["rgba(53,242,255,0.15)", NEON["magenta"]],
        )
        fig.update_traces(hovertemplate="<b>%{label}</b><br>Sales: %{value:,.0f}<extra></extra>")
        fig.update_layout(**plot_base, height=260)
        style_axes(fig)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    elif category_col:
        tre = fdf.groupby(category_col, dropna=False)[sales_col].sum().reset_index()
        fig = px.treemap(
            tre,
            path=[category_col],
            values=sales_col,
            color=sales_col,
            color_continuous_scale=["rgba(53,242,255,0.15)", NEON["magenta"]],
        )
        fig.update_layout(**plot_base, height=260)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Category column not found for treemap.")
    st.markdown("</div>", unsafe_allow_html=True)


st.markdown("### Data Explorer")
st.caption("Search and filter the currently selected dataset, then export it from the sidebar.")

with st.expander("Advanced table filters", expanded=False):
    search = st.text_input("Search (matches any text column)", value="")
    numeric_cols = [c for c in fdf.columns if pd.api.types.is_numeric_dtype(fdf[c])]
    chosen_num = st.selectbox("Numeric column filter", options=["(none)"] + numeric_cols, index=0)
    if chosen_num != "(none)" and not fdf[chosen_num].dropna().empty:
        lo, hi = float(fdf[chosen_num].min()), float(fdf[chosen_num].max())
        rng = st.slider(f"{chosen_num} range", min_value=lo, max_value=hi, value=(lo, hi))
    else:
        rng = None

view = fdf.copy()
if search.strip():
    s = search.strip().lower()
    text_cols = [c for c in view.columns if view[c].dtype == "object"]
    if text_cols:
        m = pd.Series(False, index=view.index)
        for c in text_cols:
            m |= view[c].astype(str).str.lower().str.contains(s, na=False)
        view = view[m]
if rng is not None and chosen_num != "(none)":
    view = view[view[chosen_num].between(rng[0], rng[1], inclusive="both")]

st.dataframe(
    view,
    use_container_width=True,
    height=420,
)