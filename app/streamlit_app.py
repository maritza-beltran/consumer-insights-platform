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
        "theme_impact": TABLES / "theme_impact.csv",
        "segment_summary": TABLES / "segment_summary.csv",
        "store_scores": TABLES / "store_opportunity_scores.csv",
        "drivers": TABLES / "satisfaction_drivers.csv",
        "revisit_drivers": TABLES / "revisit_intent_drivers.csv",
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
        if not theme_impact.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.bar(theme_impact.head(10), x="mention_count", y="theme", orientation="h", color_discrete_sequence=["#6F4E37"])
                fig.update_layout(yaxis={"categoryorder": "total ascending"}, title="Top Themes by Mentions")
                st.plotly_chart(fig, use_container_width=True)
            with col_b:
                fig2 = px.bar(theme_impact.head(10), x="nps_gap_vs_brand", y="theme", orientation="h", title="NPS Gap vs Brand")
                fig2.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig2, use_container_width=True)

    with tab2:
        st.subheader("Guest Segment & Dimension Performance")
        if not segment_summary.empty:
            fig = px.bar(segment_summary, x="guest_segment", y="brand_nps", color="guest_segment", title="NPS by Segment")
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
                x="avg_nps",
                y="opportunity_score",
                size="survey_count",
                color="priority_tier",
                hover_name="store_name",
                title="Store NPS vs Opportunity Score",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(store_scores.head(20), use_container_width=True)

    with tab4:
        drivers = data.get("drivers", pd.DataFrame())
        if not drivers.empty:
            top = drivers.head(12).sort_values("coefficient")
            fig = px.bar(top, x="coefficient", y="theme", orientation="h", title="Theme Drivers of NPS Promoter Status")
            st.plotly_chart(fig, use_container_width=True)

    with tab5:
        revisit = data.get("revisit_drivers", pd.DataFrame())
        if not revisit.empty:
            fig = px.bar(revisit.sort_values("coefficient"), x="coefficient", y="rating", orientation="h",
                         title="Experience Ratings Predicting Revisit Intent")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Linear model on wait time, drink quality, staff, app, rewards, and value ratings.")

    with tab6:
        st.subheader("Executive Impact Sizing")
        if impact:
            c1, c2, c3 = st.columns(3)
            c1.metric("Net Annual Impact", f"${impact.get('net_annual_impact_usd', 0):,.0f}")
            c2.metric("Recoverable Revenue", f"${impact.get('recoverable_revenue_usd', 0):,.0f}")
            c3.metric("Focus Theme", impact.get("recommended_focus_theme", "—").replace("_", " ").title())
            if impact.get("meets_100k_threshold"):
                st.success("Meets $100K+ threshold")
            st.json(impact)
        memo = ROOT / "reports" / "executive_memo.md"
        if memo.exists():
            with st.expander("Executive Memo"):
                st.markdown(memo.read_text())


if __name__ == "__main__":
    main()
