import os
import streamlit as st
import pandas as pd
from dataflow.data_manager import load_file, save_csv, save_xlsx, autosave
from dataflow.operations import (
    delete_columns, delete_rows, fillna, rename_columns, convert_dtypes_safely
)
from dataflow.charts import plot_and_save
from dataflow.exporters import export_pdf

# --- silenciar avisos streamlit ---
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit.runtime.scriptrunner")
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit")

# ---------------------- CONFIGURAÇÃO DA PÁGINA ----------------------
st.set_page_config(page_title="DataFlow", page_icon="🧊", layout="wide")

STYLE_PATH = "dataflow/assets/style.css"
if os.path.exists(STYLE_PATH):
    with open(STYLE_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---------------------- ESTADO DA SESSÃO ----------------------
def init_state():
    defaults = dict(
        df=None, orig_df=None, history=[], hist_idx=-1,
        cache_dir="tmp_exports", last_chart=None
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
    os.makedirs(st.session_state.cache_dir, exist_ok=True)

init_state()

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

col1, col2 = st.columns([3, 1])
with col1:
    if uploaded is not None:
        df = load_file(uploaded)
        df = convert_dtypes_safely(df)
        st.session_state.df = df.copy()
        st.session_state.orig_df = df.copy()
        st.success(f"Arquivo carregado: {uploaded.name} — {df.shape[0]} linhas × {df.shape[1]} colunas")
        autosave(st.session_state.df)

with col2:
    if st.session_state.df is not None:
        if st.button("🗑️ Limpar planilha", use_container_width=True):
            st.session_state.df = None
            st.session_state.orig_df = None
            st.info("A planilha foi descartada. Faça um novo upload para continuar.")

# Se não houver planilha carregada, não mostra abas
if st.session_state.df is None:
    st.stop()

# ---------------------- MENU DE ABAS ----------------------
aba1, aba2, aba3, aba4 = st.tabs(["✏️ Editor de Dados", "📊 Estatísticas", "📈 Gráficos", "💾 Exportar"])

# ---------------------- EDITOR ----------------------
with aba1:
    st.subheader("Editor de Dados")

    # --- Filtros amigáveis ---
    with st.expander("🔍 Filtros"):
        colnames = list(st.session_state.df.columns)
        col = st.selectbox("Coluna", options=colnames, help="Selecione a coluna para aplicar o filtro")

        op_label = st.selectbox(
            "Condição",
            options=[
                "É igual a",
                "É diferente de",
                "Maior que",
                "Menor que",
                "Maior ou igual a",
                "Menor ou igual a",
                "Contém (texto)"
            ],
            help="Escolha a condição para o filtro"
        )

        val = st.text_input("Valor", help="Digite o valor a ser usado no filtro")

        if st.button("Aplicar filtro"):
            if val.strip() != "":
                try:
                    if op_label == "Contém (texto)":
                        mask = st.session_state.df[col].astype(str).str.contains(val, case=False, na=False)
                        st.session_state.df = st.session_state.df[mask]
                    else:
                        ops = {
                            "É igual a": "==",
                            "É diferente de": "!=",
                            "Maior que": ">",
                            "Menor que": "<",
                            "Maior ou igual a": ">=",
                            "Menor ou igual a": "<="
                        }
                        op = ops[op_label]
                        expr = f"`{col}` {op} @val"
                        st.session_state.df = st.session_state.df.query(expr, local_dict={"val": val})

                    st.success("Filtro aplicado com sucesso ✅")
                except Exception as e:
                    st.error(f"Não foi possível aplicar o filtro ❌ ({e})")
            else:
                st.warning("Digite um valor para aplicar o filtro.")

    # --- Limpeza ---
    with st.expander("🧹 Limpeza de Dados"):
        fill_choice = st.selectbox("Preencher valores ausentes (NaN) com:", ["--", "Valor fixo", "Média", "Mediana", "Moda"])
        fill_value = st.text_input("Valor (se usar 'Valor fixo')", value="") if fill_choice == "Valor fixo" else None
        if st.button("Aplicar preenchimento"):
            strategy_map = {
                "Valor fixo": "value",
                "Média": "mean",
                "Mediana": "median",
                "Moda": "mode",
                "--": "value"
            }
            st.session_state.df = fillna(st.session_state.df, strategy=strategy_map[fill_choice], value=fill_value)

        cols_to_drop = st.multiselect("Remover colunas", options=list(st.session_state.df.columns))
        if st.button("Remover colunas selecionadas"):
            st.session_state.df = delete_columns(st.session_state.df, cols_to_drop)

        idx_str = st.text_input("Remover linhas (digite índices separados por vírgula)", value="")
        if st.button("Remover linhas"):
            try:
                idxs = [int(i.strip()) for i in idx_str.split(",") if i.strip() != ""]
            except Exception:
                idxs = []
            st.session_state.df = delete_rows(st.session_state.df, idxs)

        mapping_str = st.text_input("Renomear colunas (ex.: Antiga->Nova;Outra->NovoNome)", value="")
        if st.button("Aplicar renomeação"):
            mapping = {}
            pairs = [p.strip() for p in mapping_str.split(";") if "->" in p]
            for p in pairs:
                a, b = [x.strip() for x in p.split("->", 1)]
                mapping[a] = b
            st.session_state.df = rename_columns(st.session_state.df, mapping)

        if st.button("⟲ Recarregar versão original"):
            st.session_state.df = st.session_state.orig_df.copy()

    # --- Editor ---
    edited = st.data_editor(st.session_state.df, use_container_width=True, num_rows="dynamic")
    st.session_state.df = pd.DataFrame(edited)
    st.caption("💡 Dica: edite as células diretamente (clique duplo).")

# ---------------------- ESTATÍSTICAS ----------------------
with aba2:
    st.subheader("📊 Estatísticas Dinâmicas")

    df = st.session_state.df

    # Resumo geral em cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total de Linhas", df.shape[0])
    with c2:
        st.metric("Total de Colunas", df.shape[1])
    with c3:
        st.metric("Valores Nulos", int(df.isna().sum().sum()))

    st.markdown("---")

    # Exploração de coluna
    col = st.selectbox("Selecione uma coluna para explorar:", df.columns)

    if col:
        if pd.api.types.is_numeric_dtype(df[col]):
            st.write(f"### 🔢 Coluna Numérica: **{col}**")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Média", round(df[col].mean(), 2))
            with c2:
                st.metric("Mediana", round(df[col].median(), 2))
            with c3:
                st.metric("Desvio Padrão", round(df[col].std(), 2))

            c4, c5, c6 = st.columns(3)
            with c4:
                st.metric("Mínimo", round(df[col].min(), 2))
            with c5:
                st.metric("Máximo", round(df[col].max(), 2))
            with c6:
                st.metric("Valores Únicos", df[col].nunique())

            st.write("#### 📖 Insight Automático")
            st.info(f"A coluna **{col}** possui média de {round(df[col].mean(),2)}, "
                    f"mediana de {round(df[col].median(),2)}, "
                    f"e valores variando entre {df[col].min()} e {df[col].max()}.")

            st.bar_chart(df[col].dropna(), use_container_width=True)

        else:
            st.write(f"### 🔤 Coluna Categórica: **{col}**")

            c1, c2 = st.columns(2)
            with c1:
                st.metric("Valores Únicos", df[col].nunique())
            with c2:
                st.metric("Valor Mais Frequente", str(df[col].mode().iloc[0]))

            freq = df[col].value_counts()
            top_val, top_count = freq.index[0], freq.iloc[0]

            st.write("#### 📖 Insight Automático")
            st.info(f"A coluna **{col}** possui {df[col].nunique()} valores únicos. "
                    f"O valor mais frequente é **{top_val}**, aparecendo {top_count} vezes.")

            st.write("#### Frequência dos Valores (Top 10)")
            st.bar_chart(freq.head(10), use_container_width=True)

# ---------------------- GRÁFICOS ----------------------
with aba3:
    st.subheader("📈 Gráficos")
    num_cols = st.session_state.df.select_dtypes(include="number").columns.tolist()
    all_cols = list(st.session_state.df.columns)

    x_col = st.selectbox("Eixo X", options=["(índice)"] + all_cols, index=0)
    y_col = st.selectbox("Eixo Y", options=num_cols if num_cols else all_cols)
    kind_label = st.selectbox("Tipo de gráfico", ["Linha", "Barra", "Dispersão", "Histograma"])

    if st.button("Gerar gráfico"):
        work_df = st.session_state.df.reset_index().rename(columns={"index": "index_"})
        x_use = "index_" if x_col == "(índice)" else x_col

        kind_map = {
            "Linha": "line",
            "Barra": "bar",
            "Dispersão": "scatter",
            "Histograma": "hist"
        }
        kind = kind_map[kind_label]

        chart_path = plot_and_save(work_df, x_use, y_col, kind, st.session_state.cache_dir)
        st.image(chart_path, caption=os.path.basename(chart_path), use_container_width=True)

# ---------------------- EXPORTAR ----------------------
with aba4:
    st.subheader("💾 Exportar Dados")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Exportar como CSV", data=save_csv(st.session_state.df),
                           file_name="dataflow_export.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.download_button("Exportar como Excel (XLSX)", data=save_xlsx(st.session_state.df),
                           file_name="dataflow_export.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    with c3:
        if st.button("Gerar PDF"):
            charts = []
            if os.path.exists(st.session_state.cache_dir):
                charts = [os.path.join(st.session_state.cache_dir, f)
                          for f in os.listdir(st.session_state.cache_dir) if f.lower().endswith(".png")]
            pdf_path = export_pdf(st.session_state.df, charts, st.session_state.cache_dir)
            with open(pdf_path, "rb") as f:
                st.download_button("Baixar como PDF", data=f.read(),
                                   file_name="dataflow_relatorio.pdf", mime="application/pdf",
                                   use_container_width=True)

# Autosave
autosave(st.session_state.df)
# Fim do arquivo