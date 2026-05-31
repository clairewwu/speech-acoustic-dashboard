import pandas as pd
import numpy as np
import streamlit as st


def generate_fake_data(n=500):
    np.random.seed(42)

    df = pd.DataFrame({
        "speaker_id": np.random.choice([f"S{i:02d}" for i in range(1, 21)], n),
        "word_id": np.random.choice([f"W{i:02d}" for i in range(1, 11)], n),
        "condition": np.random.choice(["baseline", "task"], n),
        "register": np.random.choice(["formal", "casual"], n),
        "group": np.random.choice(["Control", "Experimental"], n),
        "scale_score": np.random.randint(1, 8, n),
    })

    df["duration_ms"] = np.random.normal(280, 45, n)
    df["f0_mean"] = np.random.normal(210, 35, n)
    df["intensity_db"] = np.random.normal(68, 6, n)

    df.loc[df["condition"] == "task", "duration_ms"] += 20
    df.loc[df["condition"] == "task", "f0_mean"] += 18
    df.loc[df["register"] == "formal", "intensity_db"] += 3

    df["duration_ms"] += df["scale_score"] * 4
    df["f0_mean"] += df["scale_score"] * 2
    df.loc[df["group"] == "Experimental", "duration_ms"] += df["scale_score"] * 3

    speaker_effects = {
        speaker: np.random.normal(0, 15)
        for speaker in df["speaker_id"].unique()
    }
    df["duration_ms"] += df["speaker_id"].map(speaker_effects)

    fake_bad_idx = np.random.choice(df.index, size=3, replace=False)
    df.loc[fake_bad_idx, "duration_ms"] = -1

    return df


def load_data(uploaded_file):
    if uploaded_file is None:
        return generate_fake_data()

    file_name = uploaded_file.name.lower()

    try:
        if file_name.endswith(".csv"):
            return pd.read_csv(uploaded_file)
        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            return pd.read_excel(uploaded_file)
        else:
            st.error("只支援 CSV / Excel 檔案。")
            return None
    except Exception as e:
        st.error(f"讀取檔案失敗：{e}")
        return None


def get_numeric_cols(df):
    return df.select_dtypes(include=["number"]).columns.tolist()


def get_categorical_cols(df):
    return df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()


def safe_unique_values(series):
    values = series.dropna().unique().tolist()
    values = [str(v) for v in values]
    return sorted(values)


def get_random_candidates(df):
    candidates = []
    keywords = ["id", "speaker", "subject", "participant", "word", "item", "talker"]

    for col in df.columns:
        col_lower = col.lower()
        unique_count = df[col].nunique(dropna=True)

        is_categorical = (
            df[col].dtype == "object"
            or str(df[col].dtype) == "category"
            or df[col].dtype == "bool"
        )

        is_id_like = any(keyword in col_lower for keyword in keywords)
        is_repeated_group = unique_count >= 2 and unique_count < len(df) * 0.8

        if is_categorical or is_id_like or is_repeated_group:
            candidates.append(col)

    return candidates