import os
import pandas as pd
import matplotlib.pyplot as plt

def _aggregate_for_plot(df: pd.DataFrame, x: str, y: str, kind: str, agg: str):
    if kind in ("hist", "scatter") or agg == "none":
        return df, x, y
    if x is None or x not in df.columns:
        return df, x, y
    if agg == "count":
        grouped = df.groupby(x).size().reset_index(name="Contagem")
        return grouped, x, "Contagem"
    if y not in df.columns:
        return df, x, y
    grouped = df.groupby(x)[y].agg(agg).reset_index()
    return grouped, x, y

def plot_and_save(df: pd.DataFrame, x: str, y: str, kind: str, outdir: str, agg: str = "none", top_n: int = None):
    os.makedirs(outdir, exist_ok=True)
    df_plot, x_col, y_col = _aggregate_for_plot(df, x, y, kind, agg)

    if kind in ("bar", "line") and agg != "none" and top_n and x_col in df_plot.columns and y_col in df_plot.columns:
        df_plot = df_plot.sort_values(by=y_col, ascending=False).head(int(top_n))

    width = 7
    if kind in ("bar", "line") and x_col in df_plot.columns:
        ncat = len(df_plot[x_col].unique())
        width = min(14, max(7, ncat * 0.4))

    fig, ax = plt.subplots(figsize=(width, 5))

    title = kind.upper()
    if agg != "none" and kind in ("bar", "line"):
        title += f" ({agg.upper()})"
    title += f" — {y_col if y_col else y} x {x_col if x_col else x}"
    ax.set_title(title)

    if kind == "line":
        if x_col and y_col:
            df_plot.plot(x=x_col, y=y_col, kind="line", ax=ax, legend=True)
    elif kind == "bar":
        if x_col and y_col:
            df_plot.plot(x=x_col, y=y_col, kind="bar", ax=ax, legend=True)
            ax.tick_params(axis="x", labelrotation=45)
    elif kind == "scatter":
        x_series = df_plot[x_col]
        if not pd.api.types.is_numeric_dtype(x_series):
            codes, uniques = pd.factorize(x_series.astype(str))
            ax.scatter(codes, df_plot[y_col])
            ax.set_xticks(range(len(uniques)))
            ax.set_xticklabels(uniques, rotation=45, ha="right")
        else:
            ax.scatter(df_plot[x_col], df_plot[y_col])
    elif kind == "hist":
        df_plot[y_col].plot(kind="hist", bins=20, ax=ax)

    path = os.path.join(outdir, f"chart_{kind}_{agg}.png")
    plt.tight_layout()
    plt.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path
