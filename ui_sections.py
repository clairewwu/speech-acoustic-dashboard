# ui_sections.py

import streamlit as st
import pandas as pd

from plot_utils import (
    make_summary_table,
    make_chart,
    make_interaction_plot,
    make_plotly_trend_plot,
    auto_visual_insight,
)

from model_utils import run_batch_mixedlm

from export_utils import (
    to_excel_bytes,
    figs_to_zip,
)

from ui_helpers import is_fixed_continuous


# ======================================================
# Overview Tab
# ======================================================
def render_overview(filtered_df):
    st.header("Overview")

    st.subheader("目前篩選後資料預覽")
    st.dataframe(filtered_df.head(10), use_container_width=True)

    st.subheader("欄位型態與資料品質檢查")

    missing_counts = filtered_df.isna().sum()
    minus_one_counts = {}

    for col in filtered_df.columns:
        if pd.api.types.is_numeric_dtype(filtered_df[col]):
            minus_one_counts[col] = int((filtered_df[col] == -1).sum())
        else:
            minus_one_counts[col] = 0

    dtype_df = pd.DataFrame({
        "column": filtered_df.columns,
        "dtype": filtered_df.dtypes.astype(str),
        "unique_values": [
            filtered_df[col].nunique(dropna=True)
            for col in filtered_df.columns
        ],
        "missing_count": [
            int(missing_counts[col])
            for col in filtered_df.columns
        ],
        "missing_percentage": [
            round(missing_counts[col] / len(filtered_df) * 100, 2)
            for col in filtered_df.columns
        ],
        "minus_one_count": [
            minus_one_counts[col]
            for col in filtered_df.columns
        ],
    })

    st.dataframe(dtype_df, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("缺失值檢查")
        missing_df = dtype_df[dtype_df["missing_count"] > 0]

        if missing_df.empty:
            st.success("目前篩選後資料沒有缺失值。")
        else:
            st.warning("以下欄位有缺失值：")
            st.dataframe(
                missing_df[["column", "missing_count", "missing_percentage"]],
                use_container_width=True,
            )

    with c2:
        st.subheader("數值欄位 `-1` 檢查")
        minus_one_df = dtype_df[dtype_df["minus_one_count"] > 0]

        if minus_one_df.empty:
            st.success("目前篩選後資料沒有偵測到 -1。")
        else:
            st.warning("以下數值欄位含有 -1，可能需要確認是否為缺失值編碼或異常值：")
            st.dataframe(
                minus_one_df[["column", "minus_one_count"]],
                use_container_width=True,
            )

    st.subheader("欄位獨立值檢查，依目前篩選後資料")

    selected_unique_col = st.selectbox(
        "選擇欄位查看獨立值",
        filtered_df.columns.tolist(),
        key="overview_unique_col",
    )

    unique_values = filtered_df[selected_unique_col].dropna().unique().tolist()
    unique_values = sorted([str(v) for v in unique_values])

    st.write(
        f"欄位 **{selected_unique_col}** "
        f"共有 **{len(unique_values)}** 個非空獨立值。"
    )

    unique_display_df = pd.DataFrame({
        "unique_value": unique_values
    })

    st.dataframe(unique_display_df, use_container_width=True)

    st.subheader("專案邏輯")
    st.markdown(
        """
        這個 Dashboard 分成兩個主要功能：

        1. **Explore Visualization**  
           用來選擇一個 Y、一個 X，以及可選的 hue，快速查看資料趨勢。

        2. **Batch MixedLM**  
           用來選擇多個 Y，並對每個 Y 批次執行相同模型設定。  
           如果 fixed effect 是量表或連續數值，可使用 Plotly 迴歸趨勢圖查看不同 moderator 條件下的斜率趨勢。
        """
    )


# ======================================================
# Explore Visualization Tab
# ======================================================
def render_explore(filtered_df, numeric_cols, categorical_cols):
    st.header("Explore Visualization")

    st.write(
        """
        這一頁用來互動式看圖。  
        你可以一次選一個聲學特徵，搭配不同 X 軸與 hue 觀察趨勢。
        """
    )

    chart_type = st.selectbox(
        "選擇圖表類型",
        ["Boxplot", "Violin", "Barplot", "Lineplot", "Scatterplot"],
        key="chart_type",
    )

    if chart_type == "Scatterplot":
        x_options = numeric_cols
    else:
        x_options = categorical_cols + numeric_cols

    hue_options = ["None"] + categorical_cols

    c1, c2, c3 = st.columns(3)

    with c1:
        x_col = st.selectbox(
            "X 軸變因",
            x_options,
            key="explore_x",
        )

    with c2:
        y_col = st.selectbox(
            "Y 軸聲學特徵",
            numeric_cols,
            key="explore_y",
        )

    with c3:
        hue_col = st.selectbox(
            "Hue 分組",
            hue_options,
            key="explore_hue",
        )

    fig = make_chart(
        filtered_df,
        chart_type,
        x_col,
        y_col,
        hue_col,
    )

    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("摘要表")

    try:
        summary = make_summary_table(
            filtered_df,
            x_col,
            y_col,
            hue_col,
        )

        st.dataframe(summary, use_container_width=True)

        st.subheader("自動觀察")
        st.markdown(auto_visual_insight(summary, x_col, y_col))

    except Exception as e:
        st.warning(f"摘要表產生失敗：{e}")


# ======================================================
# Batch MixedLM Tab
# ======================================================
def render_batch_mixedlm(
    filtered_df,
    numeric_cols,
    categorical_cols,
    random_candidates,
):
    st.header("Batch MixedLM")

    st.write(
        """
        這一頁用來批次跑 MixedLM。  
        你可以選多個 Y 變項，系統會對每個 Y 套用同一組 fixed effect 與 random intercept。
        若 fixed effect 是量表/連續數值且有 moderator，系統會使用 Plotly 迴歸趨勢圖顯示斜率趨勢。
        """
    )

    if len(random_candidates) == 0:
        st.error(
            "找不到適合當 random intercept 的欄位。"
            "請確認是否有 speaker_id、subject_id、word_id 或 item_id。"
        )
        st.stop()

    c1, c2 = st.columns(2)

    with c1:
        y_cols = st.multiselect(
            "選擇多個 Y 變項，也就是 acoustic outcomes",
            numeric_cols,
            default=numeric_cols[: min(3, len(numeric_cols))],
            key="batch_y_cols",
        )

        fixed_options = [
            col for col in filtered_df.columns
            if col not in y_cols
        ]

        fixed_col = st.selectbox(
            "選擇 fixed effect",
            fixed_options,
            key="batch_fixed",
        )

        fixed_as = st.radio(
            "Fixed effect 要怎麼處理？",
            ["Auto", "Continuous", "Categorical"],
            horizontal=True,
            index=0,
            key="batch_fixed_as",
        )

    with c2:
        random_options = [
            col for col in random_candidates
            if col not in y_cols and col != fixed_col
        ]

        if len(random_options) == 0:
            st.warning("目前沒有可用的 random intercept 欄位。請調整 Y 或 fixed effect。")
            st.stop()

        random_col = st.selectbox(
            "選擇 random intercept，例如 speaker_id、word_id、item_id",
            random_options,
            key="batch_random",
        )

        moderator_options = ["None"] + [
            col for col in categorical_cols
            if col not in y_cols
            and col != fixed_col
            and col != random_col
        ]

        moderator_col = st.selectbox(
            "選擇 moderator / interaction variable，可不選",
            moderator_options,
            key="batch_moderator",
        )

    fixed_is_continuous = is_fixed_continuous(
        filtered_df,
        fixed_col,
        fixed_as,
    )

    st.subheader("目前模型設定")

    if moderator_col == "None":
        st.code(
            f"""
For each outcome in {y_cols}:
    outcome ~ {fixed_col} + (1 | {random_col})

Fixed effect mode: {fixed_as}
            """,
            language="text",
        )
    else:
        st.code(
            f"""
For each outcome in {y_cols}:
    outcome ~ {fixed_col} * {moderator_col} + (1 | {random_col})

Fixed effect mode: {fixed_as}
            """,
            language="text",
        )

    st.info(
        """
        解讀提示：
        - `Intercept`：基準組的預測平均。
        - `Main effect: fixed`：fixed effect 的效果。若 fixed 是連續量表，coef 表示每增加 1 分，Y 平均改變多少。
        - `Main effect: moderator`：moderator 相對於基準組的差異。
        - `Two-way interaction`：fixed × moderator 的交互作用。
        - 若 fixed 是量表/連續數值，交互作用可理解為不同 moderator 組別的斜率是否不同。
        """
    )

    st.warning(
        """
        MixedLM 比一般圖表或 t-test 更容易失敗。  
        如果模型失敗，建議先把 moderator 改成 None，或將 fixed effect mode 改成 Auto / Categorical / Continuous 測試。
        """
    )

    if st.button("Run Batch MixedLM", key="run_batch_mixedlm"):
        if len(y_cols) == 0:
            st.warning("請至少選擇一個 Y 變項。")
            return

        with st.spinner("正在批次執行 MixedLM..."):
            coef_df, status_df = run_batch_mixedlm(
                df=filtered_df,
                y_cols=y_cols,
                fixed_col=fixed_col,
                random_col=random_col,
                moderator_col=moderator_col,
                fixed_as=fixed_as,
            )

        st.subheader("模型執行狀態")
        st.dataframe(status_df, use_container_width=True)

        if coef_df.empty:
            st.error(
                "沒有任何模型成功。請簡化模型，例如拿掉 moderator、"
                "調整 fixed effect mode，或更換 random intercept。"
            )
            return

        st.subheader("Fixed Effects 結果總表")
        st.dataframe(coef_df, use_container_width=True)

        st.subheader("顯著結果")

        sig_df = coef_df[
            (coef_df["p_value"] < 0.05)
            & (coef_df["term"] != "Intercept")
        ]

        if sig_df.empty:
            st.info("目前沒有非截距項達到 p < .05。")
        else:
            st.dataframe(sig_df, use_container_width=True)

        st.download_button(
            label="下載 Batch MixedLM 結果 Excel",
            data=to_excel_bytes(coef_df, status_df),
            file_name="batch_mixedlm_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        render_batch_plots(
            filtered_df=filtered_df,
            y_cols=y_cols,
            fixed_col=fixed_col,
            moderator_col=moderator_col,
            fixed_is_continuous=fixed_is_continuous,
        )

        render_auto_interpretation(
            sig_df=sig_df,
            random_col=random_col,
            fixed_col=fixed_col,
        )


# ======================================================
# Batch Plot Subsection
# ======================================================
def render_batch_plots(
    filtered_df,
    y_cols,
    fixed_col,
    moderator_col,
    fixed_is_continuous,
):
    if moderator_col == "None":
        st.info("若要產生交互作用 / 趨勢圖，請選擇 moderator。")
        return

    st.subheader("批次交互作用 / 趨勢圖")

    if fixed_is_continuous:
        render_continuous_trend_plots(
            filtered_df=filtered_df,
            y_cols=y_cols,
            fixed_col=fixed_col,
            moderator_col=moderator_col,
        )
    else:
        render_categorical_interaction_plots(
            filtered_df=filtered_df,
            y_cols=y_cols,
            fixed_col=fixed_col,
            moderator_col=moderator_col,
        )


def render_continuous_trend_plots(
    filtered_df,
    y_cols,
    fixed_col,
    moderator_col,
):
    st.info(
        f"""
        目前 fixed effect `{fixed_col}` 被視為連續/量表變項，因此使用 **Plotly 迴歸趨勢圖**。
        這適合量表分數、時間、年齡、trial order 等數值 X，
        可用來觀察不同 moderator 組別的斜率差異。
        """
    )

    trend_fig_dict = {}

    for y in y_cols:
        try:
            trend_fig, trend_result = make_plotly_trend_plot(
                filtered_df,
                y_col=y,
                x_col=fixed_col,
                hue_col=moderator_col,
            )

            if trend_fig is None:
                st.warning(f"{y} 的趨勢圖產生失敗：{trend_result}")
                continue

            fig_name = f"trend_{y}_{fixed_col}_by_{moderator_col}"
            trend_fig_dict[fig_name] = trend_fig

            st.markdown(f"### {y}: {fixed_col} × {moderator_col}")
            st.plotly_chart(trend_fig, use_container_width=True)

            st.download_button(
                label=f"下載 {y} 趨勢圖 HTML",
                data=trend_fig.to_html(include_plotlyjs="cdn"),
                file_name=f"{fig_name}.html",
                mime="text/html",
                key=f"download_trend_{y}",
            )

        except Exception as e:
            st.warning(f"{y} 的趨勢圖產生失敗：{e}")

    if trend_fig_dict:
        st.download_button(
            label="下載全部趨勢圖 HTML ZIP",
            data=figs_to_zip(trend_fig_dict),
            file_name="trend_plots_html.zip",
            mime="application/zip",
            key="download_all_trend_zip",
        )


def render_categorical_interaction_plots(
    filtered_df,
    y_cols,
    fixed_col,
    moderator_col,
):
    st.info(
        """
        目前 fixed effect 被視為類別變項，因此使用 grouped mean plot。
        如果 X 軸沒有自然順序，建議使用 Bar；
        如果 X 軸有明確順序，例如 baseline → task，可使用 Line。
        """
    )

    interaction_plot_type = st.radio(
        "選擇交互作用圖類型",
        ["Bar", "Line"],
        horizontal=True,
        index=0,
        key="interaction_plot_type",
    )

    interaction_order_by = st.radio(
        "選擇 X 軸排序方式",
        ["Mean", "Name", "Original"],
        horizontal=True,
        index=0,
        key="interaction_order_by",
    )

    fig_dict = {}

    for y in y_cols:
        try:
            interaction_fig, interaction_summary = make_interaction_plot(
                filtered_df,
                y_col=y,
                fixed_col=fixed_col,
                moderator_col=moderator_col,
                plot_type=interaction_plot_type,
                order_by=interaction_order_by,
            )

            if interaction_fig is None:
                st.warning(f"{y} 沒有足夠資料產生交互作用圖。")
                continue

            fig_name = f"interaction_{y}_{fixed_col}_x_{moderator_col}"
            fig_dict[fig_name] = interaction_fig

            st.markdown(f"### {y}: {fixed_col} × {moderator_col}")
            st.plotly_chart(interaction_fig, use_container_width=True)

            with st.expander(f"查看 {y} 的交互作用平均表"):
                st.dataframe(interaction_summary, use_container_width=True)

            st.download_button(
                label=f"下載 {y} 交互作用圖 HTML",
                data=interaction_fig.to_html(include_plotlyjs="cdn"),
                file_name=f"{fig_name}.html",
                mime="text/html",
                key=f"download_interaction_{y}",
            )

        except Exception as e:
            st.warning(f"{y} 的交互作用圖產生失敗：{e}")

    if fig_dict:
        st.download_button(
            label="下載全部交互作用圖 ZIP",
            data=figs_to_zip(fig_dict),
            file_name="interaction_plots_html.zip",
            mime="application/zip",
            key="download_all_interaction_zip",
        )


# ======================================================
# Auto Interpretation Subsection
# ======================================================
def render_auto_interpretation(sig_df, random_col, fixed_col):
    st.subheader("自動解讀範例")

    if sig_df.empty:
        st.write(
            """
            在目前設定下，批次 MixedLM 尚未發現非截距固定效果達到 p < .05。
            這不一定代表沒有差異，也可能與資料量、模型設定或 random intercept 選擇有關。
            """
        )
    else:
        outcomes = ", ".join(sig_df["outcome"].unique().tolist())
        effect_types = ", ".join(sig_df["effect_type"].unique().tolist())

        st.write(
            f"""
            在目前設定下，以下 outcome 至少有一個固定效果達到 p < .05：  
            **{outcomes}**

            顯著效果類型包含：**{effect_types}**。  
            這表示在控制 **{random_col}** 的隨機截距後，
            **{fixed_col}** 或其相關項目可能仍與部分聲學特徵變化有關。
            """
        )


# ======================================================
# Portfolio Notes Tab
# ======================================================
def render_portfolio():
    st.header("Portfolio Notes")

    st.subheader("中文作品集描述")

    st.text_area(
        "可複製文字",
        value="""
本專案建立一個語音聲學資料互動式分析 Dashboard，將資料查看、圖表視覺化與批次統計分析整合為可操作介面。

在 Overview 頁面中，使用者可以檢查資料欄位、缺失值、-1 異常值，以及依目前篩選條件查看各欄位的獨立值。

在 Explore Visualization 頁面中，使用者可以選擇不同的 X 軸、Y 軸與 hue 分組，快速查看不同條件下的音長、音高或音量變化。

在 Batch MixedLM 頁面中，使用者可以一次選擇多個聲學特徵，並批次執行混合效應模型，例如 condition 或量表分數對多個聲學特徵的影響，同時控制 speaker 或 item 的隨機截距。

若 fixed effect 為連續量表，系統可使用 Plotly 迴歸趨勢圖呈現不同 moderator 條件下的斜率趨勢；若 fixed effect 為類別變項，則使用 grouped mean plot 呈現條件平均差異。

此專案展示了資料處理、互動式視覺化、批次分析流程自動化、統計建模與資料解讀能力。
        """.strip(),
        height=360,
    )

    st.subheader("英文履歷 bullet")

    st.markdown(
        """
- Built an interactive Streamlit dashboard for speech acoustic data analysis, supporting data upload, filtering, data quality checks, exploratory visualization, and batch MixedLM analysis.
- Developed a batch modeling workflow to fit mixed-effects models across multiple acoustic outcomes while accounting for speaker- or item-level random intercepts.
- Added automatic visualization logic that uses Plotly regression trend plots for continuous scale predictors and grouped mean plots for categorical predictors.
- Automated repeated acoustic data exploration and statistical modeling workflows using Python, pandas, Plotly, Streamlit, and statsmodels.
        """
    )

    st.subheader("目前支援與後續擴充")

    st.markdown(
        """
        **Currently supported**
        - Data preview and column-level unique value inspection
        - Missing value and `-1` value checks
        - Global filtering
        - Interactive visualization for one selected acoustic feature
        - Batch MixedLM for multiple outcomes
        - Random intercepts such as speaker or item
        - Fixed effect mode: Auto / Continuous / Categorical
        - Optional two-way interaction: fixed × moderator
        - Plotly regression trend plot for continuous or scale-based fixed effects
        - Grouped mean plot for categorical fixed effects
        - Excel export for model results
        - HTML / ZIP download for Plotly trend plots and interaction plots

        **Future work**
        - Support multi-factor interactions, such as A × B × C
        - Add random slopes
        - Add predicted means and simple-effects visualization
        - Add model comparison using AIC / BIC
        - Add automatic report generation
        """
    )