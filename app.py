import streamlit as st

from data_utils import load_data, get_numeric_cols, get_categorical_cols, get_random_candidates
from ui_helpers import apply_global_filters, show_sidebar_info
from ui_sections import render_overview, render_explore, render_batch_mixedlm, render_portfolio


st.set_page_config(
    page_title="Speech Acoustic Dashboard",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Speech Acoustic Analysis Dashboard")

st.write(
    """
    這是一個語音聲學資料分析 Dashboard。  
    它包含資料檢查、互動式視覺化，以及批次 MixedLM 分析。
    """
)

uploaded_file = st.sidebar.file_uploader(
    "上傳 CSV 或 Excel",
    type=["csv", "xlsx", "xls"]
)

df = load_data(uploaded_file)

if df is None:
    st.stop()

if uploaded_file is None:
    st.sidebar.info("目前使用假資料展示。")

filtered_df = apply_global_filters(df)

if filtered_df.empty:
    st.error("目前篩選後沒有資料，請調整左側篩選條件。")
    st.stop()

numeric_cols = get_numeric_cols(filtered_df)
categorical_cols = get_categorical_cols(filtered_df)
random_candidates = get_random_candidates(filtered_df)

if len(numeric_cols) == 0:
    st.error("資料中需要至少一個數值欄位作為聲學特徵。")
    st.stop()

show_sidebar_info(df, filtered_df, numeric_cols, categorical_cols)

tab_overview, tab_explore, tab_batch, tab_portfolio = st.tabs([
    "Overview",
    "Explore Visualization",
    "Batch MixedLM",
    "Portfolio Notes"
])

with tab_overview:
    render_overview(filtered_df)

with tab_explore:
    render_explore(filtered_df, numeric_cols, categorical_cols)

with tab_batch:
    render_batch_mixedlm(
        filtered_df=filtered_df,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        random_candidates=random_candidates
    )

with tab_portfolio:
    render_portfolio()