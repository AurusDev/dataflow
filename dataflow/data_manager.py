import pandas as pd
import io
from pathlib import Path

SESSION_DIR = Path(".dataflow_session")
SESSION_DIR.mkdir(exist_ok=True)

def load_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        # auto-detect separador
        return pd.read_csv(uploaded_file, encoding="utf-8", sep=None, engine="python")
    if name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Formato não suportado. Envie .csv ou .xlsx.")

def save_csv(df: pd.DataFrame) -> bytes:
    out = io.StringIO()
    df.to_csv(out, index=False)
    return out.getvalue().encode("utf-8")

def save_xlsx(df: pd.DataFrame) -> bytes:
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    out.seek(0)
    return out.read()

def autosave(df: pd.DataFrame, key: str = "autosave.parquet") -> Path:
    path = SESSION_DIR / key
    try:
        df.to_parquet(path, index=False)
    except Exception:
        # fallback em csv se parquet indisponível
        path = SESSION_DIR / "autosave.csv"
        df.to_csv(path, index=False)
    return path

def try_restore() -> pd.DataFrame | None:
    pq = SESSION_DIR / "autosave.parquet"
    csv = SESSION_DIR / "autosave.csv"
    try:
        if pq.exists():
            return pd.read_parquet(pq)
        if csv.exists():
            return pd.read_csv(csv)
    except Exception:
        return None
    return None
