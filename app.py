from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data" / "processed"
TABLE_DIR = REPO_ROOT / "output" / "tables"

INDUSTRY_EN = {
    "医药生物": "Healthcare",
    "电子": "Electronics",
    "电力设备": "Electrical Equipment",
    "非银金融": "Non-bank Financials",
    "交通运输": "Transportation",
    "基础化工": "Basic Chemicals",
    "房地产": "Real Estate",
    "有色金属": "Non-ferrous Metals",
    "机械设备": "Machinery",
    "公用事业": "Utilities",
    "计算机": "Computer",
    "食品饮料": "Food & Beverage",
    "汽车": "Automobile",
    "银行": "Banks",
    "国防军工": "Defense",
    "钢铁": "Steel",
    "传媒": "Media",
    "商贸零售": "Retail",
    "煤炭": "Coal",
    "农林牧渔": "Agriculture",
    "家用电器": "Home Appliances",
    "美容护理": "Beauty Care",
    "轻工制造": "Light Manufacturing",
    "纺织服饰": "Textile & Apparel",
}


st.set_page_config(
    page_title="A-Share Firm Size and Profitability",
    page_icon="",
    layout="wide",
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    firm = pd.read_csv(DATA_DIR / "firm_panel_selected_years.csv")
    eps = pd.read_csv(DATA_DIR / "eps_timeseries.csv")
    industry = pd.read_csv(DATA_DIR / "industry_eps.csv")
    regression = pd.read_csv(TABLE_DIR / "panel_regression_summary.csv")

    firm["industry_label"] = firm["industry"].map(INDUSTRY_EN).fillna(firm["industry"])
    firm["market_cap_billion"] = firm["market_cap"] / 1e9
    firm["assets_billion"] = firm["total_assets"] / 1e9
    firm["eps_asset_scaled"] = firm["eps_asset"] * 1e12
    firm["size_bucket"] = pd.qcut(firm["market_cap"], q=4, duplicates="drop")

    industry["industry_label"] = industry["industry"].map(INDUSTRY_EN).fillna(industry["industry"])
    return firm, eps, industry, regression


def format_number(value: float, digits: int = 2) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{value:,.{digits}f}"


def metric_cards(df: pd.DataFrame) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Firm observations", f"{len(df):,}")
    c2.metric("Unique firms", f"{df['ticker'].nunique():,}")
    c3.metric("Average EPS", format_number(df["eps"].mean()))
    c4.metric("Median market cap", f"{format_number(df['market_cap_billion'].median())} bn")
    c5.metric("Median assets", f"{format_number(df['assets_billion'].median())} bn")


def sidebar_filters(firm: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")
    years = sorted(firm["year"].unique().tolist())
    selected_years = st.sidebar.multiselect("Year", years, default=years)

    groups = sorted(firm["index_group"].unique().tolist())
    selected_groups = st.sidebar.multiselect("Index group", groups, default=groups)

    industries = sorted(firm["industry_label"].unique().tolist())
    selected_industries = st.sidebar.multiselect(
        "Industry",
        industries,
        default=industries,
        help="Industry names are translated from the original Chinese industry labels.",
    )

    cap_range = st.sidebar.slider(
        "Market cap range, RMB billion",
        min_value=float(np.floor(firm["market_cap_billion"].min())),
        max_value=float(np.ceil(firm["market_cap_billion"].max())),
        value=(
            float(np.floor(firm["market_cap_billion"].quantile(0.01))),
            float(np.ceil(firm["market_cap_billion"].quantile(0.99))),
        ),
    )

    filtered = firm[
        firm["year"].isin(selected_years)
        & firm["index_group"].isin(selected_groups)
        & firm["industry_label"].isin(selected_industries)
        & firm["market_cap_billion"].between(cap_range[0], cap_range[1])
    ].copy()
    return filtered


def market_overview(eps: pd.DataFrame, firm: pd.DataFrame) -> None:
    st.subheader("Market Overview")
    metric_cards(firm)

    left, right = st.columns(2)
    with left:
        eps_fig = go.Figure()
        eps_fig.add_trace(go.Scatter(x=eps["year"], y=eps["csi300_eps"], mode="lines+markers", name="CSI 300"))
        eps_fig.add_trace(go.Scatter(x=eps["year"], y=eps["csi500_eps"], mode="lines+markers", name="CSI 500"))
        eps_fig.update_layout(title="EPS Trend, 2005-2023", xaxis_title="Year", yaxis_title="EPS")
        st.plotly_chart(eps_fig, use_container_width=True)

    with right:
        growth = eps.melt(
            id_vars="year",
            value_vars=["csi300_eps_growth", "csi500_eps_growth"],
            var_name="series",
            value_name="growth",
        ).dropna()
        growth["series"] = growth["series"].map(
            {"csi300_eps_growth": "CSI 300", "csi500_eps_growth": "CSI 500"}
        )
        fig = px.bar(growth, x="year", y="growth", color="series", barmode="group", title="Annual EPS Growth")
        fig.add_hline(y=0, line_color="black", line_width=1)
        st.plotly_chart(fig, use_container_width=True)


def company_explorer(df: pd.DataFrame) -> None:
    st.subheader("Firm Size and Profitability")
    metric_cards(df)

    x_choice = st.radio(
        "Size axis",
        ["Market capitalization", "Total assets"],
        horizontal=True,
    )
    x_col = "market_cap_billion" if x_choice == "Market capitalization" else "assets_billion"
    x_label = "Market capitalization, RMB billion" if x_col == "market_cap_billion" else "Total assets, RMB billion"

    fig = px.scatter(
        df,
        x=x_col,
        y="eps",
        color="index_group",
        facet_col="year" if df["year"].nunique() <= 5 else None,
        hover_data=["ticker", "company_name", "industry_label", "eps", "market_cap_billion", "assets_billion"],
        trendline="ols" if len(df) >= 20 else None,
        title="Firm Size vs EPS",
        labels={x_col: x_label, "eps": "EPS", "index_group": "Index group"},
    )
    fig.update_xaxes(type="log")
    st.plotly_chart(fig, use_container_width=True)

    table_cols = [
        "year",
        "index_group",
        "ticker",
        "company_name",
        "industry_label",
        "eps",
        "market_cap_billion",
        "assets_billion",
        "eps_asset_scaled",
    ]
    st.dataframe(
        df[table_cols].sort_values(["year", "market_cap_billion"], ascending=[False, False]),
        use_container_width=True,
        hide_index=True,
    )


def industry_explorer(df: pd.DataFrame, industry_eps: pd.DataFrame) -> None:
    st.subheader("Industry Comparison")
    grouped = (
        df.groupby(["year", "index_group", "industry_label"], as_index=False)
        .agg(
            firms=("ticker", "nunique"),
            avg_eps=("eps", "mean"),
            median_market_cap=("market_cap_billion", "median"),
            avg_efficiency=("eps_asset_scaled", "mean"),
        )
        .sort_values("avg_eps", ascending=False)
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            grouped.head(30),
            y="industry_label",
            x="avg_eps",
            color="index_group",
            orientation="h",
            title="Top Industry-Year Average EPS",
            labels={"industry_label": "Industry", "avg_eps": "Average EPS"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.scatter(
            grouped,
            x="median_market_cap",
            y="avg_eps",
            size="firms",
            color="index_group",
            hover_data=["year", "industry_label", "firms"],
            title="Industry Size and Profitability",
            labels={"median_market_cap": "Median market cap, RMB billion", "avg_eps": "Average EPS"},
        )
        fig.update_xaxes(type="log")
        st.plotly_chart(fig, use_container_width=True)

    st.caption("The original industry EPS summary tables are preserved below for auditability.")
    st.dataframe(industry_eps, use_container_width=True, hide_index=True)


def regression_view(regression: pd.DataFrame) -> None:
    st.subheader("Empirical Regression Results")
    st.write(
        "The Level 2 models test whether firm size is associated with profitability after adding "
        "year, industry, and firm fixed effects plus robustness checks."
    )

    main_cols = [
        "model",
        "dependent_variable",
        "sample",
        "n_observations",
        "n_firms",
        "r_squared",
        "log_market_cap_coef",
        "log_market_cap_se",
        "log_market_cap_sig",
        "log_assets_coef",
        "log_assets_se",
        "log_assets_sig",
        "is_csi500_coef",
        "is_csi500_sig",
    ]
    st.dataframe(regression[main_cols], use_container_width=True, hide_index=True)

    fig = px.bar(
        regression,
        x="model",
        y="log_market_cap_coef",
        error_y="log_market_cap_se",
        color="dependent_variable",
        title="Market Capitalization Coefficient Across Models",
        labels={"log_market_cap_coef": "Coefficient on log market cap", "model": "Model"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.info(
        "ROA is not calculated in the current dashboard because the raw exports do not include net income. "
        "A future data version can add ROA = net income / total assets and ROE = net income / book equity."
    )


def main() -> None:
    firm, eps, industry, regression = load_data()
    filtered = sidebar_filters(firm)

    st.title("Firm Size and Profitability in China's A-Share Market")
    st.caption("Interactive dashboard for CSI 300 and CSI 500 constituent analysis.")

    if filtered.empty:
        st.warning("No observations match the current filters.")
        return

    tab_overview, tab_firms, tab_industry, tab_regression = st.tabs(
        ["Market overview", "Firm explorer", "Industry comparison", "Regression results"]
    )

    with tab_overview:
        market_overview(eps, filtered)
    with tab_firms:
        company_explorer(filtered)
    with tab_industry:
        industry_explorer(filtered, industry)
    with tab_regression:
        regression_view(regression)


if __name__ == "__main__":
    main()
