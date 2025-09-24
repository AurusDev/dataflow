from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from typing import List, Optional
import os

def df_to_table_data(df, max_rows: int = 40):
    head = df.head(max_rows)
    data = [list(map(str, head.columns.tolist()))]
    data += head.astype(str).values.tolist()
    return data

def build_pdf(output_path: str, title: str, table_data: List[List[str]], image_paths: Optional[List[str]] = None):
    styles = getSampleStyleSheet()
    story = [
        Paragraph(title, styles['Title']),
        Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), styles['Normal']),
        Spacer(1, 12)
    ]

    if table_data:
        table = Table(table_data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1b2735')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 10),
            ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#0f1720'), colors.HexColor('#121b26')])
        ]))
        story += [table, Spacer(1, 12)]

    if image_paths:
        for p in image_paths:
            if os.path.exists(p):
                story += [Spacer(1, 14), Image(p, width=480, height=300), Spacer(1, 12)]

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    doc.build(story)
    return output_path
