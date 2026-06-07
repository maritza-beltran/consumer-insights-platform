"""Streamlit dashboard for Brew & Bloom Voice of Customer insights."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"


@st.cache_data
def load_data() -> dict:
    data = {}
    parquet_paths = {
        "surveys": PROCESSED / "guest_surveys_classified.parquet",
        "stores": PROCESSED / "stores_clean.parquet",
    }
    csv_paths = {
        "theme_summary": TABLES / "theme_summary.csv",
        "theme_impact": TABLES / "theme_impact.csv",
        "detractor_themes": TABLES / "detractor_theme_analysis.csv",
        "segment_summary": TABLES / "segment_summary.csv",
        "store_scores": TABLES / "store_opportunity_ranking.csv",
        "drivers": TABLES / "driver_importance.csv",
        "model_metrics": TABLES / "model_metrics.csv",
        "product_insights": TABLES / "product_insights.csv",
        "impact_summary": TABLES / "impact_summary.csv",
        "channel_summary": TABLES / "channel_summary.csv",
    }
    for key, path in parquet_paths.items():
        if path.exists():
            data[key] = pd.read_parquet(path)
    for key, path in csv_paths.items():
        if path.exists():
            data[key] = pd.read_csv(path)
    impact_path = TABLES / "impact_sizing.json"
    if impact_path.exists():
        data["impact"] = json.loads(impact_path.read_text())
    return data


def brand_nps(df: pd.DataFrame) -> float:
    return round(((df["nps"] >= 9).mean() - (df["nps"] <= 6).mean()) * 100, 1)


def main() -> None:
    st.set_page_config(page_title="Brew & Bloom VoC Insights", page_icon="☕", layout="wide")
    st.title("☕ Brew & Bloom — Voice of Customer Insights")
    st.caption("Synthetic multi-dataset demo | 90 stores | 12,000 surveys | Jan–Jun 2024")

    if not (PROCESSED / "guest_surveys_classified.parquet").exists():
        st.warning("Run: `make setup && make data && make validate && make build`")
        return

    data = load_data()
    surveys = data["surveys"]
    theme_summary = data.get("theme_summary", pd.DataFrame())
    theme_impact = data.get("theme_impact", pd.DataFrame())
    segment_summary = data.get("segment_summary", pd.DataFrame())
    store_scores = data.get("store_scores", pd.DataFrame())
    impact = data.get("impact", {})

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Brand NPS", brand_nps(surveys))
    c2.metric("Avg CSAT", f"{surveys['csat'].mean():.2f}")
    c3.metric("Avg Revisit Intent", f"{surveys['revisit_intent'].mean():.2f}")
    c4.metric("Surveys", f"{len(surveys):,}")
    c5.metric("Stores", f"{surveys['store_id'].nunique()}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["VoC Themes", "Segments", "Stores", "NPS Drivers", "Revisit Drivers", "Executive Impact"]
    )

    with tab1:
        st.subheader("Theme Prevalence & NPS Impact")
        if not theme_summary.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.bar(
                    theme_summary.head(10),
                    x="comment_count",
                    y="primary_theme",
                    orientation="h",
                    color_discrete_sequence=["#6F4E37"],
                )
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, title="Top Themes by Comments")
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                if not theme_impact.empty:
                    fig2 = px.bar(
                        theme_impact.head(10),
                        x="theme_nps_gap",
                        y="primary_theme",
                        orientation="h",
                        title="NPS Gap vs Brand",
                    )
                    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
                    st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Guest Segment & Dimension Performance")
        if not segment_summary.empty:
            fig = px.bar(segment_summary, x="guest_segment", y="avg_nps", color="guest_segment", title="Avg NPS by Segment")
            st.plotly_chart(fig, use_container_width=True)
        channel = data.get("channel_summary", pd.DataFrame())
        if not channel.empty:
            st.dataframe(channel, use_container_width=True)
        seg = st.selectbox("Filter segment", ["All"] + sorted(surveys["guest_segment"].unique()))
        region = st.selectbox("Filter region", ["All"] + sorted(surveys["region"].unique()))
        filt = surveys.copy()
        if seg != "All":
            filt = filt[filt["guest_segment"] == seg]
        if region != "All":
            filt = filt[filt["region"] == region]
        st.metric("Filtered NPS", brand_nps(filt))

    with tab3:
        st.subheader("Store Opportunity Ranking")
        if not store_scores.empty:
            fig = px.scatter(
                store_scores,
                x="nps",
                y="opportunity_score",
                size="avg_daily_transactions",
                color="region",
                hover_name="store_name",
                title="Store NPS vs Opportunity Score",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(store_scores.head(20), use_container_width=True)

    with tab4:
        drivers = data.get("drivers", pd.DataFrame())
        metrics = data.get("model_metrics", pd.DataFrame())
        if not drivers.empty:
            top = drivers.head(8).sort_values("model_coefficient")
            fig = px.bar(
                top,
                x="model_coefficient",
                y="driver",
                orientation="h",
                title="Experience Drivers of High Revisit Intent",
            )
            st.plotly_chart(fig, use_container_width=True)
        if not metrics.empty:
            st.dataframe(metrics, use_container_width=True)

    with tab5:
        revisit = data.get("drivers", pd.DataFrame())
        if not revisit.empty:
            st.dataframe(revisit[["driver", "rank", "odds_ratio", "plain_english_interpretation"]], use_container_width=True)
            st.caption("Logistic model: high revisit intent = revisit_intent >= 4.")

    with tab6:
        st.subheader("Executive Impact Sizing")
        impact_summary = data.get("impact_summary", pd.DataFrame())
        if not impact_summary.empty:
            row = impact_summary.iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.metric("Incremental Revenue", f"${row['estimated_incremental_revenue']:,.0f}")
            c2.metric("Target Stores", int(row["target_store_count"]))
            c3.metric("Window (days)", int(row["improvement_window_days"]))
            st.write(row["assumptions"])
            st.write(row["measurement_plan"])
        if impact:
            c1, c2 = st.columns(2)
            c1.metric("Brand NPS", impact.get("brand_nps_baseline", "—"))
            c2.metric("Focus Theme", impact.get("recommended_focus_theme", "—").replace("_", " ").title())
            if impact.get("meets_100k_threshold"):
                st.success("Meets $100K+ threshold")
        memo = ROOT / "reports" / "executive_memo.md"
        if memo.exists():
            with st.expander("Executive Memo"):
                st.markdown(memo.read_text())


if __name__ == "__main__":
    main()
