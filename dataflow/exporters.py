import pandas as pd
import os
from .utils_pdf import df_to_table_data, build_pdf

def export_pdf(df: pd.DataFrame, charts: list, out_dir: str, filename: str = "dataflow_report.pdf") -> str:
    os.makedirs(out_dir, exist_ok=True)
    table_data = df_to_table_data(df)
    pdf_path = os.path.join(out_dir, filename)
    build_pdf(pdf_path, "Relatório DataFlow", table_data, charts)
    return pdf_path
