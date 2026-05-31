# plot_utils.py

import pandas as pd
import plotly.express as px


# ======================================================
# Summary Table
# ======================================================
def make_summary_table(df, x_col, y_col, hue_col=None):
    """
    根據 x_col、y_col，以及可選的 hue_col 產生摘要統計表。

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    x_col : str
        X-axis / grouping variable.
    y_col : str
        Numeric outcome variable.
    hue_col : str or None
        Optional grouping variable.

    Returns
    -------
    summary : pd.DataFrame
        Summary table with N, Mean, SD, Median, Min, Max.
    """

    group_cols = [x_col]

    if hue_col and hue_col != "None" and hue_col != x_col:
        group_cols.append(hue_col)

    summary = (
        df.groupby(group_cols, dropna=False)[y_col]
        .agg(["count", "mean", "std", "median", "min", "max"])
        .reset_index()
    )

    summary = summary.rename(columns={
        "count": "N",
        "mean": "Mean",
        "std": "SD",
        "median": "Median",
        "min": "Min",
        "max": "Max",
    })

    for col in ["Mean", "SD", "Median", "Min", "Max"]:
        summary[col] = summary[col].round(3)

    return summary


# ======================================================
# Explore Visualization
# ======================================================
def make_chart(df, chart_type, x_col, y_col, hue_col):
    """
    產生 Explore Visualization 頁面使用的 Plotly 圖表。

    Supported chart types:
    - Boxplot
    - Violin
    - Barplot
    - Lineplot
    - Scatterplot
    """

    color = None if hue_col == "None" else hue_col

    try:
        if chart_type == "Boxplot":
            fig = px.box(
                df,
                x=x_col,
                y=y_col,
                color=color,
                points="outliers",
                title=f"{y_col} by {x_col}",
            )

        elif chart_type == "Violin":
            fig = px.violin(
                df,
                x=x_col,
                y=y_col,
                color=color,
                box=True,
                points="outliers",
                title=f"Distribution of {y_col} by {x_col}",
            )

        elif chart_type == "Barplot":
            group_cols = [x_col]

            if hue_col != "None" and hue_col != x_col:
                group_cols.append(hue_col)

            plot_df = (
                df.groupby(group_cols, dropna=False, as_index=False)[y_col]
                .mean()
            )

            fig = px.bar(
                plot_df,
                x=x_col,
                y=y_col,
                color=color,
                barmode="group",
                title=f"Average {y_col} by {x_col}",
            )

        elif chart_type == "Lineplot":
            group_cols = [x_col]

            if hue_col != "None" and hue_col != x_col:
                group_cols.append(hue_col)

            plot_df = (
                df.groupby(group_cols, dropna=False, as_index=False)[y_col]
                .mean()
            )

            fig = px.line(
                plot_df,
                x=x_col,
                y=y_col,
                color=color,
                markers=True,
                title=f"Trend of {y_col} by {x_col}",
            )

        elif chart_type == "Scatterplot":
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color,
                opacity=0.7,
                title=f"{y_col} vs. {x_col}",
            )

        else:
            return None

        fig.update_layout(
            height=520,
            title_x=0.02,
            margin=dict(l=30, r=30, t=70, b=50),
        )

        return fig

    except Exception:
        return None


# ======================================================
# Interaction Plot for Categorical Fixed Effect
# ======================================================
def make_interaction_plot(
    df,
    y_col,
    fixed_col,
    moderator_col,
    plot_type="Bar",
    order_by="Mean",
):
    """
    產生類別 fixed effect 的交互作用圖。

    用途：
    - fixed effect 是類別變項時
    - moderator 也是類別變項時
    - 顯示 fixed_col × moderator_col 的 group mean

    Returns
    -------
    fig : plotly.graph_objects.Figure or None
    plot_df : pd.DataFrame
        Aggregated mean table used for plotting.
    """

    plot_df = (
        df[[y_col, fixed_col, moderator_col]]
        .dropna()
        .groupby([fixed_col, moderator_col], as_index=False)[y_col]
        .agg(["mean", "count"])
        .reset_index()
    )

    plot_df = plot_df.rename(columns={
        "mean": "Mean",
        "count": "N",
    })

    if plot_df.empty:
        return None, plot_df

    if order_by == "Mean":
        order_df = (
            plot_df.groupby(fixed_col)["Mean"]
            .mean()
            .sort_values()
            .reset_index()
        )

        category_order = order_df[fixed_col].tolist()

    elif order_by == "Name":
        category_order = sorted(
            plot_df[fixed_col]
            .astype(str)
            .unique()
            .tolist()
        )

    else:
        category_order = (
            plot_df[fixed_col]
            .drop_duplicates()
            .tolist()
        )

    plot_df[fixed_col] = pd.Categorical(
        plot_df[fixed_col],
        categories=category_order,
        ordered=True,
    )

    plot_df = plot_df.sort_values([fixed_col, moderator_col])

    if plot_type == "Line":
        fig = px.line(
            plot_df,
            x=fixed_col,
            y="Mean",
            color=moderator_col,
            markers=True,
            category_orders={fixed_col: category_order},
            title=(
                f"Interaction profile plot: "
                f"{y_col} by {fixed_col} × {moderator_col}"
            ),
            hover_data=["N"],
        )

    else:
        fig = px.bar(
            plot_df,
            x=fixed_col,
            y="Mean",
            color=moderator_col,
            barmode="group",
            category_orders={fixed_col: category_order},
            title=(
                f"Grouped mean plot: "
                f"{y_col} by {fixed_col} × {moderator_col}"
            ),
            hover_data=["N"],
        )

    fig.update_layout(
        height=520,
        title_x=0.02,
        margin=dict(l=30, r=30, t=70, b=90),
        xaxis_title=fixed_col,
        yaxis_title=f"Mean {y_col}",
    )

    fig.update_xaxes(tickangle=30)

    return fig, plot_df


# ======================================================
# Trend Plot for Continuous Fixed Effect
# ======================================================
def make_plotly_trend_plot(df, y_col, x_col, hue_col):
    """
    產生連續 fixed effect 使用的 Plotly 迴歸趨勢圖。

    用途：
    - fixed effect 是量表或連續數值
    - moderator 是類別變項
    - 顯示不同 moderator 條件下 x_col 對 y_col 的斜率趨勢

    Returns
    -------
    fig : plotly.graph_objects.Figure or None
    result : pd.DataFrame or str
        成功時回傳 plot_df；失敗時回傳錯誤訊息。
    """

    plot_df = df[[y_col, x_col, hue_col]].dropna().copy()

    if plot_df.empty:
        return None, "No valid data"

    if not pd.api.types.is_numeric_dtype(plot_df[x_col]):
        return None, "X is not numeric"

    plot_df[hue_col] = plot_df[hue_col].astype(str)

    try:
        fig = px.scatter(
            plot_df,
            x=x_col,
            y=y_col,
            color=hue_col,
            trendline="ols",
            opacity=0.55,
            title=(
                f"Regression trend plot: "
                f"{y_col} by {x_col}, grouped by {hue_col}"
            ),
            labels={
                x_col: x_col,
                y_col: y_col,
                hue_col: hue_col,
            },
            hover_data=[hue_col],
        )

        fig.update_traces(
            marker=dict(size=7),
            selector=dict(mode="markers"),
        )

        fig.update_layout(
            height=560,
            title_x=0.02,
            margin=dict(l=30, r=30, t=70, b=50),
            legend_title_text=hue_col,
        )

        return fig, plot_df

    except Exception as e:
        return None, str(e)


# ======================================================
# Auto Visual Insight
# ======================================================
def auto_visual_insight(summary_df, x_col, y_col):
    """
    根據摘要表產生簡單的自動文字觀察。

    注意：
    這不是統計推論，只是 exploratory visualization 的初步描述。
    """

    if summary_df.empty or "Mean" not in summary_df.columns:
        return "目前沒有足夠資料產生摘要。"

    max_row = summary_df.loc[summary_df["Mean"].idxmax()]
    min_row = summary_df.loc[summary_df["Mean"].idxmin()]

    max_group = max_row[x_col]
    min_group = min_row[x_col]

    max_mean = max_row["Mean"]
    min_mean = min_row["Mean"]
    diff = round(max_mean - min_mean, 3)

    return (
        f"在目前設定下，**{max_group}** 的平均 **{y_col}** 最高，"
        f"約為 **{max_mean}**；"
        f"**{min_group}** 最低，約為 **{min_mean}**。"
        f"兩者平均差距約為 **{diff}**。這是初步視覺化觀察，"
        f"後續可搭配 Batch MixedLM 檢查固定效果是否顯著。"
    )