from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import os
from reportlab.lib.enums import TA_RIGHT

def format_currency(amount):
    return f"R{amount:,.2f}"

def get_styles():
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center alignment
    ))
    
    styles.add(ParagraphStyle(
        name='CompanyName',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='CompanyDetails',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='Header',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
        textColor=colors.HexColor('#2c3e50')
    ))
    
    return styles

def generate_quote_pdf(quote):
    # Create the PDF document
    doc = SimpleDocTemplate(f"temp/quote_{quote.quote_number}.pdf", pagesize=A4,
                          rightMargin=30, leftMargin=30,
                          topMargin=30, bottomMargin=30)
    
    # Initialize list to store flowable elements
    elements = []
    
    # Get the styles
    styles = get_styles()
    
    # Add document title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        alignment=TA_RIGHT,
        spaceAfter=20,
    )
    elements.append(Paragraph('<b>QUOTATION</b>', title_style))
    
    # Add logo if it exists
    if quote.company.logo:
        logo_path = os.path.join('static/uploads', quote.company.logo)
        if os.path.exists(logo_path):
            img = Image(logo_path)
            img.drawHeight = 50
            img.drawWidth = 100
            img._offs_x = 0  # Align to left
            img._offs_y = 0  # Align to top
            elements.append(img)
            elements.append(Spacer(1, 10))
    
    # Add company details
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
    )
    
    # Company details on left
    company_text = [
        Paragraph(f"<b>{quote.company.company_name}</b>", company_style),
    ]
    if quote.company.address:
        company_text.append(Paragraph(quote.company.address, company_style))
    if quote.company.registration_number:
        company_text.append(Paragraph(f"Reg No: {quote.company.registration_number}", company_style))
    if quote.company.vat_number:
        company_text.append(Paragraph(f"VAT No: {quote.company.vat_number}", company_style))
    if quote.company.telephone:
        company_text.append(Paragraph(f"Tel: {quote.company.telephone}", company_style))
    if quote.company.email:
        company_text.append(Paragraph(f"Email: {quote.company.email}", company_style))

    # Document details on right
    doc_style = ParagraphStyle(
        'DocStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=TA_RIGHT
    )
    
    doc_text = [
        Paragraph(f"Quote #: {quote.quote_number}", doc_style),
        Paragraph(f"Date: {quote.date.strftime('%d %B %Y')}", doc_style),
        Paragraph(f"Valid Until: {quote.valid_until.strftime('%d %B %Y')}", doc_style),
    ]

    # Create table for header layout
    header_data = [[company_text, doc_text]]
    header_table = Table(header_data, colWidths=[doc.width/2]*2)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Client Details
    elements.append(Paragraph('Bill To:', styles['SectionHeader']))
    client_details = [f"<b>{quote.to_name}</b>"]
    if quote.to_registration_number:
        client_details.append(f"Registration: {quote.to_registration_number}")
    if quote.to_vat_number:
        client_details.append(f"VAT: {quote.to_vat_number}")
    if quote.to_email:
        client_details.append(f"Email: {quote.to_email}")
    if quote.to_address:
        client_details.append(quote.to_address)
    
    elements.append(Paragraph("<br/>".join(client_details), styles['CompanyDetails']))
    elements.append(Spacer(1, 20))
    
    # Items Table
    data = [['Description', 'Quantity', 'Unit Price', 'Discount', 'Total']]
    
    # Add items
    for item in quote.items:
        data.append([
            item.description,
            str(item.quantity),
            format_currency(item.unit_price),
            f"{item.discount}%",
            format_currency(item.total)
        ])
    
    # Add totals
    data.extend([
        ['', '', '', 'Subtotal:', format_currency(quote.subtotal)],
        ['', '', '', 'VAT (15%):', format_currency(quote.vat_amount)],
        ['', '', '', 'Total:', format_currency(quote.total)]
    ])
    
    # Create and style the table
    items_table = Table(data, colWidths=[220, 70, 90, 70, 90])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),      # Description
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),    # Quantity
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),    # Unit Price, Discount, Total
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ecf0f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Style the totals rows
    table_style.add('BACKGROUND', (-2, -3), (-1, -1), colors.HexColor('#2c3e50'))
    table_style.add('TEXTCOLOR', (-2, -3), (-1, -1), colors.whitesmoke)
    table_style.add('FONTNAME', (-2, -3), (-1, -1), 'Helvetica-Bold')
    
    items_table.setStyle(table_style)
    elements.append(items_table)
    
    # Bank Details if they exist
    if quote.company.bank_details:
        elements.append(Spacer(1, 30))
        elements.append(Paragraph('Bank Details:', styles['SectionHeader']))
        elements.append(Paragraph(quote.company.bank_details.replace('\n', '<br/>'), styles['CompanyDetails']))
    
    # Build the PDF
    doc.build(elements)

def generate_invoice_pdf(invoice):
    # Create the PDF document
    doc = SimpleDocTemplate(f"temp/invoice_{invoice.invoice_number}.pdf", pagesize=A4,
                          rightMargin=30, leftMargin=30,
                          topMargin=30, bottomMargin=30)
    
    # Initialize list to store flowable elements
    elements = []
    
    # Get the styles
    styles = get_styles()
    
    # Add document title
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        alignment=TA_RIGHT,
        spaceAfter=20,
    )
    elements.append(Paragraph('<b>TAX INVOICE</b>', title_style))
    
    # Add logo if it exists
    if invoice.quote.company.logo:
        logo_path = os.path.join('static/uploads', invoice.quote.company.logo)
        if os.path.exists(logo_path):
            img = Image(logo_path)
            img.drawHeight = 50
            img.drawWidth = 100
            elements.append(img)
            elements.append(Spacer(1, 10))
    
    # Add company details
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
    )
    
    # Company details on left
    company_text = [
        Paragraph(f"<b>{invoice.quote.company.company_name}</b>", company_style),
    ]
    if invoice.quote.company.address:
        company_text.append(Paragraph(invoice.quote.company.address, company_style))
    if invoice.quote.company.registration_number:
        company_text.append(Paragraph(f"Reg No: {invoice.quote.company.registration_number}", company_style))
    if invoice.quote.company.vat_number:
        company_text.append(Paragraph(f"VAT No: {invoice.quote.company.vat_number}", company_style))
    if invoice.quote.company.telephone:
        company_text.append(Paragraph(f"Tel: {invoice.quote.company.telephone}", company_style))
    if invoice.quote.company.email:
        company_text.append(Paragraph(f"Email: {invoice.quote.company.email}", company_style))

    # Document details on right
    doc_style = ParagraphStyle(
        'DocStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=12,
        alignment=TA_RIGHT
    )
    
    doc_text = [
        Paragraph(f"Invoice #: {invoice.invoice_number}", doc_style),
        Paragraph(f"Date: {invoice.date.strftime('%d %B %Y')}", doc_style),
        Paragraph(f"Due Date: {invoice.due_date.strftime('%d %B %Y')}", doc_style),
        Paragraph(f"Quote Ref: {invoice.quote.quote_number}", doc_style),
    ]

    # Create table for header layout
    header_data = [[company_text, doc_text]]
    header_table = Table(header_data, colWidths=[doc.width/2]*2)
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 20))
    
    # Client Details
    elements.append(Paragraph('Bill To:', styles['SectionHeader']))
    client_details = [f"<b>{invoice.to_name}</b>"]
    if invoice.to_registration_number:
        client_details.append(f"Registration: {invoice.to_registration_number}")
    if invoice.to_vat_number:
        client_details.append(f"VAT: {invoice.to_vat_number}")
    if invoice.to_email:
        client_details.append(f"Email: {invoice.to_email}")
    if invoice.to_address:
        client_details.append(invoice.to_address)
    
    elements.append(Paragraph("<br/>".join(client_details), styles['CompanyDetails']))
    elements.append(Spacer(1, 20))
    
    # Items Table
    data = [['Description', 'Quantity', 'Unit Price', 'Discount', 'Total']]
    
    # Add items
    for item in invoice.items:
        data.append([
            item.description,
            str(item.quantity),
            format_currency(item.unit_price),
            f"{item.discount}%",
            format_currency(item.total)
        ])
    
    # Add totals
    data.extend([
        ['', '', '', 'Subtotal:', format_currency(invoice.subtotal)]
    ])
    
    # Only add VAT if company is VAT registered
    if invoice.quote.company.is_vat_registered:
        data.extend([
            ['', '', '', 'VAT (15%):', format_currency(invoice.vat_amount)],
            ['', '', '', 'Total:', format_currency(invoice.total)]
        ])
    else:
        data.extend([
            ['', '', '', 'Total:', format_currency(invoice.subtotal)]  # Use subtotal as total when no VAT
        ])
    
    # Create and style the table
    items_table = Table(data, colWidths=[220, 70, 90, 70, 90])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),      # Description
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),    # Quantity
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),    # Unit Price, Discount, Total
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ecf0f1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    # Style the totals rows
    num_total_rows = 3 if invoice.quote.company.is_vat_registered else 2
    table_style.add('BACKGROUND', (-2, -num_total_rows), (-1, -1), colors.HexColor('#2c3e50'))
    table_style.add('TEXTCOLOR', (-2, -num_total_rows), (-1, -1), colors.whitesmoke)
    table_style.add('FONTNAME', (-2, -num_total_rows), (-1, -1), 'Helvetica-Bold')
    
    items_table.setStyle(table_style)
    elements.append(items_table)
    
    # Bank Details if they exist
    if invoice.quote.company.bank_details:
        elements.append(Spacer(1, 30))
        elements.append(Paragraph('Bank Details:', styles['SectionHeader']))
        elements.append(Paragraph(invoice.quote.company.bank_details.replace('\n', '<br/>'), styles['CompanyDetails']))
    
    # Build the PDF
    doc.build(elements)
