"""
invoice_mailer.py
-----------------
Reads transactions.csv and sends one invoice email per row to your Gmail,
all appearing to come from Tuna Tax.

Distribution:
  80% — perfect emails with correct PDF
  10% — emails with a deliberate error (wrong amount, corrupt PDF, missing field)
  10% — silently skipped (simulates lost emails)

Usage:
  GMAIL_USER=you@gmail.com GMAIL_APP_PASSWORD=xxxx python invoice_mailer.py
"""

import os
import io
import csv
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas as rl_canvas

# ── CONFIG ──────────────────────────────────────────────────────────────
YOUR_GMAIL     = "hogandan42@gmail.com"
YOUR_APP_PASSWORD = "qwyv hmbo esmz xktc"
CSV_FILE       = "transactions.csv"
SMTP_SERVER    = "smtp.gmail.com"
SMTP_PORT      = 465

CLIENT = {
    "name":    "Tuna Tax Ltd.",
    "email":   "accounts@tunatax.ie",
    "address": "22 Grand Canal Dock, Dublin 4, D04 V4X7, Ireland",
    "vat_no":  "IE8734521W",
    "website": "www.tunatax.ie",
    "reg_no":  "IE654321",
}
# ─────────────────────────────────────────────────────────────────────────



# ── PDF GENERATION ───────────────────────────────────────────────────────

def _extract_fields(row: dict, error_type: str | None) -> dict:
    """Pull and optionally corrupt fields from a CSV row."""
    invoice_no    = row.get("Reference", "N/A") or "N/A"
    txn_date      = row.get("Transaction Date (Local)", "") or datetime.now().strftime("%Y-%m-%d")
    try:
        due_date_str = (datetime.strptime(txn_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
    except ValueError:
        due_date_str = "N/A"

    sender_name   = row.get("Counterparty Name", "Unknown Vendor") or "Unknown Vendor"
    sender_iban   = row.get("Counterparty IBAN", "") or ""
    sender_tax_id = row.get("Account ID", "") or ""
    buyer_name    = CLIENT["name"]

    note           = row.get("Note", "") or "Professional Services"
    category       = row.get("Cash Flow Category", "") or ""
    subcategory    = row.get("Cash Flow Subcategory", "") or ""
    currency       = row.get("Currency", "EUR") or "EUR"
    status         = row.get("Status", "") or ""
    payment_ref    = row.get("Transaction ID", "") or ""
    payment_method = row.get("Payment Method", "") or ""

    try:
        subtotal = float(row.get("Total Amount (excl. VAT)", 0) or 0)
        vat      = float(row.get("Total VAT Amount", 0) or 0)
        total    = float(row.get("Total Amount (incl. VAT)", 0) or 0)
    except (ValueError, TypeError):
        subtotal = vat = total = 0.0

    vat_rate = round((vat / subtotal * 100), 1) if subtotal else 0.0

    if error_type == "wrong_amount":
        total = round(total * random.uniform(1.15, 1.40), 2)
    elif error_type == "missing_field":
        invoice_no  = ""
        sender_iban = ""
        payment_ref = ""
    elif error_type == "wrong_date":
        due_date_str = "0000-00-00"

    return dict(
        invoice_no=invoice_no, txn_date=txn_date, due_date_str=due_date_str,
        sender_name=sender_name, sender_iban=sender_iban,
        sender_tax_id=sender_tax_id,
        buyer_name=buyer_name,
        note=note, category=category, subcategory=subcategory,
        currency=currency, status=status,
        payment_ref=payment_ref, payment_method=payment_method,
        subtotal=subtotal, vat=vat, vat_rate=vat_rate, total=total,
    )


# ── STYLE A: Corporate — navy + gold, two-column header ──────────────────

# ── STYLE A: Corporate — navy + gold, two-column header ──────────────────

def _pdf_style_a(f: dict) -> bytes:
    buf = io.BytesIO()
    styles = getSampleStyleSheet()
    navy   = colors.HexColor("#1A3C5E")
    gold   = colors.HexColor("#F0A500")

    title_s = ParagraphStyle("A_title", fontSize=22, textColor=navy, fontName="Helvetica-Bold")
    right_s = ParagraphStyle("A_right", fontSize=9,  alignment=TA_RIGHT, textColor=colors.grey)
    bold_s  = ParagraphStyle("A_bold",  fontSize=10, fontName="Helvetica-Bold")
    foot_s  = ParagraphStyle("A_foot",  fontSize=8,  textColor=colors.grey, alignment=TA_CENTER)
    lbl_s   = ParagraphStyle("A_lbl",   fontSize=9,  fontName="Helvetica-Bold", textColor=navy)
    small_s = ParagraphStyle("A_small", fontSize=8,  textColor=colors.grey)

    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=0.75*inch,  bottomMargin=0.75*inch)
    story = []

    # Header: vendor name left, their IBAN + tax ID right
    hdr = Table([[
        Paragraph(f["sender_name"].upper(), title_s),
        Paragraph(
            f"IBAN: {f['sender_iban'] or '—'}<br/>"
            f"Tax ID: {f['sender_tax_id'] or '—'}",
            right_s)
    ]], colWidths=[3.5*inch, 3.5*inch])
    hdr.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    story += [hdr, HRFlowable(width="100%", thickness=2, color=gold, spaceAfter=14)]

    # Invoice title + meta grid
    story.append(Paragraph("INVOICE", ParagraphStyle("A_inv", fontSize=16,
                            fontName="Helvetica-Bold", textColor=navy, spaceAfter=6)))
    meta = Table([
        [Paragraph("Invoice No:",    lbl_s), f["invoice_no"] or "—",
         Paragraph("Status:",        lbl_s), f["status"]],
        [Paragraph("Invoice Date:",  lbl_s), f["txn_date"],
         Paragraph("Due Date:",      lbl_s), f["due_date_str"]],
        [Paragraph("Currency:",      lbl_s), f["currency"],
         Paragraph("Payment Ref:",   lbl_s), f["payment_ref"] or "—"],
        [Paragraph("Payment Method:",lbl_s), f["payment_method"],
         Paragraph("Category:",      lbl_s), f"{f['category']} / {f['subcategory']}"],
    ], colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    meta.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),9), ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story += [meta, Spacer(1, 14)]

    # Bill To block
    story += [
        Paragraph("Bill To:", bold_s),
        Paragraph(f["buyer_name"], styles["Normal"]),
        Paragraph(CLIENT["address"], small_s),
        Paragraph(f"VAT: {CLIENT['vat_no']}", small_s),
        Spacer(1, 14),
    ]

    # Line items: Description | Qty | Unit Price | VAT% | Total
    rows = [
        [Paragraph("<b>Description</b>", styles["Normal"]),
         Paragraph("<b>Qty</b>", styles["Normal"]),
         Paragraph("<b>Unit Price</b>", styles["Normal"]),
         Paragraph("<b>VAT%</b>", styles["Normal"]),
         Paragraph("<b>Total</b>", styles["Normal"])],
        [f["note"], "1",
         f"{f['currency']} {f['subtotal']:,.2f}",
         f"{f['vat_rate']}%",
         f"{f['currency']} {f['subtotal']:,.2f}"],
        ["VAT", "", "", "", f"{f['currency']} {f['vat']:,.2f}"],
        ["", "", "", "", ""],
        [Paragraph("<b>GROSS TOTAL</b>", styles["Normal"]),
         "", "", "",
         Paragraph(f"<b>{f['currency']} {f['total']:,.2f}</b>", styles["Normal"])],
    ]
    tbl = Table(rows, colWidths=[2.8*inch, 0.5*inch, 1.3*inch, 0.7*inch, 1.7*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), navy),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-2), [colors.whitesmoke, colors.white]),
        ("LINEABOVE",     (0,-1),(-1,-1), 1.5, gold),
        ("LINEBELOW",     (0,-1),(-1,-1), 1.5, gold),
        ("ALIGN",         (1,0), (-1,-1), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
    ]))
    story += [tbl, Spacer(1, 20),
              HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=6),
              Paragraph("Thank you for your business. Please quote the invoice number in all correspondence.", foot_s)]

    doc.build(story)
    return buf.getvalue()


# ── STYLE B: Minimal — black & white, left-aligned, ruled lines ──────────

def _pdf_style_b(f: dict) -> bytes:
    buf = io.BytesIO()
    styles = getSampleStyleSheet()

    mono   = "Courier"
    mono_b = "Courier-Bold"
    black  = colors.black
    lgrey  = colors.HexColor("#CCCCCC")

    hdr_s  = ParagraphStyle("B_hdr",  fontSize=20, fontName=mono_b)
    sub_s  = ParagraphStyle("B_sub",  fontSize=8,  fontName=mono, textColor=colors.grey)
    lbl_s  = ParagraphStyle("B_lbl",  fontSize=9,  fontName=mono_b)
    foot_s = ParagraphStyle("B_foot", fontSize=7,  fontName=mono, textColor=colors.grey)

    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=inch, leftMargin=inch,
                            topMargin=0.85*inch, bottomMargin=0.75*inch)
    story = []

    # Header: company name left, IBAN + tax ID right
    hdr_table = Table([[
        Paragraph(f["sender_name"].upper(), hdr_s),
        Table([
            [Paragraph(f"IBAN: {f['sender_iban'] or '—'}", sub_s)],
            [Paragraph(f"Tax ID: {f['sender_tax_id'] or '—'}", sub_s)],
            [Paragraph(f"Invoice issued to: {CLIENT['name']}", sub_s)],
        ], colWidths=[3.5*inch])
    ]], colWidths=[3*inch, 3.5*inch])
    hdr_table.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "MIDDLE")]))
    story += [
        hdr_table,
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=black, spaceAfter=10),
    ]

    # Invoice label + key/value grid
    story.append(Paragraph("INVOICE", ParagraphStyle("B_inv", fontSize=13, fontName=mono_b, spaceAfter=8)))
    kv_data = [
        ["Invoice No",     f["invoice_no"] or "—",   "Status",      f["status"]],
        ["Invoice Date",   f["txn_date"],             "Due Date",    f["due_date_str"]],
        ["Currency",       f["currency"],             "VAT Rate",    f"{f['vat_rate']}%"],
        ["Payment Ref",    f["payment_ref"] or "—",  "Method",      f["payment_method"]],
        ["Bill To",        f["buyer_name"],           "Buyer VAT",   CLIENT["vat_no"]],
        ["Buyer Address",  CLIENT["address"],         "",            ""],
    ]
    kv = Table(kv_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.1*inch])
    kv.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), mono_b),
        ("FONTNAME",  (2,0), (2,-1), mono_b),
        ("FONTNAME",  (1,0), (1,-1), mono),
        ("FONTNAME",  (3,0), (3,-1), mono),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("LINEBELOW", (0,-1),(-1,-1), 0.5, lgrey),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
    ]))
    story += [kv, Spacer(1, 14)]

    # Line items
    story.append(HRFlowable(width="100%", thickness=0.5, color=black, spaceAfter=4))
    items = Table([
        ["DESCRIPTION",  "QTY", "UNIT PRICE",                          "VAT%",              "TOTAL"],
        [f["note"],      "1",   f"{f['currency']} {f['subtotal']:,.2f}", f"{f['vat_rate']}%", f"{f['currency']} {f['subtotal']:,.2f}"],
        ["VAT",          "",    "",                                     "",                  f"{f['currency']} {f['vat']:,.2f}"],
        ["GROSS TOTAL",  "",    "",                                     "",                  f"{f['currency']} {f['total']:,.2f}"],
    ], colWidths=[2.6*inch, 0.5*inch, 1.3*inch, 0.7*inch, 1.7*inch])
    items.setStyle(TableStyle([
        ("FONTNAME",  (0,0),  (-1,0),  mono_b),
        ("FONTNAME",  (0,1),  (-1,-2), mono),
        ("FONTNAME",  (0,-1), (-1,-1), mono_b),
        ("FONTSIZE",  (0,0),  (-1,-1), 9),
        ("ALIGN",     (1,0),  (-1,-1), "RIGHT"),
        ("LINEABOVE", (0,0),  (-1,0),  0.5, black),
        ("LINEBELOW", (0,0),  (-1,0),  0.5, black),
        ("LINEABOVE", (0,-1), (-1,-1), 0.5, black),
        ("LINEBELOW", (0,-1), (-1,-1), 1,   black),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
    ]))
    story += [items, Spacer(1, 30),
              HRFlowable(width="100%", thickness=0.5, color=lgrey, spaceAfter=4),
              Paragraph(f"{f['sender_name']}  |  IBAN: {f['sender_iban'] or '—'}  |  Tax ID: {f['sender_tax_id'] or '—'}", foot_s)]

    doc.build(story)
    return buf.getvalue()




# ── STYLE C: Modern — full-width teal banner, right-aligned totals box ───

def _pdf_style_c(f: dict) -> bytes:
    buf = io.BytesIO()
    styles = getSampleStyleSheet()

    teal    = colors.HexColor("#0D7377")
    lt_teal = colors.HexColor("#E8F5F5")
    charcoal= colors.HexColor("#2D2D2D")

    foot_s  = ParagraphStyle("C_foot", fontSize=8, textColor=colors.grey, alignment=TA_CENTER)

    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=0, leftMargin=0,
                            topMargin=0,   bottomMargin=0.75*inch)

    W, H = letter

    def draw_banner(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFillColor(teal)
        canvas_obj.rect(0, H - 1.8*inch, W, 1.8*inch, fill=1, stroke=0)
        canvas_obj.setFillColor(colors.white)
        # Vendor name + IBAN + tax ID on left
        canvas_obj.setFont("Helvetica-Bold", 22)
        canvas_obj.drawString(0.6*inch, H - 0.75*inch, f["sender_name"].upper())
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.drawString(0.6*inch, H - 1.0*inch,  f"IBAN: {f['sender_iban'] or '—'}")
        canvas_obj.drawString(0.6*inch, H - 1.18*inch, f"Tax ID: {f['sender_tax_id'] or '—'}")
        # Invoice details on right
        canvas_obj.setFont("Helvetica-Bold", 11)
        canvas_obj.drawRightString(W - 0.6*inch, H - 0.75*inch, "INVOICE")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawRightString(W - 0.6*inch, H - 0.98*inch,  f"No:      {f['invoice_no'] or '—'}")
        canvas_obj.drawRightString(W - 0.6*inch, H - 1.16*inch,  f"Date:    {f['txn_date']}")
        canvas_obj.drawRightString(W - 0.6*inch, H - 1.34*inch,  f"Due:     {f['due_date_str']}")
        canvas_obj.drawRightString(W - 0.6*inch, H - 1.52*inch,  f"Ref:     {f['payment_ref'] or '—'}")
        canvas_obj.restoreState()

    story = [Spacer(1, 1.95*inch)]

    # Bill To + status side by side
    bill_block = (
        f"<b>Bill To:</b><br/>"
        f"{f['buyer_name']}<br/>"
        f"{CLIENT['address']}<br/>"
        f"VAT: {CLIENT['vat_no']}<br/><br/>"
        f"<b>Description:</b> {f['note']}<br/>"
        f"<b>Category:</b> {f['category']} / {f['subcategory']}"
    )
    status_block = (
        f"<b>Status:</b> {f['status']}<br/>"
        f"<b>Currency:</b> {f['currency']}<br/>"
        f"<b>VAT Rate:</b> {f['vat_rate']}%<br/>"
        f"<b>Payment:</b> {f['payment_method']}"
    )
    info = Table([[
        Paragraph(bill_block,   ParagraphStyle("C_bl", fontSize=9, leading=14)),
        Paragraph(status_block, ParagraphStyle("C_st", fontSize=9, leading=14, alignment=TA_RIGHT)),
    ]], colWidths=[4*inch, 3*inch])
    info.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(0,0), 0.6*inch),
        ("RIGHTPADDING", (1,0),(1,0), 0.6*inch),
        ("VALIGN", (0,0),(-1,-1), "TOP"),
    ]))
    story += [info, Spacer(1, 20)]

    # Line items table
    items = Table([
        ["Description",  "Qty", "Unit Price",                           "VAT%",              "Total"],
        [f["note"],      "1",   f"{f['currency']} {f['subtotal']:,.2f}", f"{f['vat_rate']}%", f"{f['currency']} {f['subtotal']:,.2f}"],
        ["VAT",          "",    "",                                      "",                  f"{f['currency']} {f['vat']:,.2f}"],
    ], colWidths=[2.6*inch, 0.5*inch, 1.4*inch, 0.7*inch, 1.6*inch])
    items.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), teal),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("BACKGROUND",    (0,1), (-1,-1), lt_teal),
        ("ALIGN",         (1,0), (-1,-1), "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
    ]))
    items_wrapper = Table([[items]], colWidths=[W])
    items_wrapper.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(0,0), 0.6*inch),
        ("RIGHTPADDING", (0,0),(0,0), 0.6*inch),
    ]))
    story += [items_wrapper, Spacer(1, 16)]

    # Totals box
    total_box = Table([
        ["Net Amount",  f"{f['currency']} {f['subtotal']:,.2f}"],
        [f"VAT ({f['vat_rate']}%)", f"{f['currency']} {f['vat']:,.2f}"],
        [Paragraph("<b>GROSS TOTAL</b>", ParagraphStyle("C_td", fontSize=11, fontName="Helvetica-Bold", textColor=teal)),
         Paragraph(f"<b>{f['currency']} {f['total']:,.2f}</b>",
                   ParagraphStyle("C_ta", fontSize=11, fontName="Helvetica-Bold", textColor=teal, alignment=TA_RIGHT))],
    ], colWidths=[2.2*inch, 2*inch])
    total_box.setStyle(TableStyle([
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (1,0), (1,-1),  "RIGHT"),
        ("LINEABOVE",     (0,-1),(-1,-1), 1.5, teal),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
    ]))
    total_wrapper = Table([[total_box]], colWidths=[W])
    total_wrapper.setStyle(TableStyle([
        ("ALIGN",        (0,0),(0,0), "RIGHT"),
        ("RIGHTPADDING", (0,0),(0,0), 0.6*inch),
    ]))
    story += [total_wrapper, Spacer(1, 30),
              HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceAfter=6),
              Paragraph(f"{f['sender_name']}  ·  IBAN: {f['sender_iban'] or '—'}  ·  Tax ID: {f['sender_tax_id'] or '—'}", foot_s)]

    doc.build(story, onFirstPage=draw_banner, onLaterPages=draw_banner)
    return buf.getvalue()



# ── DISPATCHER ───────────────────────────────────────────────────────────

_STYLES = [_pdf_style_a, _pdf_style_b, _pdf_style_c]

def build_pdf(row: dict, error_type: str | None = None) -> bytes:
    """Build a PDF in a randomly chosen style for the given CSV row."""
    fields = _extract_fields(row, error_type)
    style_fn = random.choice(_STYLES)
    return style_fn(fields)


# ── EMAIL BUILDING ───────────────────────────────────────────────────────

def build_email(row: dict, pdf_bytes: bytes, error_type: str | None = None) -> MIMEMultipart:
    invoice_no   = row.get("Reference", "N/A") or "N/A"
    sender_name  = row.get("Counterparty Name", "Unknown Vendor") or "Unknown Vendor"
    sender_email = f"billing@{sender_name.lower().replace(' ', '').replace(',', '').replace('.', '')}.com"
    total        = row.get("Total Amount (incl. VAT)", "0")
    currency     = row.get("Currency", "EUR")
    txn_date     = row.get("Transaction Date (Local)", "")

    msg = MIMEMultipart()
    msg["From"]     = f"{sender_name} <{sender_email}>"
    msg["To"]       = YOUR_GMAIL
    msg["Reply-To"] = sender_email
    msg["Subject"]  = f"Invoice {invoice_no} from {sender_name} — {CLIENT['name']}"

    txn_date    = row.get("Transaction Date (Local)", "")
    due_date    = (datetime.strptime(txn_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d") if txn_date else "N/A"
    payment_ref = row.get("Transaction ID", "N/A")
    subtotal_v  = row.get("Total Amount (excl. VAT)", "0")
    vat_v       = row.get("Total VAT Amount", "0")

    body = f"""
INVOICE NOTICE

--- VENDOR (FROM) ---
Name:           {sender_name}
Email:          {sender_email}
IBAN:           {row.get("Counterparty IBAN", "—")}
Tax ID:         {row.get("Account ID", "—")}

--- BILL TO ---
Name:           {CLIENT['name']}
Address:        {CLIENT['address']}
VAT No:         {CLIENT['vat_no']}

--- INVOICE DETAILS ---
Invoice No:     {invoice_no}
Invoice Date:   {txn_date}
Due Date:       {due_date}
Payment Ref:    {payment_ref}
Payment Method: {row.get("Payment Method", "—")}
Status:         {row.get("Status", "—")}

--- AMOUNTS ---
Net Amount:     {currency} {subtotal_v}
VAT Amount:     {currency} {vat_v}
Gross Total:    {currency} {total}

Please see the attached PDF for the official invoice record.

{'⚠️  Note: This invoice may contain discrepancies. Please review carefully.' if error_type else ''}

Regards,
{sender_name} Billing Department
""".strip()

    msg.attach(MIMEText(body, "plain"))

    filename = f"{invoice_no.replace('/', '-')}_tunatax.pdf"
    part = MIMEBase("application", "octet-stream")
    part.set_payload(pdf_bytes)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    return msg


# ── MAIN ─────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max number of rows to process")
    args = parser.parse_args()

    with open(CSV_FILE, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if args.limit:
        rows = rows[:args.limit]

    total_rows = len(rows)
    print(f"Loaded {total_rows} transactions from {CSV_FILE}\n")

    sent_ok  = 0
    sent_err = 0
    skipped  = 0

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(YOUR_GMAIL, YOUR_APP_PASSWORD)

        for i, row in enumerate(rows, 1):
            roll = random.random()

            if roll < 0.10:
                # 10% — skip entirely
                print(f"[{i}/{total_rows}] ⏭  SKIPPED  {row.get('Reference','')}")
                skipped += 1
                continue

            elif roll < 0.20:
                # 10% — send with error
                error_type = random.choice(["wrong_amount", "missing_field", "wrong_date"])
                try:
                    pdf_bytes = build_pdf(row, error_type=error_type)
                    msg       = build_email(row, pdf_bytes, error_type=error_type)
                    server.sendmail(YOUR_GMAIL, YOUR_GMAIL, msg.as_string())
                    print(f"[{i}/{total_rows}] ⚠️  ERROR({error_type})  {row.get('Reference','')}")
                    sent_err += 1
                except Exception as e:
                    print(f"[{i}/{total_rows}] ✗  FAILED to send error email: {e}")

            else:
                # 80% — perfect email
                try:
                    pdf_bytes = build_pdf(row)
                    msg       = build_email(row, pdf_bytes)
                    server.sendmail(YOUR_GMAIL, YOUR_GMAIL, msg.as_string())
                    print(f"[{i}/{total_rows}] ✓  OK       {row.get('Reference','')}")
                    sent_ok += 1
                except Exception as e:
                    print(f"[{i}/{total_rows}] ✗  FAILED   {row.get('Reference','')}: {e}")

    print(f"""
─────────────────────────────
 Done!
 ✓  Sent OK:      {sent_ok}
 ⚠️  Sent w/ err:  {sent_err}
 ⏭  Skipped:      {skipped}
 Total rows:      {total_rows}
─────────────────────────────
""")

if __name__ == "__main__":
    main()
