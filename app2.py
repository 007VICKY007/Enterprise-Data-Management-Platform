# app_fixed.py
# Streamlit UI: Import Vendor Master -> DataFrame (first row headers) ->
# define duplicate criteria (Exact + Fuzzy) -> detect duplicates -> export vendor master + export duplicates
#
# Run:
#   pip install streamlit pandas openpyxl rapidfuzz
#   streamlit run app_fixed.py

from __future__ import annotations

import io
import re
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from rapidfuzz import fuzz


# --------------------------
# Page setup
# --------------------------
st.set_page_config(
    page_title="Data Quality Assessment || Master Data Objects",
    layout="wide",
)


# --------------------------
# Uniqus UI styling (CSS)
# Brand palette (Uniqus visual identity): Purple #44217A, Magenta #BF1C7D, Black #231F20
# --------------------------
def inject_uniqus_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root{
            --uni-purple: #44217A;
            --uni-magenta: #BF1C7D;
            --uni-black: #231F20;

            --uni-surface: rgba(255,255,255,0.82);
            --uni-border: rgba(35,31,32,0.12);
            --uni-muted: rgba(35,31,32,0.70);

            --uni-radius: 14px;
        }

        /* App base */
        .stApp{
            font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif !important;
            background:
              radial-gradient(900px circle at 8% 8%, rgba(68,33,122,0.10), transparent 45%),
              radial-gradient(900px circle at 92% 0%, rgba(191,28,125,0.08), transparent 45%),
              linear-gradient(180deg, rgba(35,31,32,0.02), rgba(35,31,32,0.00));
        }

        .block-container{
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        /* Sidebar */
        section[data-testid="stSidebar"]{
            border-right: 1px solid var(--uni-border);
            background: rgba(255,255,255,0.72);
            backdrop-filter: blur(10px);
        }
        section[data-testid="stSidebar"] .block-container{
            padding-top: 1.4rem;
        }

        /* Headings */
        h1,h2,h3{
            letter-spacing: -0.02em;
            color: var(--uni-black);
        }

        /* Tabs */
        button[data-baseweb="tab"]{
            font-weight: 700;
        }
        button[data-baseweb="tab"][aria-selected="true"]{
            color: var(--uni-magenta) !important;
        }

        /* Inputs */
        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div,
        div[data-testid="stMultiSelect"] div,
        div[data-testid="stTextArea"] textarea{
            border-radius: 12px !important;
            border: 1px solid var(--uni-border) !important;
            background: rgba(255,255,255,0.9) !important;
        }

        /* Buttons */
        div.stButton > button{
            border-radius: 12px;
            padding: 0.6rem 0.95rem;
            font-weight: 800;
            border: 0;
            color: #fff;
            background: linear-gradient(90deg, var(--uni-purple), var(--uni-magenta));
            box-shadow: 0 10px 24px rgba(35,31,32,0.12);
            transition: transform 0.06s ease-in-out, filter 0.12s ease-in-out;
        }
        div.stButton > button:hover{
            transform: translateY(-1px);
            filter: brightness(1.02);
        }
        div.stButton > button:active{
            transform: translateY(0px);
            filter: brightness(0.98);
        }

        /* DataFrame container */
        div[data-testid="stDataFrame"]{
            border-radius: var(--uni-radius);
            overflow: hidden;
            border: 1px solid var(--uni-border);
            box-shadow: 0 10px 24px rgba(35,31,32,0.06);
        }

        /* Expanders */
        div[data-testid="stExpander"]{
            border-radius: var(--uni-radius);
            border: 1px solid var(--uni-border);
            background: var(--uni-surface);
        }

        /* Alerts */
        div[data-testid="stAlert"]{
            border-radius: var(--uni-radius);
            border: 1px solid var(--uni-border);
        }

        /* Utility cards (optional) */
        .uni-card{
            border: 1px solid var(--uni-border);
            background: var(--uni-surface);
            border-radius: var(--uni-radius);
            padding: 16px 18px;
            box-shadow: 0 10px 24px rgba(35,31,32,0.06);
            margin-bottom: 12px;
        }
        .uni-card-title{
            font-weight: 800;
            font-size: 1.05rem;
            margin: 0 0 4px 0;
        }
        .uni-card-subtitle{
            color: var(--uni-muted);
            font-size: 0.92rem;
            margin: 0;
        }

        /* Hide Streamlit chrome */
        #MainMenu{visibility:hidden;}
        footer{visibility:hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_uniqus_css()


st.title("Data Quality Assessment || Master Data Objects")
st.markdown(
    "Upload a **CSV/Excel for Master Data**. The app will create a DataFrame using the **first row as headers**, "
    "let you define **Exact** and **Fuzzy** duplicate rules (including column combinations), identify duplicates, "
    "and export both the full Master Data and duplicates."
)

# --------------------------
# Upload -> DataFrame
# --------------------------
uploaded = st.file_uploader(
    "Upload Master Data (CSV / XLSX / XLS)",
    type=["csv", "xlsx", "xls"],
)

if not uploaded:
    st.stop()

try:
    if uploaded.name.lower().endswith(".csv"):
        df = pd.read_csv(uploaded, header=0)  # first row as headers
    else:
        df = pd.read_excel(uploaded, header=0)  # first row as headers
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

df = df.copy().reset_index(drop=True)

drop_empty = st.checkbox("Drop fully empty rows/columns", value=True)
if drop_empty:
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")

st.subheader("File summary")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Rows", f"{len(df):,}")
with c2:
    st.metric("Columns", f"{len(df.columns):,}")
with c3:
    st.metric("File", uploaded.name)

st.subheader("Preview (first 50 rows)")
st.dataframe(df.head(50), use_container_width=True, height=520)

all_cols = df.columns.tolist()
text_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()

# --------------------------
# Standardization (helps both exact + fuzzy)
# --------------------------
st.subheader("Standardization (recommended)")
sc1, sc2, sc3, sc4 = st.columns(4)
with sc1:
    trim_spaces = st.checkbox("Trim spaces", value=True)
with sc2:
    lowercase_text = st.checkbox("Lowercase text columns", value=True)
with sc3:
    blanks_as_null = st.checkbox("Treat blanks as NULL", value=True)
with sc4:
    remove_punct = st.checkbox("Remove punctuation (fuzzy helper)", value=True)


def normalize_cell(
    x: Any,
    do_lower: bool,
    do_trim: bool,
    do_blank_null: bool,
    do_remove_punct: bool,
) -> Any:
    if pd.isna(x):
        return pd.NA
    s = str(x)
    if do_trim:
        s = s.strip()
    if do_lower:
        s = s.lower()
    if do_remove_punct:
        # keep letters/numbers/spaces/@/./-/+ (email-ish friendly)
        s = re.sub(r"[^\w\s@.+-]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
    if do_blank_null and s == "":
        return pd.NA
    return s


df_std = df.copy()
if text_cols:
    for col in text_cols:
        df_std[col] = df_std[col].apply(
            lambda v: normalize_cell(
                v,
                lowercase_text,
                trim_spaces,
                blanks_as_null,
                remove_punct,
            )
        )

# --------------------------
# --------------------------
# Data completeness checks
# --------------------------
st.subheader("Data completeness (missing / NULL checks)")
st.caption(
    "Select fields that must be populated. The app will flag rows where the selected fields are NULL/blank "
    "(based on the standardization settings above) and lets you export exceptions with one sheet per field."
)

if "comp_fields" not in st.session_state:
    st.session_state["comp_fields"] = []
if "comp_exceptions" not in st.session_state:
    st.session_state["comp_exceptions"] = {}  # field -> exception df
if "comp_summary" not in st.session_state:
    st.session_state["comp_summary"] = pd.DataFrame()

comp_fields = st.multiselect(
    "Fields to check for missing values",
    options=all_cols,
    default=st.session_state.get("comp_fields", []),
    key="comp_fields",
)

def _safe_sheet_name(name: str, used: set[str]) -> str:
    # Excel sheet name constraints: <=31 chars, cannot contain : \ / ? * [ ]
    cleaned = re.sub(r"[:\\/\?\*\[\]]", "_", str(name)).strip()
    cleaned = cleaned[:31] if cleaned else "Sheet"
    base = cleaned
    k = 1
    while cleaned in used:
        suffix = f"_{k}"
        cleaned = (base[: (31 - len(suffix))] + suffix) if len(base) + len(suffix) > 31 else base + suffix
        k += 1
    used.add(cleaned)
    return cleaned

def run_completeness_checks(df_raw: pd.DataFrame, df_norm: pd.DataFrame, fields: list[str]) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    exceptions: dict[str, pd.DataFrame] = {}
    summary_rows = []

    for f in fields:
        if f not in df_norm.columns:
            continue
        miss_mask = df_norm[f].isna()
        ex = df_raw.loc[miss_mask].copy()
        if ex.empty:
            continue
        ex.insert(0, "_row_id", ex.index + 1)  # 1-based row id (after read/reset)
        ex.insert(1, "_missing_field", f)
        ex.insert(2, "_issue", "Missing/NULL value")
        exceptions[f] = ex.reset_index(drop=True)
        summary_rows.append({"field": f, "missing_rows": int(miss_mask.sum())})

    summary = pd.DataFrame(summary_rows).sort_values("missing_rows", ascending=False) if summary_rows else pd.DataFrame(columns=["field", "missing_rows"])
    return exceptions, summary

run_comp = st.button(
    "Run completeness checks",
    type="secondary",
    disabled=not bool(comp_fields),
    key="btn_run_completeness",
)

if run_comp:
    comp_ex, comp_sum = run_completeness_checks(df, df_std, comp_fields)
    st.session_state["comp_exceptions"] = comp_ex
    st.session_state["comp_summary"] = comp_sum

    if comp_sum.empty:
        st.success("No missing values found for the selected fields.")
    else:
        st.subheader("Completeness summary")
        st.dataframe(comp_sum, use_container_width=True)

        with st.expander("Preview missing-value exceptions"):
            for f, exdf in comp_ex.items():
                st.markdown(f"**{f}** — {len(exdf):,} rows missing")
                st.dataframe(exdf.head(50), use_container_width=True, height=280)

# Duplicate rules state
# --------------------------
if "dup_rules" not in st.session_state:
    st.session_state.dup_rules = []  # list[dict]

# --------------------------
# Rule Builder UI (Exact + Fuzzy)
# --------------------------
st.subheader("Duplicate criteria builder")
tab_exact, tab_fuzzy = st.tabs(["Add Exact Rule", "Add Fuzzy Rule"])

# ----- Exact Rule -----
with tab_exact:
    st.caption(
        "Exact match on one or more columns (combination). Example: VendorName + City + Country"
    )
    exact_cols = st.multiselect("Exact rule columns", options=all_cols, default=[])
    exact_name_default = (
        "EXACT: " + " + ".join(exact_cols) if exact_cols else "EXACT: Rule"
    )
    exact_rule_name = st.text_input(
        "Exact rule name",
        value=exact_name_default,
        key="exact_rule_name",
    )
    exact_ignore_nulls = st.checkbox(
        "Ignore rows where ANY selected field is NULL/blank (exact)",
        value=True,
        key="exact_ignore_nulls",
    )

    if st.button("Add Exact Rule", key="btn_add_exact"):
        if not exact_cols:
            st.warning("Please select at least one column for the exact rule.")
        else:
            st.session_state.dup_rules.append(
                {
                    "type": "exact",
                    "name": exact_rule_name.strip() or exact_name_default,
                    "cols": list(exact_cols),
                    "ignore_nulls": bool(exact_ignore_nulls),
                }
            )
            st.success("Exact rule added.")

# ----- Fuzzy Rule -----
with tab_fuzzy:
    st.caption(
        "Fuzzy match compares text similarity. Choose 1+ columns, set a threshold (%), and optional weights.\n\n"
        "Tip: Use Vendor Name and Address fields for fuzzy matching."
    )

    if not text_cols:
        st.warning(
            "No text columns detected in your file. Fuzzy rules work best with text columns."
        )

    fuzzy_cols = st.multiselect(
        "Fuzzy rule columns (text)",
        options=all_cols,
        default=[],
    )
    fuzzy_name_default = (
        "FUZZY: " + " + ".join(fuzzy_cols) if fuzzy_cols else "FUZZY: Rule"
    )
    fuzzy_rule_name = st.text_input(
        "Fuzzy rule name",
        value=fuzzy_name_default,
        key="fuzzy_rule_name",
    )

    threshold = st.slider(
        "Fuzzy match threshold (%)",
        min_value=60,
        max_value=99,
        value=88,
        step=1,
    )
    fuzzy_ignore_nulls = st.checkbox(
        "Ignore rows where ANY selected field is NULL/blank (fuzzy)",
        value=True,
        key="fuzzy_ignore_nulls",
    )

    st.markdown("**Weights (optional)** — used when multiple columns are selected.")
    w_total_help = "Weights are normalized internally; they don't need to sum to 100."
    wc1, wc2 = st.columns(2)
    with wc1:
        w1 = st.number_input(
            "Weight for column 1",
            min_value=0.0,
            value=1.0,
            step=0.5,
            help=w_total_help,
        )
        w3 = st.number_input(
            "Weight for column 3",
            min_value=0.0,
            value=1.0,
            step=0.5,
            help=w_total_help,
        )
    with wc2:
        w2 = st.number_input(
            "Weight for column 2",
            min_value=0.0,
            value=1.0,
            step=0.5,
            help=w_total_help,
        )
        w4 = st.number_input(
            "Weight for column 4",
            min_value=0.0,
            value=1.0,
            step=0.5,
            help=w_total_help,
        )

    if st.button("Add Fuzzy Rule", key="btn_add_fuzzy"):
        if not fuzzy_cols:
            st.warning("Please select at least one column for the fuzzy rule.")
        else:
            default_weights = [w1, w2, w3, w4] + [1.0] * max(0, len(fuzzy_cols) - 4)
            weights = default_weights[: len(fuzzy_cols)]

            st.session_state.dup_rules.append(
                {
                    "type": "fuzzy",
                    "name": fuzzy_rule_name.strip() or fuzzy_name_default,
                    "cols": list(fuzzy_cols),
                    "ignore_nulls": bool(fuzzy_ignore_nulls),
                    "threshold": int(threshold),
                    "weights": weights,  # aligned to cols order
                    "algorithm": "token_set_ratio",
                }
            )
            st.success("Fuzzy rule added.")

# Show current rules
st.write("### Current duplicate rules")
if not st.session_state.dup_rules:
    st.info("No rules added yet. Add at least one rule to run duplicate detection.")
else:
    st.dataframe(pd.DataFrame(st.session_state.dup_rules), use_container_width=True)

rc1, rc2 = st.columns([1, 6])
with rc1:
    if st.session_state.dup_rules and st.button("Clear all rules", key="btn_clear_rules"):
        st.session_state.dup_rules = []
        st.rerun()

# --------------------------
# Duplicate engines
# --------------------------
def build_exact_key(df_in: pd.DataFrame, cols: List[str]) -> pd.Series:
    tmp = df_in[cols].astype("string").fillna("<NULL>")
    return tmp.agg("␟".join, axis=1)


def find_duplicates_exact(df_in: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
    cols = rule["cols"]
    work = df_in.copy()

    if rule.get("ignore_nulls", True):
        work = work[work[cols].notna().all(axis=1)].copy()

    if work.empty:
        return pd.DataFrame()

    work["_dup_key"] = build_exact_key(work, cols)
    dmask = work.duplicated(subset=["_dup_key"], keep=False)
    dups = work[dmask].copy()

    if dups.empty:
        return pd.DataFrame()

    dups["_group_id"] = dups.groupby("_dup_key").ngroup() + 1
    dups["_group_size"] = dups.groupby("_group_id")["_group_id"].transform("size")
    dups["_rule"] = rule["name"]
    dups["_match_type"] = "EXACT"
    dups["_match_cols"] = ", ".join(cols)
    dups["_score"] = 100

    meta = ["_rule", "_match_type", "_match_cols", "_group_id", "_group_size", "_score"]
    ordered = meta + [c for c in dups.columns if c not in meta]
    return dups[ordered]


def fuzzy_score_rowpair(
    a: pd.Series,
    b: pd.Series,
    cols: List[str],
    weights: List[float],
) -> int:
    sims: List[int] = []
    wts: List[float] = []
    for col, w in zip(cols, weights):
        if w <= 0:
            continue
        av = a.get(col, pd.NA)
        bv = b.get(col, pd.NA)
        if pd.isna(av) or pd.isna(bv):
            sim = 0
        else:
            sim = fuzz.token_set_ratio(str(av), str(bv))
        sims.append(sim)
        wts.append(w)

    if not wts:
        return 0

    return int(round(sum(s * w for s, w in zip(sims, wts)) / sum(wts)))


def find_duplicates_fuzzy(df_in: pd.DataFrame, rule: Dict[str, Any]) -> pd.DataFrame:
    """
    MVP fuzzy approach:
    - Create 'blocks' to avoid O(n^2) across full dataset.
    - Compare pairs within each block using RapidFuzz token_set_ratio.
    - Build groups using union-find over matched pairs.

    Blocking key:
    - first character of first fuzzy column
    - plus first 3 chars of City/Country if present (helps reduce comparisons)
    """
    cols = rule["cols"]
    if not cols:
        return pd.DataFrame()

    threshold = int(rule["threshold"])
    weights = rule.get("weights", [1.0] * len(cols))

    work = df_in.copy()
    if rule.get("ignore_nulls", True):
        work = work[work[cols].notna().all(axis=1)].copy()

    if work.empty:
        return pd.DataFrame()

    # Basic blocking key: first char of first selected col
    first_col = cols[0]
    work["_block"] = work[first_col].astype("string").fillna("").str[:1]

    # Optional: add geo info into block
    for geo_col in ["Country", "country", "CITY", "City", "city"]:
        if geo_col in work.columns:
            work["_block"] = work["_block"] + "|" + work[geo_col].astype("string").fillna("").str[:3]
            break

    matches: List[Dict[str, Any]] = []
    max_pairs_per_block = int(st.session_state.get("max_pairs_per_block", 20000))

    # Compare within each block
    for _, g in work[work["_block"] != ""].groupby("_block"):
        idxs = list(g.index)
        n = len(idxs)

        # safety cap: skip overly-large blocks
        if n * (n - 1) // 2 > max_pairs_per_block:
            continue

        for i_pos in range(n):
            for j_pos in range(i_pos + 1, n):
                i = idxs[i_pos]
                j = idxs[j_pos]
                a = work.loc[i]
                b = work.loc[j]

                score = fuzzy_score_rowpair(a, b, cols, weights)
                if score >= threshold:
                    matches.append({"_i": i, "_j": j, "_score": score})

    if not matches:
        return pd.DataFrame()

    pair_df = pd.DataFrame(matches).sort_values("_score", ascending=False)

    # Union-find to form groups
    parent: Dict[int, int] = {}

    def uf_find(x: int) -> int:
        parent.setdefault(x, x)
        if parent[x] != x:
            parent[x] = uf_find(parent[x])
        return parent[x]

    def uf_union(x: int, y: int) -> None:
        rx, ry = uf_find(x), uf_find(y)
        if rx != ry:
            parent[ry] = rx

    # Use Series access to avoid pandas itertuples() renaming issues (especially with leading underscores)
    for i, j in zip(pair_df["_i"].astype(int).tolist(), pair_df["_j"].astype(int).tolist()):
        uf_union(int(i), int(j))

    members: Dict[int, List[int]] = {}
    for idx in set(pair_df["_i"]).union(set(pair_df["_j"])):
        root = uf_find(int(idx))
        members.setdefault(root, []).append(int(idx))

    # All rows belonging to any fuzzy group (size >=2)
    out_rows = []
    group_num = 0
    for _, idx_list in members.items():
        if len(idx_list) < 2:
            continue
        group_num += 1
        group = work.loc[idx_list].copy()
        group["_group_id"] = group_num
        group["_group_size"] = len(idx_list)
        group["_rule"] = rule["name"]
        group["_match_type"] = "FUZZY"
        group["_match_cols"] = ", ".join(cols)

        group_pairs = pair_df[(pair_df["_i"].isin(idx_list)) & (pair_df["_j"].isin(idx_list))]
        group["_score"] = int(group_pairs["_score"].max()) if not group_pairs.empty else threshold
        out_rows.append(group)

    if not out_rows:
        return pd.DataFrame()

    dups = pd.concat(out_rows, ignore_index=True)
    meta = ["_rule", "_match_type", "_match_cols", "_group_id", "_group_size", "_score"]
    ordered = meta + [c for c in dups.columns if c not in meta]
    return dups[ordered]


# --------------------------
# Run duplicate detection
# --------------------------
st.subheader("Run duplicate detection")

with st.expander("Fuzzy performance settings (optional)"):
    st.caption(
        "If your dataset is large, fuzzy matching can be heavy. "
        "Blocking reduces comparisons per block."
    )
    st.session_state["max_pairs_per_block"] = st.number_input(
        "Max pairwise comparisons per block (skip blocks beyond this)",
        min_value=1000,
        max_value=200000,
        value=20000,
        step=1000,
    )

run_btn = st.button(
    "Run duplicates",
    type="primary",
    disabled=not bool(st.session_state.dup_rules),
    key="btn_run_dups",
)

if run_btn:
    results = []
    for rule in st.session_state.dup_rules:
        if rule["type"] == "exact":
            out = find_duplicates_exact(df_std, rule)
        else:
            out = find_duplicates_fuzzy(df_std, rule)

        if out is not None and not out.empty:
            results.append(out)

    if not results:
        st.success("No duplicates found for the configured rules.")
        st.session_state["dup_df"] = pd.DataFrame()
        st.session_state["dup_summary"] = pd.DataFrame()
    else:
        dup_df = pd.concat(results, ignore_index=True)

        summary = (
            dup_df.groupby(["_rule", "_match_type", "_match_cols"])
            .agg(
                duplicate_rows=("_group_id", "size"),
                duplicate_groups=("_group_id", "nunique"),
                max_score=("_score", "max"),
                min_score=("_score", "min"),
            )
            .reset_index()
            .sort_values(["duplicate_groups", "duplicate_rows"], ascending=False)
        )

        st.session_state["dup_df"] = dup_df
        st.session_state["dup_summary"] = summary

        st.subheader("Duplicate summary")
        st.dataframe(summary, use_container_width=True)

        st.subheader("Duplicate records (all members)")
        st.dataframe(dup_df, use_container_width=True, height=520)

# --------------------------
# Export buttons
# --------------------------
st.subheader("Export")

base_name = uploaded.name.rsplit(".", 1)[0]
default_vendor_export = f"{base_name}_export.xlsx"
default_dups_export = f"{base_name}_duplicates.xlsx"
default_fuzzy_export = f"{base_name}_fuzzy_duplicates.xlsx"

dup_df = st.session_state.get("dup_df", pd.DataFrame())
dup_summary = st.session_state.get("dup_summary", pd.DataFrame())

colA, colB, colC, colD = st.columns(4)

with colA:
    st.markdown("#### Export Vendor Master")
    vendor_export_name = st.text_input(
        "Vendor Master export filename",
        value=default_vendor_export,
        key="vendor_export_name",
    )

    vendor_buf = io.BytesIO()
    with pd.ExcelWriter(vendor_buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="VendorMaster")
    vendor_buf.seek(0)

    st.download_button(
        label="Download Vendor Master (Excel)",
        data=vendor_buf,
        file_name=vendor_export_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with colB:
    st.markdown("#### Export All Duplicates (Exact + Fuzzy)")
    dups_export_name = st.text_input(
        "All duplicates export filename",
        value=default_dups_export,
        key="dups_export_name",
    )

    if dup_df is None or dup_df.empty:
        st.info("Run duplicates first to enable export.")
    else:
        dup_buf = io.BytesIO()
        with pd.ExcelWriter(dup_buf, engine="openpyxl") as writer:
            dup_summary.to_excel(writer, index=False, sheet_name="Summary")
            dup_df.to_excel(writer, index=False, sheet_name="Duplicates")
        dup_buf.seek(0)

        st.download_button(
            label="Download All Duplicates (Excel)",
            data=dup_buf,
            file_name=dups_export_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

with colC:
    st.markdown("#### Export Fuzzy Duplicates Only")
    fuzzy_export_name = st.text_input(
        "Fuzzy duplicates export filename",
        value=default_fuzzy_export,
        key="fuzzy_export_name",
    )

    if dup_df is None or dup_df.empty:
        st.info("Run duplicates first to enable export.")
    else:
        fuzzy_only = dup_df[dup_df["_match_type"] == "FUZZY"].copy()
        if fuzzy_only.empty:
            st.info("No fuzzy duplicates found to export.")
        else:
            fuzzy_summary = (
                fuzzy_only.groupby(["_rule", "_match_cols"])
                .agg(
                    duplicate_rows=("_group_id", "size"),
                    duplicate_groups=("_group_id", "nunique"),
                    max_score=("_score", "max"),
                    min_score=("_score", "min"),
                )
                .reset_index()
                .sort_values(["duplicate_groups", "duplicate_rows"], ascending=False)
            )

            fuzzy_buf = io.BytesIO()
            with pd.ExcelWriter(fuzzy_buf, engine="openpyxl") as writer:
                fuzzy_summary.to_excel(writer, index=False, sheet_name="Summary")
                fuzzy_only.to_excel(writer, index=False, sheet_name="FuzzyDuplicates")
            fuzzy_buf.seek(0)

            st.download_button(
                label="Download Fuzzy Duplicates (Excel)",
                data=fuzzy_buf,
                file_name=fuzzy_export_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
with colD:
    st.markdown("#### Export Completeness Exceptions")
    completeness_export_name = st.text_input(
        "Completeness export filename",
        value=f"{base_name}_completeness_exceptions.xlsx",
        key="completeness_export_name",
    )

    comp_exceptions = st.session_state.get("comp_exceptions", {})
    comp_summary_df = st.session_state.get("comp_summary", pd.DataFrame())

    if not comp_fields:
        st.info("Select fields under **Data completeness** to enable this export.")
    elif not comp_exceptions:
        st.info("Run completeness checks first to enable export.")
    else:
        comp_buf = io.BytesIO()
        with pd.ExcelWriter(comp_buf, engine="openpyxl") as writer:
            # Summary
            if comp_summary_df is None or comp_summary_df.empty:
                pd.DataFrame(columns=["field", "missing_rows"]).to_excel(writer, index=False, sheet_name="Summary")
            else:
                comp_summary_df.to_excel(writer, index=False, sheet_name="Summary")

            used_sheet_names: set[str] = set(["Summary"])
            for field, exdf in comp_exceptions.items():
                sheet = _safe_sheet_name(f"Missing_{field}", used_sheet_names)
                exdf.to_excel(writer, index=False, sheet_name=sheet)

        comp_buf.seek(0)

        st.download_button(
            label="Download Completeness Exceptions (Excel)",
            data=comp_buf,
            file_name=completeness_export_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
