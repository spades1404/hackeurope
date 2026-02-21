import io
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime

def render_document_to_pdf(doc_data: dict, company_name: str) -> bytes:
    """Takes document JSON and returns a PDF byte string layout"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading3']
    normal_style = styles['Normal']
    warning_style = ParagraphStyle(
        name='Warning',
        parent=styles['Normal'],
        textColor=colors.darkred,
        backColor=colors.lightyellow,
        borderColor=colors.orange,
        borderWidth=1,
        borderPadding=5
    )
    
    elements = []
    
    # header
    status_text = doc_data['metadata'].get('status', 'draft').upper()
    elements.append(Paragraph(f"{company_name} - {doc_data.get('form', 'FORM')}", title_style))
    elements.append(Paragraph(doc_data.get('title', 'Tax Document'), subtitle_style))
    elements.append(Paragraph(f"Status: <b>{status_text}</b>", normal_style))
    elements.append(Spacer(1, 15))
    
    if status_text != 'APPROVED' and status_text != 'SUBMITTED':
        elements.append(Paragraph("DRAFT - NOT FOR SUBMISSION", warning_style))
        elements.append(Spacer(1, 15))
        
    if doc_data.get('warnings'):
        for w in doc_data['warnings']:
            elements.append(Paragraph(f"Warning: {w}", warning_style))
            elements.append(Spacer(1, 10))
            
    # sections
    sections = doc_data.get('sections', [])
    for sec in sections:
        elements.append(Paragraph(sec.get('name', 'Section'), subtitle_style))
        
        table_data = []
        fields = sec.get('fields', {})
        for k, v in fields.items():
            # Formatting numbers
            if isinstance(v, (int, float)):
                val_str = f"{v:,.2f}"
            else:
                val_str = str(v)
            table_data.append([Paragraph(k, normal_style), Paragraph(val_str, normal_style)])
            
        if table_data:
            t = Table(table_data, colWidths=[300, 200])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(t)
            elements.append(Spacer(1, 15))
            
    if doc_data.get('required_attachments'):
        elements.append(Paragraph("Required Attachments:", subtitle_style))
        for att in doc_data['required_attachments']:
            elements.append(Paragraph(f"• {att}", normal_style))
        elements.append(Spacer(1, 15))
        
    gen_time = doc_data['metadata'].get('generated_at', datetime.now().isoformat())
    elements.append(Paragraph(f"Generated at: {gen_time}", styles['Italic']))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
