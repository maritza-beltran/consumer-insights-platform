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
CHARTS = ROOT / "outputs" / "charts"


@st.cache_data
def load_data() -> dict:
    data = {}
    paths = {
        "surveys": PROCESSED / "guest_surveys_classified.parquet",
        "stores": PROCESSED / "stores_clean.parquet",
        "theme_impact": TABLES / "theme_impact.csv",
        "segment_summary": TABLES / "segment_summary.csv",
        "store_scores": TABLES / "store_opportunity_scores.csv",
        "drivers": TABLES / "satisfaction_drivers.csv",
    }
    for key, path in paths.items():
        if path.suffix == ".parquet":
            data[key] = pd.read_parquet(path)
        elif path.exists():
            data[key] = pd.read_csv(path)
    impact_path = TABLES / "impact_sizing.json"
    if impact_path.exists():
        data["impact"] = json.loads(impact_path.read_text())
    return data


def _brand_nps(df: pd.DataFrame) -> float:
    promoters = (df["nps_score"] >= 9).mean()
    detractors = (df["nps_score"] <= 6).mean()
    return round((promoters - detractors) * 100, 1)


def main() -> None:
    st.set_page_config(
        page_title="Brew & Bloom VoC Insights",
        page_icon="☕",
        layout="wide",
    )

    st.title("☕ Brew & Bloom — Voice of Customer Insights")
    st.caption("Synthetic data demo | Consumer Insights Platform")

    required = PROCESSED / "guest_surveys_classified.parquet"
    if not required.exists():
        st.warning(
            "Processed data not found. Run the pipeline first:\n\n"
            "```\npip install -r requirements.txt\n"
            "python src/generate_data.py\n"
            "python src/validate_data.py\n"
            "python src/build_outputs.py\n```"
        )
        return

    data = load_data()
    surveys = data["surveys"]
    theme_impact = data.get("theme_impact", pd.DataFrame())
    segment_summary = data.get("segment_summary", pd.DataFrame())
    store_scores = data.get("store_scores", pd.DataFrame())
    impact = data.get("impact", {})

    # KPI row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Brand NPS", _brand_nps(surveys))
    c2.metric("Avg CSAT", f"{surveys['csat_score'].mean():.2f}")
    c3.metric("Surveys", f"{len(surveys):,}")
    c4.metric("Stores", f"{surveys['store_id'].nunique()}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["VoC Themes", "Segments", "Stores", "Drivers", "Executive Impact"]
    )

    with tab1:
        st.subheader("Theme Prevalence & NPS Impact")
        if not theme_impact.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.bar(
                    theme_impact.head(10),
                    x="mention_count",
                    y="theme",
                    orientation="h",
                    title="Top Themes by Mentions",
                    color_discrete_sequence=["#6F4E37"],
                )
                fig.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                fig2 = px.bar(
                    theme_impact.head(10),
                    x="nps_gap_vs_brand",
                    y="theme",
                    orientation="h",
                    title="NPS Gap vs Brand Average",
                    color="nps_gap_vs_brand",
                    color_continuous_scale=["#C0392B", "#F5F5F5", "#27AE60"],
                )
                fig2.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Guest Segment Performance")
        if not segment_summary.empty:
            fig = px.bar(
                segment_summary,
                x="segment",
                y="brand_nps",
                color="segment",
                title="NPS by Segment",
                text="brand_nps",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(segment_summary, use_container_width=True)

        st.subheader("Filter Explorer")
        region = st.selectbox("Region", ["All"] + sorted(surveys["region"].unique()))
        segment = st.selectbox("Segment", ["All"] + sorted(surveys["segment"].unique()))
        filtered = surveys.copy()
        if region != "All":
            filtered = filtered[filtered["region"] == region]
        if segment != "All":
            filtered = filtered[filtered["segment"] == segment]
        st.metric("Filtered NPS", _brand_nps(filtered))

    with tab3:
        st.subheader("Store Opportunity Ranking")
        if not store_scores.empty:
            tier = st.multiselect(
                "Priority tier",
                options=sorted(store_scores["priority_tier"].unique()),
                default=list(store_scores["priority_tier"].unique()),
            )
            stores_filtered = store_scores[store_scores["priority_tier"].isin(tier)]
            fig = px.scatter(
                stores_filtered,
                x="avg_nps",
                y="opportunity_score",
                size="survey_count",
                color="priority_tier",
                hover_name="store_name",
                title="Store NPS vs Opportunity Score",
                color_discrete_map={
                    "urgent": "#C0392B",
                    "improve": "#E67E22",
                    "monitor": "#95A5A6",
                },
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(
                stores_filtered[
                    [
                        "store_name",
                        "region",
                        "store_type",
                        "store_nps",
                        "detractor_rate",
                        "opportunity_score",
                        "priority_tier",
                    ]
                ].head(20),
                use_container_width=True,
            )

    with tab4:
        st.subheader("Satisfaction Driver Model")
        drivers = data.get("drivers", pd.DataFrame())
        if not drivers.empty:
            top = drivers.head(12).sort_values("coefficient")
            fig = px.bar(
                top,
                x="coefficient",
                y="theme",
                orientation="h",
                title="Theme Coefficients (Promoter Logistic Model)",
                color="coefficient",
                color_continuous_scale=["#C0392B", "#F5F5F5", "#27AE60"],
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Positive coefficients increase promoter likelihood; "
                "negative coefficients are pain-point drag."
            )

    with tab5:
        st.subheader("Executive Impact Sizing")
        if impact:
            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Net Annual Impact",
                f"${impact.get('net_annual_impact_usd', 0):,.0f}",
            )
            c2.metric(
                "Recoverable Revenue",
                f"${impact.get('recoverable_revenue_usd', 0):,.0f}",
            )
            c3.metric(
                "Focus Theme",
                impact.get("recommended_focus_theme", "—").replace("_", " ").title(),
            )
            meets = impact.get("meets_100k_threshold", False)
            st.success("Meets $100K+ threshold") if meets else st.warning("Below $100K threshold")
            st.json(impact)
        else:
            st.info("Run `python src/build_outputs.py` to generate impact sizing.")

        memo_path = ROOT / "reports" / "executive_memo.md"
        if memo_path.exists():
            with st.expander("Executive Memo"):
                st.markdown(memo_path.read_text())


if __name__ == "__main__":
    main()
