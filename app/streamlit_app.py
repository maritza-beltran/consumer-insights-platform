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


def standard_nps(scores: pd.Series) -> float:
    """NPS from a score series: (% promoters − % detractors) × 100."""
    if scores.empty:
        return 0.0
    return round(((scores >= 9).mean() - (scores <= 6).mean()) * 100, 1)


def brand_nps(df: pd.DataFrame) -> float:
    return standard_nps(df["nps"])


def missing_files() -> list[Path]:
    return [path for path in REQUIRED_FILES if not path.exists()]


def render_setup_message() -> None:
    st.error("Required output files are missing.")
    st.markdown(SETUP_CMD)


DRIVER_LABELS = {
    "wait_time_rating": "Wait Time",
    "drink_quality_rating": "Drink Quality",
    "order_accuracy_rating": "Order Accuracy",
    "staff_friendliness_rating": "Staff Friendliness",
    "cleanliness_rating": "Cleanliness",
    "mobile_app_experience_rating": "Mobile App Experience",
    "rewards_satisfaction": "Rewards Satisfaction",
    "price_value_perception": "Price-Value Perception",
}


def _driver_label(driver: str) -> str:
    return DRIVER_LABELS.get(driver, _label(driver))


def _comment_count(surveys: pd.DataFrame, theme_summary: pd.DataFrame) -> int:
    if not theme_summary.empty:
        return int(theme_summary["comment_count"].sum())
    return int(surveys["comment_text"].astype(str).str.strip().ne("").sum())


def _commented_surveys(surveys: pd.DataFrame) -> pd.DataFrame:
    return surveys[surveys["comment_text"].astype(str).str.strip() != ""]


def _apply_voc_filters(
    surveys: pd.DataFrame,
    region: str,
    store_type: str,
    guest_segment: str,
    visit_channel: str,
) -> pd.DataFrame:
    filt = surveys.copy()
    if region != "All":
        filt = filt[filt["region"] == region]
    if store_type != "All":
        filt = filt[filt["store_type"] == store_type]
    if guest_segment != "All":
        filt = filt[filt["guest_segment"] == guest_segment]
    if visit_channel != "All":
        filt = filt[filt["visit_channel"] == visit_channel]
    return filt


def _theme_metrics(surveys: pd.DataFrame) -> pd.DataFrame:
    """Aggregate VoC theme metrics from filtered survey rows with comments."""
    commented = _commented_surveys(surveys)
    if commented.empty:
        return pd.DataFrame()

    groups = commented.groupby("primary_theme")
    metrics = groups.agg(
        theme_frequency=("survey_id", "count"),
        negative_share=("is_negative_experience", "mean"),
        avg_csat=("csat", "mean"),
        avg_revisit_intent=("revisit_intent", "mean"),
    ).reset_index()
    metrics["avg_nps"] = groups["nps"].apply(standard_nps).values
    metrics["theme_label"] = metrics["primary_theme"].map(_label)
    return metrics.sort_values("theme_frequency", ascending=False).round(4)


def _detractor_over_index(surveys: pd.DataFrame) -> pd.DataFrame:
    commented = _commented_surveys(surveys)
    if commented.empty:
        return pd.DataFrame()

    total = len(commented)
    detractors = commented[commented["nps"] <= 6]
    detractor_total = len(detractors)
    if detractor_total == 0:
        return pd.DataFrame()

    all_counts = commented.groupby("primary_theme").size().rename("all_count")
    det_counts = detractors.groupby("primary_theme").size().rename("detractor_count")
    table = pd.concat([all_counts, det_counts], axis=1).fillna(0).astype(int).reset_index()
    table["share_of_all_comments"] = (table["all_count"] / total).round(4)
    table["share_of_detractor_comments"] = (table["detractor_count"] / detractor_total).round(4)
    table["detractor_over_index"] = (
        table["share_of_detractor_comments"] / table["share_of_all_comments"]
    ).replace([float("inf")], 0).round(4)
    table["avg_nps"] = (
        commented.groupby("primary_theme")["nps"]
        .apply(standard_nps)
        .reindex(table["primary_theme"])
        .values
    )
    table["negative_share"] = (
        commented.groupby("primary_theme")["is_negative_experience"]
        .mean()
        .reindex(table["primary_theme"])
        .values
    )
    return table.sort_values("detractor_over_index", ascending=False).round(4)


def page_executive_readout(data: dict, surveys: pd.DataFrame) -> None:
    st.header("Executive Readout")
    st.caption("Brew & Bloom Coffee Co. · Jan–Jun 2024 · Synthetic demo dataset")

    theme_summary = data.get("theme_summary", pd.DataFrame())
    theme_impact = data.get("theme_impact", pd.DataFrame())
    drivers = data.get("drivers", pd.DataFrame())
    store_scores = data.get("store_scores", pd.DataFrame())
    impact_summary = data.get("impact_summary", pd.DataFrame())
    impact = data.get("impact", {})

    total_comments = _comment_count(surveys, theme_summary)
    overall_nps = brand_nps(surveys)
    overall_csat = surveys["csat"].mean()
    avg_revisit = surveys["revisit_intent"].mean()

    top_negative_theme = "—"
    if not theme_summary.empty:
        top_negative_theme = _label(
            theme_summary.sort_values("negative_share", ascending=False).iloc[0]["primary_theme"]
        )

    top_driver = "—"
    if not drivers.empty:
        top_driver = _driver_label(drivers.sort_values("rank").iloc[0]["driver"])

    revenue_90d = 0.0
    if not impact_summary.empty:
        revenue_90d = float(impact_summary.iloc[0]["estimated_incremental_revenue"])
    elif not store_scores.empty:
        revenue_90d = float(store_scores["estimated_90_day_upside"].head(30).sum())

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    r1c1.metric("Total Surveys", f"{len(surveys):,}")
    r1c2.metric("Total Comments", f"{total_comments:,}")
    r1c3.metric("Overall NPS", overall_nps)
    r1c4.metric("Overall CSAT", f"{overall_csat:.2f}")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    r2c1.metric("Avg Revisit Intent", f"{avg_revisit:.2f}")
    r2c2.metric("Top Negative VoC Theme", top_negative_theme)
    r2c3.metric("Top Satisfaction Driver", top_driver)
    r2c4.metric("Est. 90-Day Revenue Opportunity", f"${revenue_90d:,.0f}")

    st.subheader("Executive Charts")
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        if not theme_summary.empty:
            top5_vol = theme_summary.nlargest(5, "comment_count").copy()
            top5_vol["theme_label"] = top5_vol["primary_theme"].map(_label)
            fig_vol = px.bar(
                top5_vol.sort_values("comment_count"),
                x="comment_count",
                y="theme_label",
                orientation="h",
                color_discrete_sequence=[BRAND_COLOR],
                title="Top 5 Themes by Comment Volume",
            )
            fig_vol.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig_vol, use_container_width=True)

    with col_b:
        if not theme_impact.empty:
            top5_gap = theme_impact.nsmallest(5, "theme_nps_gap").copy()
            top5_gap["theme_label"] = top5_gap["primary_theme"].map(_label)
            fig_gap = px.bar(
                top5_gap.sort_values("theme_nps_gap"),
                x="theme_nps_gap",
                y="theme_label",
                orientation="h",
                color="theme_nps_gap",
                color_continuous_scale=["#C0392B", "#F5F5F5"],
                title="Top 5 Themes by NPS Gap",
            )
            fig_gap.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
            st.plotly_chart(fig_gap, use_container_width=True)

    with col_c:
        if not store_scores.empty:
            top5_stores = store_scores.head(5).copy()
            fig_stores = px.bar(
                top5_stores.sort_values("opportunity_score"),
                x="opportunity_score",
                y="store_name",
                orientation="h",
                color="region",
                title="Top 5 Store Opportunities",
            )
            st.plotly_chart(fig_stores, use_container_width=True)

    focus_theme = (
        _label(impact.get("recommended_focus_theme", ""))
        if impact.get("recommended_focus_theme")
        else top_negative_theme
    )
    top_store = store_scores.iloc[0]["store_name"] if not store_scores.empty else "priority stores"

    st.subheader("Key Takeaway")
    st.markdown(
        f"Brew & Bloom's brand NPS is **{overall_nps}** with **{top_negative_theme}** driving the "
        f"highest share of negative guest comments. **{top_driver}** is the strongest predictor of "
        f"high revisit intent, indicating that operational and product-quality fixes can move both "
        f"satisfaction scores and return behavior."
    )

    st.subheader("Recommended Action")
    if not impact_summary.empty:
        row = impact_summary.iloc[0]
        st.markdown(f"**{row['initiative']}**")
        st.markdown(row["assumptions"])
    elif not store_scores.empty:
        st.markdown(store_scores.iloc[0]["recommended_action"])
    else:
        st.markdown(
            f"Prioritize **{focus_theme}** improvements starting with **{top_store}** and "
            f"expand to the highest-opportunity locations."
        )

    st.subheader("Expected Business Impact")
    if not impact_summary.empty:
        row = impact_summary.iloc[0]
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("Incremental Revenue (90 days)", f"${row['estimated_incremental_revenue']:,.0f}")
        ic2.metric("Pilot Stores", int(row["target_store_count"]))
        ic3.metric("Repeat-Visit Lift Assumption", f"{float(row['expected_repeat_visit_lift']):.1%}")
        st.caption(row["measurement_plan"])
        if impact.get("meets_100k_threshold"):
            st.success("Initiative exceeds the $100K incremental revenue threshold.")
    else:
        st.metric("Estimated 90-Day Upside (Top 30 Stores)", f"${revenue_90d:,.0f}")

    memo = ROOT / "reports" / "executive_memo.md"
    if memo.exists():
        with st.expander("Full executive memo"):
            st.markdown(memo.read_text())


def page_voc_deep_dive(surveys: pd.DataFrame) -> None:
    st.header("Voice of Customer Deep Dive")
    st.info(
        "High frequency does not always mean high impact. Themes with larger NPS and revisit gaps "
        "should receive higher leadership attention."
    )

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        region = st.selectbox("Region", ["All"] + sorted(surveys["region"].dropna().unique()), key="voc_region")
    with f2:
        store_type = st.selectbox(
            "Store Type", ["All"] + sorted(surveys["store_type"].dropna().unique()), key="voc_store_type"
        )
    with f3:
        guest_segment = st.selectbox(
            "Guest Segment", ["All"] + sorted(surveys["guest_segment"].dropna().unique()), key="voc_segment"
        )
    with f4:
        visit_channel = st.selectbox(
            "Visit Channel", ["All"] + sorted(surveys["visit_channel"].dropna().unique()), key="voc_channel"
        )

    filtered = _apply_voc_filters(surveys, region, store_type, guest_segment, visit_channel)
    metrics = _theme_metrics(filtered)
    detractor_table = _detractor_over_index(filtered)

    if metrics.empty:
        st.warning("No commented surveys match the selected filters.")
        return

    st.caption(f"{len(_commented_surveys(filtered)):,} comments · {len(filtered):,} surveys in view")

    row_a, row_b = st.columns(2)
    with row_a:
        fig_freq = px.bar(
            metrics.head(10).sort_values("theme_frequency"),
            x="theme_frequency",
            y="theme_label",
            orientation="h",
            color_discrete_sequence=[BRAND_COLOR],
            title="Theme Frequency",
        )
        fig_freq.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_freq, use_container_width=True)

    with row_b:
        fig_neg = px.bar(
            metrics.head(10).sort_values("negative_share"),
            x="negative_share",
            y="theme_label",
            orientation="h",
            color="negative_share",
            color_continuous_scale="Reds",
            title="Negative Share by Theme",
        )
        fig_neg.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_neg, use_container_width=True)

    row_c, row_d, row_e = st.columns(3)
    with row_c:
        fig_nps = px.bar(
            metrics.sort_values("avg_nps").head(10),
            x="avg_nps",
            y="theme_label",
            orientation="h",
            color="avg_nps",
            color_continuous_scale="RdYlGn",
            title="Average NPS by Theme",
        )
        fig_nps.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_nps, use_container_width=True)

    with row_d:
        fig_csat = px.bar(
            metrics.sort_values("avg_csat").head(10),
            x="avg_csat",
            y="theme_label",
            orientation="h",
            color="avg_csat",
            color_continuous_scale="RdYlGn",
            title="Average CSAT by Theme",
        )
        fig_csat.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_csat, use_container_width=True)

    with row_e:
        fig_revisit = px.bar(
            metrics.sort_values("avg_revisit_intent").head(10),
            x="avg_revisit_intent",
            y="theme_label",
            orientation="h",
            color="avg_revisit_intent",
            color_continuous_scale="RdYlGn",
            title="Average Revisit Intent by Theme",
        )
        fig_revisit.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_revisit, use_container_width=True)

    st.subheader("Theme Metrics")
    st.dataframe(
        metrics[
            [
                "primary_theme",
                "theme_frequency",
                "negative_share",
                "avg_nps",
                "avg_csat",
                "avg_revisit_intent",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Detractor Over-Index")
    if not detractor_table.empty:
        st.dataframe(detractor_table, use_container_width=True, hide_index=True)
    else:
        st.write("No detractor comments in the current filter selection.")

    st.subheader("Sample Comments")
    theme_options = metrics["primary_theme"].tolist()
    selected_theme = st.selectbox(
        "Select theme",
        theme_options,
        format_func=_label,
        key="voc_sample_theme",
    )
    samples = _commented_surveys(filtered)
    samples = samples[samples["primary_theme"] == selected_theme][
        ["survey_id", "guest_segment", "visit_channel", "region", "nps", "csat", "sentiment_label", "comment_text"]
    ].head(8)
    if samples.empty:
        st.write("No sample comments for this theme.")
    else:
        st.dataframe(samples, use_container_width=True, hide_index=True)


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
        page_voc_deep_dive(surveys)
    elif page == PAGES[2]:
        page_drivers_segments(data, surveys)
    else:
        page_opportunities(data)


if __name__ == "__main__":
    main()
