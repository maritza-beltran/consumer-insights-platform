"""Voice of Customer Insights Platform — reads precomputed pipeline outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "outputs" / "tables"

BRAND_COLOR = "#6F4E37"
SETUP_CMD = (
    "Data not found. Generate and build outputs first:\n\n"
    "```bash\n"
    "python src/generate_data.py\n"
    "python src/build_outputs.py\n"
    "```\n\n"
    "Or with the project virtualenv:\n\n"
    "```bash\n"
    ".venv/bin/python src/generate_data.py\n"
    ".venv/bin/python src/build_outputs.py\n"
    "```"
)

PAGES = [
    "Executive Readout",
    "Voice of Customer Deep Dive",
    "Drivers and Segments",
    "Opportunities and Recommendations",
]

REQUIRED_FILES = [
    PROCESSED / "guest_surveys_classified.parquet",
    TABLES / "theme_summary.csv",
    TABLES / "segment_summary.csv",
    TABLES / "driver_importance.csv",
    TABLES / "store_opportunity_ranking.csv",
]


def _label(text: str) -> str:
    return text.replace("_", " ").title()


@st.cache_data
def load_data() -> dict:
    data: dict = {}
    parquet_paths = {
        "surveys": PROCESSED / "guest_surveys_classified.parquet",
        "stores": PROCESSED / "stores_clean.parquet",
    }
    csv_paths = {
        "theme_summary": TABLES / "theme_summary.csv",
        "theme_impact": TABLES / "theme_impact.csv",
        "detractor_themes": TABLES / "detractor_theme_analysis.csv",
        "segment_summary": TABLES / "segment_summary.csv",
        "segment_theme_matrix": TABLES / "segment_theme_matrix.csv",
        "channel_summary": TABLES / "channel_summary.csv",
        "region_summary": TABLES / "region_summary.csv",
        "store_scores": TABLES / "store_opportunity_ranking.csv",
        "drivers": TABLES / "driver_importance.csv",
        "model_metrics": TABLES / "model_metrics.csv",
        "product_insights": TABLES / "product_insights.csv",
        "impact_summary": TABLES / "impact_summary.csv",
        "validation_summary": TABLES / "validation_summary.csv",
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


def missing_files() -> list[Path]:
    return [path for path in REQUIRED_FILES if not path.exists()]


def render_setup_message() -> None:
    st.error("Required output files are missing.")
    st.markdown(SETUP_CMD)


def render_kpi_row(surveys: pd.DataFrame) -> None:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Brand NPS", brand_nps(surveys))
    c2.metric("Avg CSAT", f"{surveys['csat'].mean():.2f}")
    c3.metric("Avg Revisit Intent", f"{surveys['revisit_intent'].mean():.2f}")
    c4.metric("Surveys", f"{len(surveys):,}")
    c5.metric("Stores", f"{surveys['store_id'].nunique()}")


def page_executive_readout(data: dict, surveys: pd.DataFrame) -> None:
    st.header("Executive Readout")
    st.caption("Brew & Bloom Coffee Co. · Jan–Jun 2024 · Synthetic demo dataset")
    render_kpi_row(surveys)

    impact_summary = data.get("impact_summary", pd.DataFrame())
    impact = data.get("impact", {})
    theme_impact = data.get("theme_impact", pd.DataFrame())

    st.subheader("Priority Initiative")
    if not impact_summary.empty:
        row = impact_summary.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated Incremental Revenue", f"${row['estimated_incremental_revenue']:,.0f}")
        c2.metric("Target Stores", int(row["target_store_count"]))
        c3.metric("Improvement Window", f"{int(row['improvement_window_days'])} days")
        st.markdown(f"**{row['initiative']}**")
        st.info(row["assumptions"])
        if impact.get("meets_100k_threshold"):
            st.success("Initiative exceeds the $100K incremental revenue threshold.")
    elif impact:
        st.metric("Focus Theme", _label(impact.get("recommended_focus_theme", "—")))

    col_a, col_b = st.columns(2)
    with col_a:
        if not theme_impact.empty:
            top = theme_impact.sort_values("impact_rank").head(8).copy()
            top["theme_label"] = top["primary_theme"].map(_label)
            fig = px.bar(
                top,
                x="theme_nps_gap",
                y="theme_label",
                orientation="h",
                color="theme_nps_gap",
                color_continuous_scale=["#C0392B", "#F5F5F5", "#27AE60"],
                title="Top Themes by NPS Gap vs Brand",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        theme_summary = data.get("theme_summary", pd.DataFrame())
        if not theme_summary.empty:
            top_vol = theme_summary.head(8).copy()
            top_vol["theme_label"] = top_vol["primary_theme"].map(_label)
            fig2 = px.pie(
                top_vol,
                names="theme_label",
                values="comment_count",
                title="Comment Share by Theme",
                color_discrete_sequence=px.colors.sequential.YlOrBr,
            )
            st.plotly_chart(fig2, use_container_width=True)

    memo = ROOT / "reports" / "executive_memo.md"
    if memo.exists():
        with st.expander("Executive memo"):
            st.markdown(memo.read_text())


def page_voc_deep_dive(data: dict) -> None:
    st.header("Voice of Customer Deep Dive")

    theme_summary = data.get("theme_summary", pd.DataFrame())
    detractor_themes = data.get("detractor_themes", pd.DataFrame())
    theme_impact = data.get("theme_impact", pd.DataFrame())

    if theme_summary.empty:
        st.warning("theme_summary.csv not found — run the build pipeline.")
        return

    theme_summary = theme_summary.copy()
    theme_summary["theme_label"] = theme_summary["primary_theme"].map(_label)

    col_a, col_b = st.columns(2)
    with col_a:
        fig = px.bar(
            theme_summary.head(10),
            x="comment_count",
            y="theme_label",
            orientation="h",
            color_discrete_sequence=[BRAND_COLOR],
            title="Theme Volume (Comments)",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.bar(
            theme_summary.head(10),
            x="negative_share",
            y="theme_label",
            orientation="h",
            color="negative_share",
            color_continuous_scale="Reds",
            title="Negative Experience Share by Theme",
        )
        fig2.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    if not theme_impact.empty:
        impact_plot = theme_impact.copy()
        impact_plot["theme_label"] = impact_plot["primary_theme"].map(_label)
        fig3 = px.scatter(
            impact_plot,
            x="theme_avg_csat",
            y="theme_avg_nps",
            size="impact_rank",
            color="theme_revisit_gap",
            hover_name="theme_label",
            color_continuous_scale="RdYlGn",
            title="Theme Satisfaction Profile (Standard NPS)",
            labels={"theme_avg_csat": "Avg CSAT", "theme_avg_nps": "Theme NPS"},
        )
        st.plotly_chart(fig3, use_container_width=True)

    if not detractor_themes.empty:
        st.subheader("Detractor Over-Index")
        det = detractor_themes.head(10).copy()
        det["theme_label"] = det["primary_theme"].map(_label)
        fig4 = px.bar(
            det.sort_values("detractor_over_index"),
            x="detractor_over_index",
            y="theme_label",
            orientation="h",
            color_discrete_sequence=["#C0392B"],
            title="Themes Over-Represented Among Detractors",
        )
        fig4.add_vline(x=1.0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig4, use_container_width=True)
        st.dataframe(detractor_themes, use_container_width=True, hide_index=True)


def page_drivers_segments(data: dict, surveys: pd.DataFrame) -> None:
    st.header("Drivers and Segments")

    drivers = data.get("drivers", pd.DataFrame())
    metrics = data.get("model_metrics", pd.DataFrame())
    segment_summary = data.get("segment_summary", pd.DataFrame())
    theme_matrix = data.get("segment_theme_matrix", pd.DataFrame())

    st.subheader("High Revisit Intent Drivers")
    st.caption("Logistic model: high revisit intent = revisit_intent ≥ 4 · Features standardized before fitting.")
    if not drivers.empty:
        plot_drivers = drivers.sort_values("model_coefficient")
        fig = px.bar(
            plot_drivers,
            x="model_coefficient",
            y="driver",
            orientation="h",
            color="model_coefficient",
            color_continuous_scale=["#C0392B", "#F5F5F5", "#27AE60"],
            title="Experience Rating Drivers (Logistic Coefficients)",
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        for _, row in drivers.sort_values("rank").head(3).iterrows():
            st.write(f"**#{int(row['rank'])} {row['driver']}** — {row['plain_english_interpretation']}")

    if not metrics.empty:
        st.dataframe(metrics, use_container_width=True, hide_index=True)

    st.subheader("Guest Segment Performance")
    if not segment_summary.empty:
        seg = segment_summary.copy()
        seg["segment_label"] = seg["guest_segment"].map(_label)
        fig2 = px.bar(
            seg,
            x="segment_label",
            y="avg_nps",
            color="avg_nps",
            color_continuous_scale="RdYlGn",
            title="Segment NPS (Standard Formula)",
            labels={"avg_nps": "NPS", "segment_label": "Segment"},
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(
            segment_summary[
                [
                    "guest_segment",
                    "survey_count",
                    "avg_nps",
                    "avg_csat",
                    "avg_revisit_intent",
                    "top_negative_theme",
                    "recommended_action",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if not theme_matrix.empty:
        st.subheader("Segment × Theme Matrix")
        pivot = theme_matrix.pivot_table(
            index="primary_theme",
            columns="guest_segment",
            values="comment_count",
            fill_value=0,
        )
        top_themes = pivot.sum(axis=1).sort_values(ascending=False).head(8).index
        pivot = pivot.loc[top_themes]
        fig3 = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=[_label(c) for c in pivot.columns],
                y=[_label(i) for i in pivot.index],
                colorscale="YlOrBr",
            )
        )
        fig3.update_layout(title="Comment Count by Segment and Theme", height=420)
        st.plotly_chart(fig3, use_container_width=True)

    channel = data.get("channel_summary", pd.DataFrame())
    if not channel.empty:
        st.subheader("Visit Channel Benchmarks")
        fig4 = px.bar(
            channel,
            x="visit_channel",
            y="avg_nps",
            color="visit_channel",
            title="Average Raw NPS Score by Channel",
        )
        st.plotly_chart(fig4, use_container_width=True)

    with st.expander("Filtered segment drill-down"):
        seg = st.selectbox("Segment", ["All"] + sorted(surveys["guest_segment"].unique()), key="seg_filter")
        region = st.selectbox("Region", ["All"] + sorted(surveys["region"].unique()), key="region_filter")
        filt = surveys.copy()
        if seg != "All":
            filt = filt[filt["guest_segment"] == seg]
        if region != "All":
            filt = filt[filt["region"] == region]
        st.metric("Filtered NPS", brand_nps(filt))


def page_opportunities(data: dict) -> None:
    st.header("Opportunities and Recommendations")

    store_scores = data.get("store_scores", pd.DataFrame())
    product_insights = data.get("product_insights", pd.DataFrame())
    impact_summary = data.get("impact_summary", pd.DataFrame())

    if not store_scores.empty:
        st.subheader("Store Opportunity Ranking")
        fig = px.scatter(
            store_scores,
            x="nps",
            y="opportunity_score",
            size="avg_daily_transactions",
            color="region",
            hover_name="store_name",
            hover_data=["top_negative_theme", "recommended_action"],
            title="Store NPS vs Opportunity Score",
            labels={"nps": "Store NPS", "opportunity_score": "Opportunity Score"},
        )
        st.plotly_chart(fig, use_container_width=True)

        top_stores = store_scores.head(15).copy()
        top_stores["theme_label"] = top_stores["top_negative_theme"].map(_label)
        fig2 = px.bar(
            top_stores.sort_values("opportunity_score"),
            x="opportunity_score",
            y="store_name",
            color="theme_label",
            orientation="h",
            title="Top 15 Priority Stores",
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(
            store_scores[
                [
                    "store_name",
                    "region",
                    "store_type",
                    "nps",
                    "csat",
                    "opportunity_score",
                    "top_negative_theme",
                    "recommended_action",
                    "estimated_90_day_upside",
                ]
            ].head(20),
            use_container_width=True,
            hide_index=True,
        )

    if not product_insights.empty:
        st.subheader("Product Insights")
        fig3 = px.scatter(
            product_insights,
            x="avg_product_rating",
            y="trial_rate",
            size="avg_repeat_purchase_intent",
            color="product_category",
            hover_name="product_name",
            title="Product Rating vs Trial Rate",
        )
        st.plotly_chart(fig3, use_container_width=True)
        st.dataframe(
            product_insights[
                [
                    "product_name",
                    "product_category",
                    "trial_rate",
                    "avg_product_rating",
                    "price_value_complaint_rate",
                    "sweetness_complaint_rate",
                    "recommendation",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if not impact_summary.empty:
        st.subheader("Impact Sizing & Measurement")
        row = impact_summary.iloc[0]
        st.markdown(f"**Initiative:** {row['initiative']}")
        st.write(row["measurement_plan"])


def main() -> None:
    st.set_page_config(
        page_title="Voice of Customer Insights Platform",
        page_icon="☕",
        layout="wide",
    )

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", PAGES, label_visibility="collapsed")

    missing = missing_files()
    if missing:
        st.title("Voice of Customer Insights Platform")
        render_setup_message()
        with st.expander("Missing files"):
            for path in missing:
                st.code(str(path.relative_to(ROOT)))
        return

    data = load_data()
    surveys = data.get("surveys")
    if surveys is None or surveys.empty:
        st.title("Voice of Customer Insights Platform")
        render_setup_message()
        return

    st.sidebar.markdown("---")
    st.sidebar.metric("Brand NPS", brand_nps(surveys))
    st.sidebar.caption(f"{len(surveys):,} surveys · {surveys['store_id'].nunique()} stores")

    st.title("Voice of Customer Insights Platform")

    if page == PAGES[0]:
        page_executive_readout(data, surveys)
    elif page == PAGES[1]:
        page_voc_deep_dive(data)
    elif page == PAGES[2]:
        page_drivers_segments(data, surveys)
    else:
        page_opportunities(data)


if __name__ == "__main__":
    main()
