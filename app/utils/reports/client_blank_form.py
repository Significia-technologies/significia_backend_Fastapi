"""
Client Registration Blank Form Generator — PDF Generation.
"""
import io
import os
from datetime import datetime
from typing import Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def resolve_logo_path(logo_path: Optional[str]) -> Optional[str]:
    """Try multiple strategies to find the logo file on disk."""
    if not logo_path:
        return None
        
    # Strategy 1: Absolute path
    if os.path.isabs(logo_path) and os.path.exists(logo_path):
        return logo_path
        
    # Strategy 2: Relative to CWD
    if os.path.exists(logo_path):
        return os.path.abspath(logo_path)

    # Strategy 3: Relative to backend root
    file_dir = os.path.dirname(os.path.abspath(__file__))
    backend_root = os.path.abspath(os.path.join(file_dir, '..', '..', '..')) # backend/app/utils/reports/ -> backend/
    joined_path = os.path.join(backend_root, logo_path)
    if os.path.exists(joined_path):
        return joined_path

    # Strategy 4: Try prepending 'uploads/'
    uploads_path = os.path.join(backend_root, 'uploads', logo_path)
    if os.path.exists(uploads_path):
        return uploads_path

    return None


def generate_client_blank_form(ia_logo_path: Optional[str] = None) -> io.BytesIO:
    """Generate a professionally styled, grid-based blank Client Registration Form."""
    if not PDF_AVAILABLE:
        raise ImportError("reportlab is not installed.")

    buffer = io.BytesIO()
    # Compact margins for maximum writing space
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle('FormTitle', parent=styles['Heading1'], fontSize=18, alignment=1, spaceAfter=8, textColor=colors.HexColor('#1e293b'), fontName='Helvetica-Bold')
    section_style = ParagraphStyle('FormSection', parent=styles['Normal'], fontSize=11, textColor=colors.white, fontName='Helvetica-Bold')
    label_style = ParagraphStyle('FormLabel', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=10)
    normal_label_style = ParagraphStyle('NormalLabel', parent=styles['Normal'], fontSize=9, fontName='Helvetica', leading=10)

    def add_section_header(text):
        data = [[Paragraph(text.upper(), section_style)]]
        t = Table(data, colWidths=[535])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1e293b')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 4))

    # --- HEADER ---
    header_data = []
    resolved_logo = resolve_logo_path(ia_logo_path)
    if resolved_logo:
        try:
            logo = Image(resolved_logo, width=0.8*inch, height=0.8*inch)
            header_data.append([logo, Paragraph("CLIENT REGISTRATION FORM", title_style), ""])
        except Exception:
            header_data.append(["", Paragraph("CLIENT REGISTRATION FORM", title_style), ""])
    else:
        header_data.append(["", Paragraph("CLIENT REGISTRATION FORM", title_style), ""])
    
    t_header = Table(header_data, colWidths=[80, 375, 80])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'CENTER')]))
    elements.append(t_header)
    elements.append(Spacer(1, 10))

    # Advisor Info Grid
    info_data = [
        [Paragraph("Advisor Name:", label_style), "____________________________", Paragraph("Advisor ID:", label_style), "________________"],
        [Paragraph("Client Code:", label_style), "____________________________", Paragraph("Date:", label_style), "___________"]
    ]
    t_info = Table(info_data, colWidths=[110, 230, 90, 105], rowHeights=25)
    t_info.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_info)
    elements.append(Spacer(1, 5))

    # 1. PERSONAL INFORMATION
    add_section_header("1. Personal Details")
    personal_data = [
        [Paragraph("Full Name:", label_style), "________________________________________", Paragraph("DOB:", label_style), "___________"],
        [Paragraph("Gender:", label_style), "__________________", Paragraph("Marital Status:", label_style), "__________________"],
        [Paragraph("PAN Number:", label_style), "__________________", Paragraph("Aadhar No:", label_style), "__________________"],
        [Paragraph("Nationality:", label_style), "__________________", Paragraph("Passport No:", label_style), "__________________"],
        [Paragraph("Occupation:", label_style), "________________________________________", "", ""],
        [Paragraph("Father's Name:", label_style), "________________________________________", "", ""],
        [Paragraph("Mother's Name:", label_style), "________________________________________", "", ""],
        [Paragraph("Contact Number:", label_style), "__________________", Paragraph("Email ID:", label_style), "__________________"],
        [Paragraph("Residential Status:", label_style), "__________________", Paragraph("Tax Residency:", label_style), "__________________"],
        [Paragraph("PEP Status:", label_style), "________________________________________", "", ""],
        [Paragraph("Permanent Address:", label_style), "________________________________________________________________________", "", ""],
        ["", "________________________________________________________________________", "", ""]
    ]
    t_personal = Table(personal_data, colWidths=[110, 185, 90, 150], rowHeights=24)
    t_personal.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (1,0), (2,0)), ('SPAN', (1,4), (3,4)), ('SPAN', (1,5), (3,5)),
        ('SPAN', (1,6), (3,6)), ('SPAN', (1,9), (3,9)), ('SPAN', (1,10), (3,10)), ('SPAN', (1,11), (3,11)),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_personal)
    elements.append(Spacer(1, 10))

    # 2. FAMILY DETAILS
    add_section_header("2. Family / Spouse Details")
    family_data = [
        [Paragraph("Spouse Name:", label_style), "________________________________", Paragraph("Spouse DOB:", label_style), "___________"],
        [Paragraph("Nominee Name:", label_style), "________________________________", Paragraph("Relationship:", label_style), "___________"]
    ]
    t_family = Table(family_data, colWidths=[110, 185, 90, 150], rowHeights=24)
    t_family.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_family)
    elements.append(Spacer(1, 10))

    # 3. FINANCIAL INFORMATION
    add_section_header("3. Financial Information")
    financial_data = [
        [Paragraph("Annual Income:", label_style), "Rs. ____________________", Paragraph("Net Worth:", label_style), "Rs. ______________"],
        [Paragraph("Income Source:", label_style), "________________________________", Paragraph("FATCA Status:", label_style), "_______________"],
        [Paragraph("Portfolio Value:", label_style), "Rs. ____________________", "", ""],
        [Paragraph("Portfolio Composition:", label_style), "____________________________________________________________", "", ""]
    ]
    t_financial = Table(financial_data, colWidths=[110, 185, 90, 150], rowHeights=24)
    t_financial.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (1,2), (3,2)), ('SPAN', (1,3), (3,3)),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_financial)
    elements.append(Spacer(1, 10))

    # 4. BANKING & TRADING DETAILS
    add_section_header("4. Banking & Trading Details")
    banking_data = [
        [Paragraph("Bank Name:", label_style), "________________________________", Paragraph("Branch:", label_style), "________________"],
        [Paragraph("Account Number:", label_style), "________________________________", Paragraph("IFSC Code:", label_style), "________________"],
        [Paragraph("Demat A/c No:", label_style), "________________________________", Paragraph("Trading A/c:", label_style), "________________"]
    ]
    t_banking = Table(banking_data, colWidths=[110, 185, 90, 150], rowHeights=24)
    t_banking.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_banking)
    elements.append(Spacer(1, 10))

    # 5. INVESTMENT PROFILE
    add_section_header("5. Investment Profile")
    investment_data = [
        [Paragraph("Risk Profile:", label_style), "_________________________", Paragraph("Exp (Years):", label_style), "________"],
        [Paragraph("Horizon:", label_style), "_________________________", Paragraph("Liquidity Needs:", label_style), "________"],
        [Paragraph("Objectives:", label_style), "____________________________________________________________________________", "", ""],
        ["", "____________________________________________________________________________", "", ""]
    ]
    t_investment = Table(investment_data, colWidths=[110, 185, 90, 150], rowHeights=24)
    t_investment.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('SPAN', (1,2), (3,2)), ('SPAN', (1,3), (3,3)),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_investment)
    elements.append(Spacer(1, 10))

    # 6. ADVISOR & OTHER DETAILS
    add_section_header("6. Advisor & Other Details")
    other_data = [
        [Paragraph("Previous Advisor:", label_style), "________________________________", Paragraph("Referral:", label_style), "________________"],
        [Paragraph("Declaration Date:", label_style), "________________________________", Paragraph("Signed (Y/N):", label_style), "________________"]
    ]
    t_other = Table(other_data, colWidths=[110, 185, 90, 150], rowHeights=24)
    t_other.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5)
    ]))
    elements.append(t_other)
    elements.append(Spacer(1, 20))

    # 7. SIGNATURES
    add_section_header("7. Declarations & Signatures")
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("I hereby declare that all the information provided above is true to the best of my knowledge.", normal_label_style))
    elements.append(Spacer(1, 40))
    
    sig_data = [
        ["__________________________", "__________________________"],
        ["Client Signature", "Advisor Signature"],
        ["Date: ___________", "Date: ___________"]
    ]
    sig_table = Table(sig_data, colWidths=[250, 250])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 20),
    ]))
    elements.append(sig_table)

    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("STRICTLY CONFIDENTIAL - Client Registration Document", ParagraphStyle('Footer', alignment=1, fontSize=7, textColor=colors.grey)))

    doc.build(elements)
    buffer.seek(0)
    return buffer
