import os
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def export_pdf(df: pd.DataFrame, charts: list[str], outdir: str) -> str:
    """
    Gera relatório PDF estilizado com base no DataFrame e gráficos exportados.

    Args:
        df (pd.DataFrame): DataFrame já processado (inclui alterações do usuário).
        charts (list[str]): Lista de caminhos de gráficos (imagens .png).
        outdir (str): Diretório de saída para salvar o PDF.

    Returns:
        str: Caminho final do PDF gerado.
    """
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, "dataflow_relatorio.pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []

    # ---- Estilos ----
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCustom", fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#0ea5e9")))
    styles.add(ParagraphStyle(name="Subtitle", fontSize=11, leading=14, spaceAfter=10, textColor=colors.grey))
    styles.add(ParagraphStyle(name="NormalSmall", fontSize=9, leading=12))

    # ---- Cabeçalho ----
    elements.append(Paragraph("Relatório DataFlow", styles["TitleCustom"]))
    elements.append(Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Subtitle"]))
    elements.append(Spacer(1, 12))

    # ---- Estatísticas rápidas ----
    stats_summary = [
        f"Total de Linhas: {df.shape[0]}",
        f"Total de Colunas: {df.shape[1]}",
        f"Valores Nulos: {int(df.isna().sum().sum())}"
    ]
    for stat in stats_summary:
        elements.append(Paragraph(stat, styles["NormalSmall"]))
    elements.append(Spacer(1, 12))

    # ---- Estatísticas detalhadas por coluna ----
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            desc = (
                f"<b>{col}</b> → Média: {df[col].mean():.2f}, "
                f"Mediana: {df[col].median():.2f}, "
                f"Mín: {df[col].min()}, "
                f"Máx: {df[col].max()}, "
                f"Únicos: {df[col].nunique()}"
            )
        else:
            top = df[col].mode().iloc[0] if not df[col].mode().empty else "-"
            desc = (
                f"<b>{col}</b> → Únicos: {df[col].nunique()}, "
                f"Mais frequente: {top}"
            )
        elements.append(Paragraph(desc, styles["NormalSmall"]))
    elements.append(Spacer(1, 14))

    # ---- Tabela com dados ----
    max_rows = 30  # limitar para não estourar o PDF
    table_data = [list(df.columns)] + df.head(max_rows).astype(str).values.tolist()

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0ea5e9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # ---- Gráficos ----
    if charts:
        elements.append(PageBreak())
        elements.append(Paragraph("📊 Gráficos", styles["TitleCustom"]))
        elements.append(Spacer(1, 12))

        for chart in charts:
            if os.path.exists(chart):
                elements.append(Image(chart, width=450, height=250))
                elements.append(Spacer(1, 12))

    # ---- Constrói PDF ----
    doc.build(elements)
    return pdf_path
