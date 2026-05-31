# model_utils.py

import pandas as pd
import statsmodels.formula.api as smf


# ======================================================
# Effect Term Classification
# ======================================================
def classify_effect(term):
    """
    將 statsmodels 輸出的 coefficient term 粗略分類，
    方便在結果表中閱讀。
    """

    if term == "Intercept":
        return "Intercept / baseline"

    elif ":" in term:
        parts = term.count(":") + 1

        if parts == 2:
            return "Two-way interaction"
        elif parts == 3:
            return "Three-way interaction"
        else:
            return "Higher-order interaction"

    elif "C(fixed)" in term or term == "fixed":
        return "Main effect: fixed"

    elif "C(moderator)" in term:
        return "Main effect: moderator"

    else:
        return "Other"


# ======================================================
# Formula Helpers
# ======================================================
def build_fixed_term(temp, fixed_as):
    """
    根據 fixed_as 決定 fixed effect 要當連續變項或類別變項。

    Parameters
    ----------
    temp : pd.DataFrame
        已經將 fixed_col 改名成 fixed 的資料。
    fixed_as : str
        "Auto", "Continuous", or "Categorical"

    Returns
    -------
    temp : pd.DataFrame
        處理後的資料。
    fixed_term : str
        statsmodels formula 使用的 fixed term。
    fixed_display : str
        UI 顯示用的 fixed term。
    error_message : str or None
        如果處理失敗，回傳錯誤訊息；成功則為 None。
    """

    if fixed_as == "Continuous":
        temp["fixed"] = pd.to_numeric(temp["fixed"], errors="coerce")
        temp = temp.dropna(subset=["fixed"])

        if temp.empty:
            return temp, None, None, "Fixed effect cannot be converted to numeric"

        fixed_term = "fixed"
        fixed_display = "fixed"

    elif fixed_as == "Categorical":
        temp["fixed"] = temp["fixed"].astype(str)
        fixed_term = "C(fixed)"
        fixed_display = "C(fixed)"

    else:
        if pd.api.types.is_numeric_dtype(temp["fixed"]):
            fixed_term = "fixed"
            fixed_display = "fixed"
        else:
            temp["fixed"] = temp["fixed"].astype(str)
            fixed_term = "C(fixed)"
            fixed_display = "C(fixed)"

    return temp, fixed_term, fixed_display, None


def build_formula(y_col, fixed_col, random_col, moderator_col, fixed_term, fixed_display):
    """
    建立 statsmodels formula 與顯示用 formula。
    """

    if moderator_col and moderator_col != "None":
        formula = f"y ~ {fixed_term} * C(moderator)"

        if fixed_display == "fixed":
            display_fixed = fixed_col
        else:
            display_fixed = f"C({fixed_col})"

        display_formula = (
            f"{y_col} ~ {display_fixed} * {moderator_col} "
            f"+ (1 | {random_col})"
        )

    else:
        formula = f"y ~ {fixed_term}"

        if fixed_display == "fixed":
            display_fixed = fixed_col
        else:
            display_fixed = f"C({fixed_col})"

        display_formula = (
            f"{y_col} ~ {display_fixed} + (1 | {random_col})"
        )

    return formula, display_formula


# ======================================================
# Data Validation Helpers
# ======================================================
def validate_mixedlm_data(temp, y_col, random_col):
    """
    在跑 MixedLM 前檢查資料是否足夠。
    """

    if temp.empty:
        return {
            "outcome": y_col,
            "status": "failed",
            "note": "No valid data",
        }

    if temp[y_col].nunique() < 2:
        return {
            "outcome": y_col,
            "status": "failed",
            "note": "Outcome has too little variation",
        }

    if temp[random_col].nunique() < 2:
        return {
            "outcome": y_col,
            "status": "failed",
            "note": "Random intercept needs at least 2 groups",
        }

    group_counts = temp[random_col].value_counts()

    if (group_counts >= 2).sum() < 2:
        return {
            "outcome": y_col,
            "status": "failed",
            "note": "At least 2 random groups need 2+ observations",
        }

    return None


# ======================================================
# Model Fitting Helpers
# ======================================================
def fit_mixedlm_with_fallback(formula, temp):
    """
    先用 lbfgs 擬合，如果失敗，再改用 powell。
    """

    try:
        model = smf.mixedlm(
            formula=formula,
            data=temp,
            groups=temp["random_group"],
        )

        result = model.fit(
            reml=False,
            method="lbfgs",
            maxiter=200,
        )

        return result, None

    except Exception:
        try:
            model = smf.mixedlm(
                formula=formula,
                data=temp,
                groups=temp["random_group"],
            )

            result = model.fit(
                reml=False,
                method="powell",
                maxiter=500,
            )

            return result, None

        except Exception as e:
            return None, f"Model failed: {e}"


def extract_fixed_effects(result, y_col, display_formula, temp):
    """
    將 MixedLM 結果整理成 DataFrame。
    """

    fixed_terms = result.fe_params.index

    coef_df = pd.DataFrame({
        "outcome": y_col,
        "formula": display_formula,
        "term": fixed_terms,
        "effect_type": [
            classify_effect(term)
            for term in fixed_terms
        ],
        "coef": result.fe_params.values,
        "std_error": result.bse[fixed_terms].values,
        "z": result.tvalues[fixed_terms].values,
        "p_value": result.pvalues[fixed_terms].values,
        "n": int(result.nobs),
        "random_groups": temp["random_group"].nunique(),
        "aic": result.aic,
        "bic": result.bic,
        "converged": result.converged,
    })

    for col in ["coef", "std_error", "z", "p_value", "aic", "bic"]:
        coef_df[col] = coef_df[col].round(6)

    return coef_df


def make_success_status(result, y_col, display_formula, temp):
    """
    產生模型成功時的狀態表。
    """

    return {
        "outcome": y_col,
        "status": "success",
        "formula": display_formula,
        "n": int(result.nobs),
        "random_groups": temp["random_group"].nunique(),
        "converged": result.converged,
        "note": "OK",
    }


# ======================================================
# Main MixedLM Functions
# ======================================================
def run_one_mixedlm(
    df,
    y_col,
    fixed_col,
    random_col,
    moderator_col=None,
    fixed_as="Auto",
):
    """
    Run one MixedLM:

    Without moderator:
        y ~ fixed + (1 | random)

    With moderator:
        y ~ fixed * moderator + (1 | random)

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    y_col : str
        Outcome variable.
    fixed_col : str
        Fixed effect variable.
    random_col : str
        Random intercept grouping variable.
    moderator_col : str or None
        Optional moderator / interaction variable.
    fixed_as : str
        "Auto", "Continuous", or "Categorical"

    Returns
    -------
    coef_df : pd.DataFrame or None
        Fixed effect result table.
    model_status : dict
        Model running status.
    """

    needed_cols = [y_col, fixed_col, random_col]

    if moderator_col and moderator_col != "None":
        needed_cols.append(moderator_col)

    temp = df[needed_cols].dropna().copy()

    validation_error = validate_mixedlm_data(
        temp=temp,
        y_col=y_col,
        random_col=random_col,
    )

    if validation_error is not None:
        return None, validation_error

    temp = temp.rename(columns={
        y_col: "y",
        fixed_col: "fixed",
        random_col: "random_group",
    })

    temp, fixed_term, fixed_display, error_message = build_fixed_term(
        temp=temp,
        fixed_as=fixed_as,
    )

    if error_message is not None:
        return None, {
            "outcome": y_col,
            "status": "failed",
            "note": error_message,
        }

    if moderator_col and moderator_col != "None":
        temp = temp.rename(columns={moderator_col: "moderator"})
        temp["moderator"] = temp["moderator"].astype(str)

    temp["random_group"] = temp["random_group"].astype(str)

    formula, display_formula = build_formula(
        y_col=y_col,
        fixed_col=fixed_col,
        random_col=random_col,
        moderator_col=moderator_col,
        fixed_term=fixed_term,
        fixed_display=fixed_display,
    )

    result, fit_error = fit_mixedlm_with_fallback(
        formula=formula,
        temp=temp,
    )

    if fit_error is not None:
        return None, {
            "outcome": y_col,
            "status": "failed",
            "note": fit_error,
        }

    try:
        coef_df = extract_fixed_effects(
            result=result,
            y_col=y_col,
            display_formula=display_formula,
            temp=temp,
        )

        model_status = make_success_status(
            result=result,
            y_col=y_col,
            display_formula=display_formula,
            temp=temp,
        )

        return coef_df, model_status

    except Exception as e:
        return None, {
            "outcome": y_col,
            "status": "failed",
            "note": f"Result extraction failed: {e}",
        }


def run_batch_mixedlm(
    df,
    y_cols,
    fixed_col,
    random_col,
    moderator_col=None,
    fixed_as="Auto",
):
    """
    對多個 outcome 批次執行 MixedLM。
    """

    all_coef_tables = []
    status_list = []

    for y_col in y_cols:
        coef_df, status = run_one_mixedlm(
            df=df,
            y_col=y_col,
            fixed_col=fixed_col,
            random_col=random_col,
            moderator_col=moderator_col,
            fixed_as=fixed_as,
        )

        status_list.append(status)

        if coef_df is not None:
            all_coef_tables.append(coef_df)

    if all_coef_tables:
        coef_results = pd.concat(all_coef_tables, ignore_index=True)
    else:
        coef_results = pd.DataFrame()

    status_df = pd.DataFrame(status_list)

    return coef_results, status_df