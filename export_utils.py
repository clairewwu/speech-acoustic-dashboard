from io import BytesIO
import zipfile
import pandas as pd


def to_excel_bytes(coef_df, status_df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        coef_df.to_excel(writer, index=False, sheet_name="fixed_effects")
        status_df.to_excel(writer, index=False, sheet_name="model_status")

    return output.getvalue()


def figs_to_zip(fig_dict):
    output = BytesIO()

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, fig in fig_dict.items():
            html = fig.to_html(include_plotlyjs="cdn")
            safe_name = (
                str(name)
                .replace("/", "_")
                .replace("\\", "_")
                .replace(" ", "_")
                .replace(":", "_")
            )
            zf.writestr(f"{safe_name}.html", html)

    output.seek(0)
    return output.getvalue()