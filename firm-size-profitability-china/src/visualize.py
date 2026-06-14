from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(REPO_ROOT / ".matplotlib-cache"))
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PROCESSED_DIR = REPO_ROOT / "data" / "processed"
FIGURE_DIR = REPO_ROOT / "output" / "figures"

INDUSTRY_EN = {
    "医药生物": "Healthcare",
    "电力设备": "Electrical Equipment",
    "计算机": "Computer",
    "食品饮料": "Food & Beverage",
    "汽车": "Automobile",
    "基础化工": "Basic Chemicals",
    "煤炭": "Coal",
    "传媒": "Media",
    "家用电器": "Home Appliances",
    "美容护理": "Beauty Care",
    "轻工制造": "Light Manufacturing",
    "纺织服饰": "Textile & Apparel",
    "非银金融": "Non-bank Financials",
    "银行": "Banks",
    "交通运输": "Transportation",
    "电子": "Electronics",
}


def save_figure(path: Path) -> None:
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_eps_trend() -> None:
    df = pd.read_csv(PROCESSED_DIR / "eps_timeseries.csv")
    plt.figure(figsize=(9, 5))
    plt.plot(df["year"], df["csi300_eps"], marker="o", label="CSI 300")
    plt.plot(df["year"], df["csi500_eps"], marker="o", label="CSI 500")
    plt.title("EPS Trend: CSI 300 vs CSI 500, 2005-2023")
    plt.xlabel("Year")
    plt.ylabel("EPS")
    plt.legend()
    plt.grid(alpha=0.25)
    save_figure(FIGURE_DIR / "eps_trend_csi300_vs_csi500.png")


def plot_growth_volatility() -> None:
    df = pd.read_csv(PROCESSED_DIR / "eps_timeseries.csv")
    long = df.melt(
        id_vars="year",
        value_vars=["csi300_eps_growth", "csi500_eps_growth"],
        var_name="series",
        value_name="growth",
    ).dropna()
    long["series"] = long["series"].map(
        {
            "csi300_eps_growth": "CSI 300",
            "csi500_eps_growth": "CSI 500",
        }
    )
    plt.figure(figsize=(9, 5))
    sns.barplot(data=long, x="year", y="growth", hue="series")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Annual EPS Growth Rate")
    plt.xlabel("Year")
    plt.ylabel("Growth rate")
    plt.xticks(rotation=45)
    save_figure(FIGURE_DIR / "eps_growth_rate_comparison.png")


def plot_eps_asset() -> None:
    df = pd.read_csv(PROCESSED_DIR / "eps_asset_timeseries.csv")
    plt.figure(figsize=(9, 5))
    plt.plot(df["year"], df["csi300_eps_asset_index"], marker="o", label="CSI 300")
    plt.plot(df["year"], df["csi500_eps_asset_index"], marker="o", label="CSI 500")
    plt.title("Indexed EPS-to-Asset Ratio")
    plt.xlabel("Year")
    plt.ylabel("Index, first year = 100")
    plt.legend()
    plt.grid(alpha=0.25)
    save_figure(FIGURE_DIR / "eps_asset_index_trend.png")


def plot_industry_2023() -> None:
    df = pd.read_csv(PROCESSED_DIR / "industry_eps.csv")
    df = df[df["year"] == 2023].dropna(subset=["avg_eps"])
    top_industries = (
        df.groupby("industry")["avg_eps"]
        .mean()
        .sort_values(ascending=False)
        .head(12)
        .index
    )
    plot_df = df[df["industry"].isin(top_industries)].copy()
    plot_df["industry_label"] = plot_df["industry"].map(INDUSTRY_EN).fillna(plot_df["industry"])
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=plot_df,
        y="industry_label",
        x="avg_eps",
        hue="index_group",
        errorbar=None,
    )
    ax.legend(title="Index group")
    plt.title("Industry-Level Average EPS, 2023")
    plt.xlabel("Average EPS")
    plt.ylabel("Industry")
    save_figure(FIGURE_DIR / "industry_eps_2023.png")


def plot_size_profitability_scatter() -> None:
    df = pd.read_csv(PROCESSED_DIR / "firm_panel_selected_years.csv")
    df = df[df["year"] == 2023].dropna(subset=["log_market_cap", "eps"])
    plt.figure(figsize=(9, 5))
    sns.scatterplot(data=df, x="log_market_cap", y="eps", hue="index_group", alpha=0.65)
    sns.regplot(data=df, x="log_market_cap", y="eps", scatter=False, color="black")
    plt.title("Firm Size and EPS, 2023")
    plt.xlabel("Log market capitalization")
    plt.ylabel("EPS")
    save_figure(FIGURE_DIR / "size_profitability_scatter_2023.png")


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    plot_eps_trend()
    plot_growth_volatility()
    plot_eps_asset()
    plot_industry_2023()
    plot_size_profitability_scatter()
    print(f"Figures saved to: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
