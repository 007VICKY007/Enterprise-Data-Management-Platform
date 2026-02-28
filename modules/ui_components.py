"""
modules/ui_components.py
=========================
Enhancement 5: Descriptive text added below download buttons
Enhancement 6: Combined Excel link removed
"""
import streamlit as st
import pandas as pd
import traceback
from typing import Dict
from .config import AppConfig


_LOTTIE_URLS = {
    "upload":     "https://assets10.lottiefiles.com/packages/lf20_jcikwtux.json",
    "processing": "https://assets9.lottiefiles.com/packages/lf20_ue6xppcm.json",
    "analytics":  "https://assets3.lottiefiles.com/packages/lf20_qp1q7mct.json",
    "success":    "https://assets3.lottiefiles.com/packages/lf20_pKiaUR.json",
}
_LOTTIE_JS_KEY = "_lottie_js_injected"


def _inject_lottie_lib() -> None:
    if st.session_state.get(_LOTTIE_JS_KEY):
        return
    st.markdown(
        '<script src="https://unpkg.com/@lottiefiles/lottie-player@latest'
        '/dist/lottie-player.js"></script>',
        unsafe_allow_html=True,
    )
    st.session_state[_LOTTIE_JS_KEY] = True


def _lottie_player(url: str, fallback_class: str, size: int = 120) -> str:
    return f"""
    <div class="orbit-loader"
         style="width:{size}px;height:{size}px;">
        <div class="center-dot"></div>
        <div class="orbiter"></div>
        <div class="orbiter"></div>
        <div class="orbiter"></div>
    </div>
    """


# Enhancement 5: helper for button description text
def _btn_desc(text: str) -> None:
    """Render a small descriptive line below a download button."""
    st.markdown(
        f'<p style="font-size:0.76rem;color:#7a7a9a;margin-top:0.2rem;'
        f'margin-bottom:0.6rem;line-height:1.45;font-family:Aptos,Segoe UI,Arial,sans-serif;">'
        f'{text}</p>',
        unsafe_allow_html=True,
    )


class UIComponents:
    """Streamlit UI components — with integrated animated guidance."""

    @staticmethod
    def render_header():
        st.markdown(
            f'<h1 class="purple-text">{AppConfig.APP_ICON} {AppConfig.APP_TITLE}</h1>',
            unsafe_allow_html=True,
        )
        st.caption(f"Version {AppConfig.VERSION}")
        st.markdown("---")

    @staticmethod
    def render_sidebar():
        with st.sidebar:
            st.markdown("### 📊 Supported Rules")
            st.markdown("Completeness · Uniqueness · Validity · Standardization")
            st.markdown("### 📁 File Formats")
            st.markdown("CSV · Excel · JSON · Parquet · ODS · XML · xlsx · xlsm · xlsb")

    @staticmethod
    def render_file_format_help():
        with st.expander("📋 Expected File Formats"):
            st.markdown("""
            ### Rules Dataset Format (CSV/Excel)
            **Required Columns:**
            - `column_name` or `column` — Target column name
            - `rule` or `rule_type` — Type of validation
            - `dimension` or `rule_category` — DQ dimension
            - `message` — Validation error message

            **Optional Columns:**
            - `expression` — Rule expression (regex, range, etc.)
            - `severity` — HIGH, MEDIUM, or LOW
            """)

    @staticmethod
    def render_results_dashboard(
        overall_score: float,
        results_df: pd.DataFrame,
        column_scores: Dict[str, float],
        dimension_scores: Dict[str, float],
    ):
        st.subheader("📊 Data Quality Dashboard")
        col1, col2, col3, col4 = st.columns(4)
        clean_count  = len(results_df[results_df["Count of issues"] == 0])
        issue_count  = len(results_df) - clean_count
        pass_columns = sum(1 for s in column_scores.values() if s == 100)

        col1.metric("Overall DQ Score",    f"{overall_score}%")
        col2.metric("Clean Records",       f"{clean_count:,}")
        col3.metric("Records with Issues", f"{issue_count:,}")
        col4.metric("Columns at 100%",     f"{pass_columns}/{len(column_scores)}")

        if overall_score >= 95:
            st.success("🎉 **Excellent!** Outstanding data quality.")
        elif overall_score >= 80:
            st.info("👍 **Good!** Minor improvements needed.")
        elif overall_score >= 60:
            st.warning("⚠️ **Fair!** Significant improvements required.")
        else:
            st.error("❌ **Poor!** Critical data quality issues detected.")

    # Enhancement 5: render_download_section with descriptions
    # Enhancement 6: combined Excel button removed
    @staticmethod
    def render_download_section(output_path, rulebook_path, total_annexures: int):
        st.subheader("📥 Download Reports")
        col1, col2 = st.columns(2)
        with col1:
            with open(output_path, "rb") as f:
                st.download_button(
                    "📊 Download Excel DQ Report", f,
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help=f"Includes DQ score, summary dashboard, column analysis, "
                         f"dimension scores, and {total_annexures} annexures.",
                )
            _btn_desc(
                "Includes DQ score, summary dashboard, column analysis, "
                "dimension scores, and annexures."
            )
        with col2:
            with open(rulebook_path, "rb") as f:
                st.download_button(
                    "📋 Download Rulebook JSON", f,
                    file_name=rulebook_path.name,
                    mime="application/json",
                    use_container_width=True,
                    help="Generated rulebook for reference and reuse",
                )
            _btn_desc("Generated rule configuration file for reference and reuse across assessments.")

    @staticmethod
    def render_detailed_views(
        rulebook: Dict,
        results_df: pd.DataFrame,
        column_scores: Dict[str, float],
        dimension_scores: Dict[str, float],
    ):
        st.subheader("🔍 Detailed Analysis")
        tab1, tab2, tab3, tab4 = st.tabs(
            ["Column Scores", "Dimension Analysis", "Rulebook", "Results Preview"]
        )
        with tab1:
            UIComponents._render_column_scores(column_scores)
        with tab2:
            UIComponents._render_dimension_scores(dimension_scores)
        with tab3:
            st.json(rulebook)
            st.info(f"Total rules: {len(rulebook.get('rules', []))}")
        with tab4:
            UIComponents._render_results_preview(results_df)

    @staticmethod
    def _render_column_scores(column_scores: Dict[str, float]):
        score_data = []
        for col, score in sorted(column_scores.items(), key=lambda x: x[1]):
            status = "✅ PASSED" if score == 100 else "❌ FAILED"
            score_data.append({"Column": col, "DQ Score (%)": score, "Status": status})
        score_df = pd.DataFrame(score_data)
        def color_status(val):
            if val == "✅ PASSED":
                return "background-color: #C6EFCE; color: #006100"
            return "background-color: #FFC7CE; color: #9C0006"
        st.dataframe(
            score_df.style.applymap(color_status, subset=["Status"]),
            use_container_width=True, hide_index=True,
        )

    @staticmethod
    def _render_dimension_scores(dimension_scores: Dict[str, float]):
        if not dimension_scores:
            st.info("No dimension analysis available")
            return
        dim_data = []
        for dimension, score in dimension_scores.items():
            status = "✅ PASSED" if score == 100 else "❌ FAILED"
            dim_data.append({"Dimension": dimension, "DQ Score (%)": score, "Status": status})
        st.dataframe(pd.DataFrame(dim_data), use_container_width=True, hide_index=True)

    @staticmethod
    def _render_results_preview(results_df: pd.DataFrame):
        if results_df.empty:
            st.info("No results to preview")
            return
        preview_cols = [c for c in results_df.columns if c != "original_row"]
        st.dataframe(
            results_df[preview_cols].head(100),
            use_container_width=True, hide_index=True,
        )

    # ── Lottie & Animated helpers (unchanged) ─────────────────────────────────
    @staticmethod
    def render_lottie_upload(label: str = "Drop your file here") -> None:
        _inject_lottie_lib()
        player = _lottie_player(_LOTTIE_URLS["upload"], "lottie-upload-fallback")
        st.markdown(f'<div class="lottie-slot"><div class="lottie-frame">{player}</div>'
                    f'<span class="lottie-caption">{label}</span></div>', unsafe_allow_html=True)

    @staticmethod
    def render_lottie_processing(label: str = "Processing your data…") -> None:
        _inject_lottie_lib()
        player = _lottie_player(_LOTTIE_URLS["processing"], "lottie-process-fallback")
        st.markdown(f'<div class="lottie-slot"><div class="lottie-frame scan-overlay">{player}</div>'
                    f'<span class="lottie-caption">{label}</span></div>', unsafe_allow_html=True)

    @staticmethod
    def render_lottie_analytics(label: str = "Building your report…") -> None:
        _inject_lottie_lib()
        player = _lottie_player(_LOTTIE_URLS["analytics"], "lottie-analytics-fallback")
        st.markdown(f'<div class="lottie-slot"><div class="lottie-frame">{player}</div>'
                    f'<span class="lottie-caption">{label}</span></div>', unsafe_allow_html=True)

    @staticmethod
    def render_lottie_success(label: str = "Assessment complete!") -> None:
        _inject_lottie_lib()
        player = _lottie_player(_LOTTIE_URLS["success"], "lottie-analytics-fallback")
        st.markdown(f'<div class="lottie-slot"><div class="lottie-frame" '
                    f'style="border-color:rgba(16,185,129,0.4);box-shadow:0 0 30px rgba(16,185,129,0.2);">'
                    f'{player}</div><span class="lottie-caption" style="color:#34d399;">'
                    f'{label}</span></div>', unsafe_allow_html=True)

    @staticmethod
    def render_beacon(color: str = "#60a5fa") -> str:
        return (f'<span class="beacon"><span class="beacon-dot" style="background:{color};"></span>'
                f'<span class="beacon-ring" style="border-color:{color}80;"></span></span>')

    @staticmethod
    def render_hint_chip(label: str, tip: str = "", icon: str = "💡") -> None:
        tip_attr = f'data-tip="{tip}"' if tip else ""
        st.markdown(f'<span class="hint-chip" {tip_attr}>{icon} {label}</span>', unsafe_allow_html=True)

    @staticmethod
    def render_action_hint_bar(title: str, message: str, color: str = "#60a5fa") -> None:
        beacon = UIComponents.render_beacon(color)
        st.markdown(f'<div class="action-hint-bar"><div class="ahb-beacon">{beacon}</div>'
                    f'<div class="ahb-text"><strong>{title}:</strong> {message}</div></div>',
                    unsafe_allow_html=True)

    @staticmethod
    def render_arrow_down(color: str = "#60a5fa") -> None:
        st.markdown(f'<div class="guidance-arrow-down" style="color:{color};">↓</div>',
                    unsafe_allow_html=True)

    @staticmethod
    def render_guidance_card(icon, title, description, step_number=None, delay_ms=0):
        badge = (f'<div class="guidance-card-step">{step_number}</div>'
                 if step_number is not None else "")
        st.markdown(f'<div class="guidance-card" style="animation-delay:{delay_ms}ms;">'
                    f'{badge}<span class="guidance-card-icon">{icon}</span>'
                    f'<div class="guidance-card-title">{title}</div>'
                    f'<p class="guidance-card-desc">{description}</p></div>',
                    unsafe_allow_html=True)

    @staticmethod
    def render_micro_progress(pct=100, color_start="#3b82f6", color_end="#a78bfa"):
        st.markdown(f'<div class="micro-progress"><div class="micro-progress-fill" '
                    f'style="--target-width:{pct}%;background:linear-gradient(90deg,{color_start},{color_end});'
                    f'background-size:200% 100%;"></div></div>', unsafe_allow_html=True)

    @staticmethod
    def render_pulsing_dot(color="#f87171"):
        st.markdown(f'<div class="pulsing-dot" style="background:{color};"></div>',
                    unsafe_allow_html=True)

    @staticmethod
    def render_orbit_loader():
        st.markdown('<div class="orbit-loader"><div class="center-dot"></div>'
                    '<div class="orbiter"></div><div class="orbiter"></div>'
                    '<div class="orbiter"></div></div>', unsafe_allow_html=True)

    @staticmethod
    def render_upload_hint(file_type: str = "dataset") -> None:
        if file_type == "dataset":
            icon, title, tip = "📋", "Master Dataset", "CSV, Excel, JSON, Parquet or ODS"
        else:
            icon, title, tip = "📜", "Rules Configuration", "CSV/Excel rules sheet or JSON rulebook"
        beacon = UIComponents.render_beacon()
        st.markdown(f'<div class="action-hint-bar" style="margin-bottom:0.5rem;">'
                    f'<div class="ahb-beacon">{beacon}</div><div class="ahb-text">'
                    f'<strong>{icon} {title}</strong>&nbsp;'
                    f'<span class="hint-chip" style="font-size:0.72rem;padding:0.15rem 0.5rem;">'
                    f'{tip}</span></div></div>', unsafe_allow_html=True)

    @staticmethod
    def render_welcome_screen() -> None:
        st.info("👆 Please upload both Master Dataset and Rules Configuration to begin")

    @staticmethod
    def render_results_header(score: float) -> None:
        _inject_lottie_lib()
        UIComponents.render_workflow_tracker(active_step=4)
        color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 60 else "#ef4444")
        emoji = "🎉"      if score >= 80 else ("👍"      if score >= 60 else "⚠️")
        _, col_c, _ = st.columns([1, 1.2, 1])
        with col_c:
            UIComponents.render_lottie_success(f"{emoji} Score: {score:.1f}%")
        UIComponents.render_action_hint_bar(
            title="Assessment complete",
            message="Download your <strong>Excel report</strong> below or "
                    "continue to the <strong>Maturity Assessment →</strong>",
            color=color,
        )

    @staticmethod
    def render_workflow_tracker(active_step: int = 1) -> None:
        steps = [
            ("📤", "Upload Data"),
            ("📜", "Configure Rules"),
            ("🚀", "Run Assessment"),
            ("📊", "View Results"),
        ]
        html_steps = ""
        for i, (icon, label) in enumerate(steps, 1):
            active_cls = "active" if i == active_step else ""
            done_cls   = "done"   if i < active_step  else ""
            html_steps += (
                f'<div class="wf-step {active_cls} {done_cls}">'
                f'<div class="wf-step-icon">{icon}</div>'
                f'<div class="wf-step-label">{label}</div></div>'
            )
            if i < len(steps):
                html_steps += '<div class="wf-connector"></div>'
        st.markdown(f'<div class="workflow-tracker">{html_steps}</div>', unsafe_allow_html=True)