from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
TABLE_DIR = REPO_ROOT / "output" / "tables"

FINANCIAL_INDUSTRIES = {"银行", "非银金融"}


@dataclass(frozen=True)
class ModelSpec:
    name: str
    formula: str
    dependent_var: str
    sample_note: str
    data_filter: str = "all"
    use_clustered_se: bool = True


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    lo, hi = series.quantile([lower, upper])
    return series.clip(lo, hi)


def prepare_panel() -> pd.DataFrame:
    df = pd.read_csv(PROCESSED_DIR / "firm_panel_selected_years.csv")
    df = df.dropna(subset=["ticker", "industry", "year", "eps", "eps_asset", "log_market_cap", "log_assets"])
    df = df.copy()
    df["year"] = df["year"].astype(int)
    df["is_csi500"] = (df["index_group"] == "CSI 500").astype(int)
    df["is_financial"] = df["industry"].isin(FINANCIAL_INDUSTRIES).astype(int)
    df["eps_w"] = winsorize(df["eps"])
    df["eps_asset_scaled"] = df["eps_asset"] * 1e12
    df["eps_asset_scaled_w"] = winsorize(df["eps_asset_scaled"])
    df["firm_observation_count"] = df.groupby("ticker")["ticker"].transform("size")
    return df


def fit_model(spec: ModelSpec, df: pd.DataFrame):
    model_df = df.copy()
    if spec.data_filter == "non_financial":
        model_df = model_df[model_df["is_financial"] == 0]
    elif spec.data_filter == "repeat_firms":
        model_df = model_df[model_df["firm_observation_count"] >= 2]

    model_df = model_df.dropna(subset=[spec.dependent_var, "log_market_cap", "log_assets"])

    fit_kwargs = {}
    if spec.use_clustered_se:
        fit_kwargs = {
            "cov_type": "cluster",
            "cov_kwds": {"groups": model_df["industry"]},
        }
    else:
        fit_kwargs = {"cov_type": "HC3"}

    result = smf.ols(spec.formula, data=model_df).fit(**fit_kwargs)
    return result, model_df


def coefficient_table(model_name: str, result) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "model": model_name,
            "term": result.params.index,
            "coefficient": result.params.values,
            "std_error": result.bse.values,
            "t_value": result.tvalues.values,
            "p_value": result.pvalues.values,
        }
    )


def stars(p_value: float) -> str:
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def build_summary_row(spec: ModelSpec, result, model_df: pd.DataFrame) -> dict[str, object]:
    size_terms = ["log_market_cap", "log_assets", "is_csi500"]
    row: dict[str, object] = {
        "model": spec.name,
        "dependent_variable": spec.dependent_var,
        "sample": spec.sample_note,
        "n_observations": int(result.nobs),
        "n_firms": int(model_df["ticker"].nunique()),
        "n_industries": int(model_df["industry"].nunique()),
        "r_squared": result.rsquared,
        "adj_r_squared": result.rsquared_adj,
        "covariance": result.cov_type,
    }
    for term in size_terms:
        if term in result.params.index:
            p_value = result.pvalues[term]
            row[f"{term}_coef"] = result.params[term]
            row[f"{term}_se"] = result.bse[term]
            row[f"{term}_p"] = p_value
            row[f"{term}_sig"] = stars(p_value)
        else:
            row[f"{term}_coef"] = np.nan
            row[f"{term}_se"] = np.nan
            row[f"{term}_p"] = np.nan
            row[f"{term}_sig"] = ""
    return row


def write_markdown_summary(summary: pd.DataFrame) -> None:
    display_cols = [
        "model",
        "dependent_variable",
        "sample",
        "n_observations",
        "n_firms",
        "r_squared",
        "log_market_cap_coef",
        "log_market_cap_se",
        "log_assets_coef",
        "log_assets_se",
        "is_csi500_coef",
        "is_csi500_se",
    ]
    out = summary[display_cols].copy()
    for col in out.select_dtypes(include=["float"]).columns:
        out[col] = out[col].map(lambda x: "" if pd.isna(x) else f"{x:.4f}")

    headers = list(out.columns)
    rows = out.astype(str).values.tolist()
    markdown_table = []
    markdown_table.append("| " + " | ".join(headers) + " |")
    markdown_table.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        markdown_table.append("| " + " | ".join(row) + " |")

    markdown = "# Panel Regression Summary\n\n"
    markdown += "Standard errors are industry-clustered unless otherwise noted. "
    markdown += "Stars are reported in the CSV output.\n\n"
    markdown += "\n".join(markdown_table)
    (TABLE_DIR / "panel_regression_summary.md").write_text(markdown, encoding="utf-8")


def run_empirical_models() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = prepare_panel()
    specs = [
        ModelSpec(
            name="M1_pooled_ols",
            formula="eps ~ log_market_cap + log_assets + is_csi500",
            dependent_var="eps",
            sample_note="Full selected-year sample",
        ),
        ModelSpec(
            name="M2_year_industry_fe",
            formula="eps ~ log_market_cap + log_assets + is_csi500 + C(year) + C(industry)",
            dependent_var="eps",
            sample_note="Full sample with year and industry fixed effects",
        ),
        ModelSpec(
            name="M3_non_financial_fe",
            formula="eps ~ log_market_cap + log_assets + is_csi500 + C(year) + C(industry)",
            dependent_var="eps",
            sample_note="Excludes banks and non-bank financial firms",
            data_filter="non_financial",
        ),
        ModelSpec(
            name="M4_winsorized_eps_fe",
            formula="eps_w ~ log_market_cap + log_assets + is_csi500 + C(year) + C(industry)",
            dependent_var="eps_w",
            sample_note="EPS winsorized at 1st and 99th percentiles",
        ),
        ModelSpec(
            name="M5_efficiency_fe",
            formula="eps_asset_scaled_w ~ log_market_cap + log_assets + is_csi500 + C(year) + C(industry)",
            dependent_var="eps_asset_scaled_w",
            sample_note="Alternative outcome: winsorized EPS/assets, scaled by 1e12",
        ),
        ModelSpec(
            name="M6_firm_year_fe",
            formula="eps_w ~ log_market_cap + log_assets + C(ticker) + C(year)",
            dependent_var="eps_w",
            sample_note="Repeat-firm sample with firm and year fixed effects",
            data_filter="repeat_firms",
            use_clustered_se=False,
        ),
    ]

    all_coefficients = []
    summary_rows = []
    for spec in specs:
        result, model_df = fit_model(spec, df)
        all_coefficients.append(coefficient_table(spec.name, result))
        summary_rows.append(build_summary_row(spec, result, model_df))

    coefficients = pd.concat(all_coefficients, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    return coefficients, summary


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    coefficients, summary = run_empirical_models()

    coefficients.to_csv(TABLE_DIR / "panel_regression_coefficients.csv", index=False)
    summary.to_csv(TABLE_DIR / "panel_regression_summary.csv", index=False)
    write_markdown_summary(summary)

    # Backward-compatible exports used by the Level 1 README and older scripts.
    baseline = coefficients[coefficients["model"] == "M1_pooled_ols"].copy()
    baseline.to_csv(TABLE_DIR / "baseline_regression_eps.csv", index=False)
    diagnostics = summary[summary["model"] == "M1_pooled_ols"][
        ["n_observations", "n_firms", "r_squared", "adj_r_squared"]
    ].melt(var_name="metric", value_name="value")
    diagnostics.to_csv(TABLE_DIR / "baseline_regression_diagnostics.csv", index=False)

    print(f"Panel regression outputs saved to: {TABLE_DIR}")


if __name__ == "__main__":
    main()
