import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, PageBreak
)


def export_pdf(df, charts, outdir):
    """
    Gera um relatório PDF estilizado com base no dataframe filtrado/atualizado
    e gráficos gerados durante a sessão.

    Args:
        df (pd.DataFrame): dataframe final (df_view) após edições e filtros
        charts (list[str]): caminhos das imagens de gráficos
        outdir (str): pasta de saída

    Returns:
        str: caminho completo do PDF gerado
    """
    pdf_path = os.path.join(outdir, "dataflow_relatorio.pdf")

    # Documento base
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    elements = []

    # ====== Estilos ======
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#62f5ff"),
        alignment=1,  # centralizado
        spaceAfter=20,
    )
    subtitle_style = ParagraphStyle(
        "subtitle",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=colors.HexColor("#0ea5e9"),
        spaceBefore=12,
        spaceAfter=8,
    )
    normal_style = styles["Normal"]

    # ====== Cabeçalho ======
    elements.append(Paragraph("📊 Relatório DataFlow", title_style))
    elements.append(Paragraph(
        "Este relatório reflete todas as edições, filtros e estatísticas aplicadas no DataFlow durante a sessão.",
        normal_style,
    ))
    elements.append(Spacer(1, 20))

    # ====== Estatísticas ======
    elements.append(Paragraph("📈 Estatísticas do Dataset", subtitle_style))
    stats_data = [
        ["Total de Linhas", len(df)],
        ["Total de Colunas", len(df.columns)],
        ["Valores Nulos", int(df.isna().sum().sum())],
    ]
    stats_table = Table(stats_data, colWidths=[200, 200])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0b0f14")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#62f5ff")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))

    # ====== Preview dos dados ======
    elements.append(Paragraph("📋 Preview dos Dados", subtitle_style))
    if not df.empty:
        preview = df.head(15).reset_index().astype(str).values.tolist()
        preview.insert(0, ["Index"] + list(df.columns))

        preview_table = Table(preview, repeatRows=1)
        preview_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#62f5ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        elements.append(preview_table)
    else:
        elements.append(Paragraph("⚠ Nenhum dado disponível no momento.", normal_style))

    elements.append(PageBreak())

    # ====== Gráficos ======
    if charts:
        elements.append(Paragraph("📊 Gráficos Gerados", subtitle_style))
        for chart in charts:
            try:
                elements.append(Image(chart, width=400, height=250))
                elements.append(Spacer(1, 20))
            except Exception:
                elements.append(Paragraph(f"⚠ Erro ao carregar gráfico: {chart}", normal_style))

    # Monta o documento final
    doc.build(elements)
    return pdf_path
# Fim do arquivo exporters.py