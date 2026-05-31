import streamlit as st
import pandas as pd
from data_utils import safe_unique_values


def apply_global_filters(df):
    filtered_df = df.copy()

    st.sidebar.subheader("全域篩選")

    filter_candidates = [
        col for col in df.columns
        if df[col].nunique(dropna=True) <= 50
    ]

    selected_filter_cols = st.sidebar.multiselect(
        "選擇要篩選的欄位",
        filter_candidates,
        default=[]
    )

    for col in selected_filter_cols:
        values = safe_unique_values(filtered_df[col])

        selected_values = st.sidebar.multiselect(
            f"篩選 {col}",
            values,
            default=values
        )

        if selected_values:
            filtered_df = filtered_df[
                filtered_df[col].astype(str).isin(selected_values)
            ]

    return filtered_df


def show_sidebar_info(df, filtered_df, numeric_cols, categorical_cols):
    st.sidebar.subheader("資料資訊")
    st.sidebar.write(f"原始資料筆數：{len(df)}")
    st.sidebar.write(f"篩選後筆數：{len(filtered_df)}")
    st.sidebar.write(f"欄位數：{df.shape[1]}")
    st.sidebar.write(f"數值欄位：{len(numeric_cols)}")
    st.sidebar.write(f"類別欄位：{len(categorical_cols)}")


def is_fixed_continuous(df, fixed_col, fixed_as):
    if fixed_as == "Continuous":
        return True
    elif fixed_as == "Categorical":
        return False
    else:
        return pd.api.types.is_numeric_dtype(df[fixed_col])