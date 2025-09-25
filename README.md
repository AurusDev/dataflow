# 🧊 DataFlow

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Manipule, analise e exporte planilhas com uma interface moderna, responsiva e fácil de usar.  
O **DataFlow** é um aplicativo construído em [Streamlit](https://streamlit.io/) que permite trabalhar com arquivos CSV/XLSX de forma interativa.

---

## 🚀 Deploy Público

👉 [Acesse aqui no Streamlit Cloud](hhttps://dataflow.streamlit.app/)  

---

## ✨ Funcionalidades

- Upload de arquivos **CSV** ou **Excel (XLSX)**
- Editor de dados interativo (adicionar, editar, remover linhas e colunas)
- Limpeza de dados: preenchimento de valores ausentes, renomeação, remoção de linhas/colunas
- Filtros simples (numéricos e textuais)
- Estatísticas dinâmicas com métricas resumidas
- Gráficos interativos (linha, barra, dispersão, histograma)
- Exportação em **CSV, XLSX e PDF** (com gráficos incluídos)

---

## 🖼️ Preview

![Screenshot do DataFlow](dataflow/assets/banner.png)  

---

## 🛠️ Instalação local

Clone este repositório e instale as dependências:

```bash
git clone https://github.com/AurusDev/DataFlow.git
cd DataFlow

# Crie um ambiente virtual (opcional, mas recomendado)
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# Instale dependências
pip install -r requirements.txt

# Rode o app
streamlit run app.py
