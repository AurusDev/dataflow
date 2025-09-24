# DataFlow

App em **Python + Streamlit** para manipular e analisar planilhas (.xlsx/.csv) com uma interface **glassmorphism dark**.

## Funcionalidades
- Upload `.csv`/`.xlsx`
- Editor inline (adicionar/remover/editar)
- Filtros via `pandas.query`
- Limpeza: `fillna` (value/mean/median/mode), drop de colunas/linhas, rename
- Estatísticas rápidas
- Gráficos (linha, barra, dispersão, histograma)
- Exportar CSV/XLSX/PDF (PDF inclui gráficos)
- **Undo/Redo (MVP)** e **Autosave** de sessão

## Requisitos
- Python 3.11/3.12 recomendado
- `pip install -r requirements.txt`

## Executar
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
