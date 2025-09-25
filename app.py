import os
import streamlit as st
import pandas as pd

from dataflow.data_manager import load_file, save_csv, save_xlsx, autosave
from dataflow.operations import (
    delete_columns, delete_rows, fillna, rename_columns, convert_dtypes_safely
)
from dataflow.charts import plot_and_save
from dataflow.exporters import export_pdf

# ---- evitar avisos ruidosos do streamlit ----
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit.runtime.scriptrunner")
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit")

# ---------------------- CONFIG PÁGINA ----------------------
st.set_page_config(page_title="DataFlow", page_icon="🧊", layout="wide")

STYLE_PATH = "dataflow/assets/style.css"
if os.path.exists(STYLE_PATH):
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------- ESTADO ----------------------
def init_state():
    defaults = dict(
        df_master=None,
        df_view=None,
        orig_master=None,
        filters=None,
        cache_dir="tmp_exports"
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    os.makedirs(st.session_state.cache_dir, exist_ok=True)

init_state()

# ---------------------- HELPERS ----------------------
def _coerce_value_for_col(df: pd.DataFrame, col: str, val: str):
    if col not in df.columns:
        return val
    s = df[col]
    if pd.api.types.is_numeric_dtype(s):
        try:
            return pd.to_numeric(val)
        except Exception:
            return val
    return val

def apply_filters(df: pd.DataFrame, filters: dict | None) -> pd.DataFrame:
    if df is None or filters is None:
        return df
    col, op_label, val = filters.get("col"), filters.get("op"), filters.get("val")
    if not col or val is None or val == "":
        return df

    try:
        if op_label == "Contém (texto)":
            return df[df[col].astype(str).str.contains(str(val), case=False, na=False)]
        ops = {
            "É igual a": "==",
            "É diferente de": "!=",
            "Maior que": ">",
            "Menor que": "<",
            "Maior ou igual a": ">=",
            "Menor ou igual a": "<=",
        }
        op = ops.get(op_label)
        if op is None:
            return df
        coerced = _coerce_value_for_col(df, col, val)
        expr = f"`{col}` {op} @coerced"
        return df.query(expr, local_dict={"coerced": coerced})
    except Exception:
        return df

def recompute_view():
    st.session_state.df_view = apply_filters(st.session_state.df_master, st.session_state.filters)

# ---------------------- CABEÇALHO ----------------------
st.markdown(
    """
    <div class="block-glass neon" style="margin-bottom:1rem;">
      <h1>🧊 DataFlow</h1>
      <p style="margin:0;opacity:.9">Manipule, analise e exporte planilhas com uma interface moderna.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------- UPLOAD + LIMPAR ----------------------
uploaded = st.file_uploader("📂 Envie um arquivo (.csv ou .xlsx)", type=["csv", "xlsx"])

left, right = st.columns([3, 1])
with left:
    if uploaded is not None:
        df = load_file(uploaded)
        df = convert_dtypes_safely(df)

        st.session_state.df_master = df.copy()
        st.session_state.orig_master = df.copy()
        st.session_state.filters = None
        recompute_view()

        st.success(f"Arquivo carregado: {uploaded.name} — {df.shape[0]} linhas × {df.shape[1]} colunas")
        autosave(st.session_state.df_master)

with right:
    if st.session_state.df_master is not None:
        if st.button("🗑️ Limpar planilha", use_container_width=True):
            st.session_state.df_master = None
            st.session_state.orig_master = None
            st.session_state.filters = None
            st.session_state.df_view = None
            st.info("A planilha foi descartada. Faça um novo upload para continuar.")

if st.session_state.df_master is None or st.session_state.df_view is None:
    st.stop()

# ---------------------- ABAS ----------------------
tab_edit, tab_stats, tab_charts, tab_export = st.tabs(
    ["✏️ Editor de Dados", "📊 Estatísticas", "📈 Gráficos", "💾 Exportar"]
)

# ---------------------- EDITOR ----------------------
with tab_edit:
    st.subheader("Editor de Dados")

    with st.expander("🔍 Filtros"):
        df = st.session_state.df_master
        colnames = list(df.columns)
        fcol = st.selectbox("Coluna", colnames, index=0)
        fop = st.selectbox("Condição", [
            "É igual a", "É diferente de", "Maior que", "Menor que",
            "Maior ou igual a", "Menor ou igual a", "Contém (texto)"
        ])
        fval = st.text_input("Valor")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Aplicar filtro", use_container_width=True):
                st.session_state.filters = {"col": fcol, "op": fop, "val": fval}
                recompute_view()
        with c2:
            if st.button("Limpar filtro", use_container_width=True):
                st.session_state.filters = None
                recompute_view()

    with st.expander("🧹 Limpeza de Dados"):
        fill_choice = st.selectbox("Preencher valores ausentes (NaN) com:",
                                   ["--", "Valor fixo", "Média", "Mediana", "Moda"])
        fill_value = st.text_input("Valor (se usar 'Valor fixo')", value="") if fill_choice == "Valor fixo" else None
        if st.button("Aplicar preenchimento"):
            strategy_map = {"Valor fixo": "value", "Média": "mean", "Mediana": "median", "Moda": "mode", "--": "value"}
            st.session_state.df_master = fillna(st.session_state.df_master, strategy=strategy_map[fill_choice], value=fill_value)
            recompute_view()

        cols_to_drop = st.multiselect("Remover colunas", options=list(st.session_state.df_master.columns))
        if st.button("Remover colunas selecionadas"):
            st.session_state.df_master = delete_columns(st.session_state.df_master, cols_to_drop)
            recompute_view()

        idx_str = st.text_input("Remover linhas (índices separados por vírgula)", value="")
        if st.button("Remover linhas"):
            try:
                idxs = [int(i.strip()) for i in idx_str.split(",") if i.strip() != ""]
            except Exception:
                idxs = []
            st.session_state.df_master = delete_rows(st.session_state.df_master, idxs)
            recompute_view()

        mapping_str = st.text_input("Renomear colunas (ex.: Antiga->Nova;Outra->NovoNome)", value="")
        if st.button("Aplicar renomeação"):
            mapping = {}
            pairs = [p.strip() for p in mapping_str.split(";") if "->" in p]
            for p in pairs:
                a, b = [x.strip() for x in p.split("->", 1)]
                mapping[a] = b
            st.session_state.df_master = rename_columns(st.session_state.df_master, mapping)
            recompute_view()

        if st.button("⟲ Recarregar versão original"):
            st.session_state.df_master = st.session_state.orig_master.copy()
            recompute_view()

    st.caption("💡 Dica: você pode editar diretamente as células (clique duplo).")
    view = st.session_state.df_view.copy()
    view["__rowid__"] = view.index

    edited = st.data_editor(
        view,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        key="data_editor_view",
        column_config={"__rowid__": st.column_config.NumberColumn("row_id", help="id", disabled=True)},
    )

    edited = pd.DataFrame(edited)
    if "__rowid__" in edited.columns:
        old_rows = edited[edited["__rowid__"].notna()].copy()
        if not old_rows.empty:
            base_cols = [c for c in old_rows.columns if c != "__rowid__"]
            st.session_state.df_master.loc[old_rows["__rowid__"].astype(int).values, base_cols] = old_rows[base_cols].values

        new_rows = edited[edited["__rowid__"].isna()].drop(columns="__rowid__", errors="ignore")
        if not new_rows.empty:
            st.session_state.df_master = pd.concat([st.session_state.df_master, new_rows], ignore_index=True)

        recompute_view()

# ---------------------- ESTATÍSTICAS ----------------------
with tab_stats:
    st.subheader("📊 Estatísticas Dinâmicas")
    df = st.session_state.df_view

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Total de Linhas", df.shape[0])
    with c2: st.metric("Total de Colunas", df.shape[1])
    with c3: st.metric("Valores Nulos", int(df.isna().sum().sum()))

    st.markdown("---")

    col = st.selectbox("Selecione uma coluna para explorar:", df.columns, key="col_selecionada")
    if col:
        if pd.api.types.is_numeric_dtype(df[col]):
            st.write(f"### 🔢 Coluna Numérica: **{col}**")
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Média", round(df[col].mean(), 2))
            with c2: st.metric("Mediana", round(df[col].median(), 2))
            with c3: st.metric("Desvio Padrão", round(df[col].std(), 2))
            c4, c5, c6 = st.columns(3)
            with c4: st.metric("Mínimo", round(df[col].min(), 2))
            with c5: st.metric("Máximo", round(df[col].max(), 2))
            with c6: st.metric("Valores Únicos", df[col].nunique())
            st.bar_chart(df[col].dropna(), use_container_width=True)
        else:
            st.write(f"### 🔤 Coluna Categórica: **{col}**")
            c1, c2 = st.columns(2)
            with c1: st.metric("Valores Únicos", df[col].nunique())
            top = df[col].mode().iloc[0] if not df[col].mode().empty else "-"
            with c2: st.metric("Valor Mais Frequente", str(top))
            freq = df[col].value_counts()
            if not freq.empty:
                st.bar_chart(freq.head(10), use_container_width=True)

# ---------------------- GRÁFICOS ----------------------
with tab_charts:
    st.subheader("📈 Gráficos")
    df = st.session_state.df_view

    num_cols = df.select_dtypes(include="number").columns.tolist()
    all_cols = list(df.columns)

    x_col = st.selectbox("Eixo X", options=["(índice)"] + all_cols, index=0)
    y_col = st.selectbox("Eixo Y", options=num_cols if num_cols else all_cols)
    kind_label = st.selectbox("Tipo de gráfico", ["Linha", "Barra", "Dispersão", "Histograma"])

    agg_label = "Sem agregação"
    top_n = None
    if kind_label in ["Barra", "Linha"]:
        agg_label = st.selectbox(
            "Como agregar?",
            ["Somar por categoria", "Média por categoria", "Contar registros", "Máximo por categoria", "Mínimo por categoria"],
            index=0
        )
        top_n = st.slider("Limitar categorias (Top N)", 5, 100, 20, 1)

    if st.button("Gerar gráfico"):
        work_df = df.reset_index().rename(columns={"index": "index_"})
        x_use = "index_" if x_col == "(índice)" else x_col

        kind_map = {"Linha": "line", "Barra": "bar", "Dispersão": "scatter", "Histograma": "hist"}
        agg_map = {
            "Sem agregação": "none",
            "Somar por categoria": "sum",
            "Média por categoria": "mean",
            "Contar registros": "count",
            "Máximo por categoria": "max",
            "Mínimo por categoria": "min",
        }
        kind = kind_map[kind_label]
        agg = agg_map.get(agg_label, "none")

        if kind == "hist" and not pd.api.types.is_numeric_dtype(work_df[y_col]):
            st.error("Para histograma, selecione uma coluna numérica no eixo Y.")
        else:
            chart_path = plot_and_save(
                work_df, x_use, y_col,
                kind=kind,
                outdir=st.session_state.cache_dir,
                agg=agg,
                top_n=top_n if kind in ["bar", "line"] else None
            )
            st.image(chart_path, caption=os.path.basename(chart_path), use_container_width=True)

# ---------------------- EXPORTAR ----------------------
with tab_export:
    st.subheader("💾 Exportar Dados")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.download_button(
            "Exportar como CSV",
            data=save_csv(st.session_state.df_view),
            file_name="dataflow_export.csv",
            mime="text/csv",
            use_container_width=True
        )

    with c2:
        st.download_button(
            "Exportar como Excel (XLSX)",
            data=save_xlsx(st.session_state.df_view),
            file_name="dataflow_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with c3:
        if st.button("Gerar PDF", use_container_width=True):
            charts = []
            if os.path.exists(st.session_state.cache_dir):
                charts = [
                    os.path.join(st.session_state.cache_dir, f)
                    for f in os.listdir(st.session_state.cache_dir)
                    if f.lower().endswith(".png")
                ]
            pdf_path = export_pdf(st.session_state.df_view, charts, st.session_state.cache_dir)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📄 Baixar Relatório PDF",
                    data=f.read(),
                    file_name="dataflow_relatorio.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# autosave do master
autosave(st.session_state.df_master)
