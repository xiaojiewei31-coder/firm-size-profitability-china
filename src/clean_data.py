from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLE_DIR = REPO_ROOT / "output" / "tables"


def find_source(relative_path: str) -> Path:
    candidates = [
        REPO_ROOT / "data" / "raw" / relative_path,
        REPO_ROOT.parent / relative_path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find source file: {relative_path}")


def clean_column_name(value: object) -> str:
    text = str(value).replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def export_eps_timeseries() -> pd.DataFrame:
    path = find_source("Eps对比/data/ALL DATA.xlsx")
    raw = pd.read_excel(path, header=None)
    df = raw.iloc[2:21, [0, 1, 2]].copy()
    df.columns = ["year", "csi300_eps", "csi500_eps"]
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    for col in ["csi300_eps", "csi500_eps"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["csi300_eps_growth"] = df["csi300_eps"].pct_change()
    df["csi500_eps_growth"] = df["csi500_eps"].pct_change()
    first_300 = df.loc[df.index[0], "csi300_eps"]
    first_500 = df.loc[df.index[0], "csi500_eps"]
    df["csi300_eps_index"] = df["csi300_eps"] / first_300 * 100
    df["csi500_eps_index"] = df["csi500_eps"] / first_500 * 100
    df.to_csv(PROCESSED_DIR / "eps_timeseries.csv", index=False)
    return df


def export_eps_asset_timeseries() -> pd.DataFrame:
    path = find_source("EPS:Asset分析/EPS:Asset对比.xlsx")
    raw = pd.read_excel(path, header=None)
    df = raw.iloc[1:, [0, 1, 2]].copy()
    df.columns = ["year", "csi300_eps_asset", "csi500_eps_asset"]
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    for col in ["csi300_eps_asset", "csi500_eps_asset"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["csi300_eps_asset_index"] = df["csi300_eps_asset"] / df["csi300_eps_asset"].iloc[0] * 100
    df["csi500_eps_asset_index"] = df["csi500_eps_asset"] / df["csi500_eps_asset"].iloc[0] * 100
    df.to_csv(PROCESSED_DIR / "eps_asset_timeseries.csv", index=False)
    return df


def read_firm_file(relative_path: str, year: int, index_group: str) -> pd.DataFrame:
    try:
        path = find_source(relative_path)
    except FileNotFoundError:
        return pd.DataFrame()

    raw = pd.read_excel(path, header=None)
    header_row = None
    for i, row in raw.iterrows():
        values = [str(v).strip() for v in row.tolist()]
        if "证券代码" in values:
            header_row = i
            break
    if header_row is None:
        return pd.DataFrame()

    headers = [clean_column_name(v) for v in raw.iloc[header_row].tolist()]
    data = raw.iloc[header_row + 1 :].copy()
    data.columns = headers

    def find_col(keyword: str) -> str:
        matches = [col for col in data.columns if keyword in col]
        if not matches:
            raise KeyError(keyword)
        return matches[0]

    try:
        out = pd.DataFrame(
            {
                "year": year,
                "index_group": index_group,
                "ticker": data[find_col("证券代码")],
                "company_name": data[find_col("证券名称")],
                "industry": data[find_col("行业")],
                "eps": pd.to_numeric(data[find_col("每股收益")], errors="coerce"),
                "total_assets": pd.to_numeric(data[find_col("资产总计")], errors="coerce"),
                "market_cap": pd.to_numeric(data[find_col("总市值")], errors="coerce"),
            }
        )
    except KeyError:
        return pd.DataFrame()

    out = out.dropna(subset=["ticker", "eps", "total_assets", "market_cap"])
    out = out[out["ticker"].astype(str).str.contains(r"\.", regex=True)]
    out["eps_asset"] = out["eps"] / out["total_assets"]
    out["log_assets"] = np.log(out["total_assets"].where(out["total_assets"] > 0))
    out["log_market_cap"] = np.log(out["market_cap"].where(out["market_cap"] > 0))
    return out


def export_firm_panel() -> pd.DataFrame:
    files = [
        ("EPS:Asset分析/2007 300.xlsx", 2007, "CSI 300"),
        ("EPS:Asset分析/2007中证.xlsx", 2007, "CSI 500"),
        ("EPS:Asset分析/2009 300.xlsx", 2009, "CSI 300"),
        ("EPS:Asset分析/2014 300.xlsx", 2014, "CSI 300"),
        ("EPS:Asset分析/2014 中证.xlsx", 2014, "CSI 500"),
        ("EPS:Asset分析/2019年沪深300.xlsx", 2019, "CSI 300"),
        ("EPS:Asset分析/2019年中证500.xlsx", 2019, "CSI 500"),
        ("EPS:Asset分析/2023 300.xlsx", 2023, "CSI 300"),
        ("EPS:Asset分析/2023 中证.xlsx", 2023, "CSI 500"),
    ]
    frames = [read_firm_file(*item) for item in files]
    df = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
    df.to_csv(PROCESSED_DIR / "firm_panel_selected_years.csv", index=False)
    return df


def read_industry_eps(relative_path: str, year: int) -> pd.DataFrame:
    path = find_source(relative_path)
    raw = pd.read_excel(path, header=None)
    rows = []
    for start_col, index_group in [(0, "CSI 300"), (4, "CSI 500")]:
        block = raw.iloc[2:, start_col : start_col + 3].copy()
        block.columns = ["industry", "firm_count", "avg_eps"]
        block = block.dropna(subset=["industry"])
        block["year"] = year
        block["index_group"] = index_group
        block["firm_count"] = pd.to_numeric(block["firm_count"], errors="coerce")
        block["avg_eps"] = pd.to_numeric(block["avg_eps"], errors="coerce")
        rows.append(block[["year", "index_group", "industry", "firm_count", "avg_eps"]])
    return pd.concat(rows, ignore_index=True)


def export_industry_eps() -> pd.DataFrame:
    files = [
        ("Eps对比/行业分析/2009年行业EPS分析.xlsx", 2009),
        ("Eps对比/行业分析/2017年行业EPS分析.xlsx", 2017),
        ("Eps对比/行业分析/2023年行业EPS分析.xlsx", 2023),
    ]
    df = pd.concat([read_industry_eps(*item) for item in files], ignore_index=True)
    df.to_csv(PROCESSED_DIR / "industry_eps.csv", index=False)
    return df


def export_summary_tables(eps: pd.DataFrame, firm_panel: pd.DataFrame) -> None:
    growth = eps[["csi300_eps_growth", "csi500_eps_growth"]].std(skipna=True)
    summary = pd.DataFrame(
        {
            "metric": [
                "mean_eps_2005_2023_csi300",
                "mean_eps_2005_2023_csi500",
                "eps_growth_volatility_csi300",
                "eps_growth_volatility_csi500",
                "firm_observations",
            ],
            "value": [
                eps["csi300_eps"].mean(),
                eps["csi500_eps"].mean(),
                growth["csi300_eps_growth"],
                growth["csi500_eps_growth"],
                len(firm_panel),
            ],
        }
    )
    summary.to_csv(TABLE_DIR / "summary_statistics.csv", index=False)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)

    eps = export_eps_timeseries()
    export_eps_asset_timeseries()
    firm_panel = export_firm_panel()
    export_industry_eps()
    export_summary_tables(eps, firm_panel)

    print("Data cleaning complete.")
    print(f"Processed files saved to: {PROCESSED_DIR}")
    print(f"Summary tables saved to: {TABLE_DIR}")


if __name__ == "__main__":
    main()
