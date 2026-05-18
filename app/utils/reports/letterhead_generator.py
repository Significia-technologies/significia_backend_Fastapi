"""
Advisor dynamic letterhead PDF Generator — ReportLab stationary implementation.
"""
import io
import os
from typing import Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def generate_letterhead_pdf(
    ia_data: dict,
    logo_path: Optional[str] = None
) -> io.BytesIO:
    """
    Generate a highly polished, dynamically branded corporate letterhead PDF.
    This creates exactly one blank page with the custom header and footer dynamically
    drawn on the page's canvas.
    """
    if not PDF_AVAILABLE:
        raise ImportError("ReportLab is not installed on this system.")

    buffer = io.BytesIO()
    
    # Page setup: A4 with margins configured to clear the header (130pt) and footer (100pt)
    # to avoid overlapping if flowables are printed on it later.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=135,
        bottomMargin=100
    )

    # Blank placeholder element to populate the single page
    elements = [Spacer(1, 10)]

    def draw_letterhead(canvas, document):
        canvas.saveState()

        # ─── BRAND COLOR RESOLUTION ───
        brand_color_hex = ia_data.get("brand_color") or "#0f172a"
        if not str(brand_color_hex).startswith("#"):
            brand_color_hex = f"#{brand_color_hex}"
        try:
            brand_color = colors.HexColor(brand_color_hex)
        except Exception:
            brand_color = colors.HexColor("#0f172a") # Fallback Navy Slate

        # Dimensions & Coordinates
        left_margin = 54
        right_margin = 541.27
        page_width = 595.27
        
        # ─── HEADER SECTION (Draws at y=730) ───
        styles = getSampleStyleSheet()
        
        # Heading typography
        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Normal'],
            fontSize=13,
            leading=16,
            alignment=2, # Right aligned
            fontName='Helvetica-Bold',
            textColor=brand_color
        )
        
        subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            parent=styles['Normal'],
            fontSize=8,
            leading=11,
            alignment=2, # Right aligned
            fontName='Helvetica',
            textColor=colors.HexColor("#475569") # Slate-600
        )

        # 1. Logo Flowable
        logo_flowable = ""
        if logo_path and os.path.exists(logo_path):
            try:
                # Scaled neatly for corporate stationary
                logo_flowable = Image(logo_path, width=80, height=45)
            except Exception as e:
                print(f"Error rendering logo in letterhead: {e}")
                logo_flowable = ""

        # 2. IA / Entity details
        entity_name = ia_data.get("name_of_entity") or ia_data.get("name_of_ia") or "Investment Advisor"
        reg_no = ia_data.get("ia_registration_number")
        basl_id = ia_data.get("basl_membership_id")
        
        subtitle_lines = []
        if reg_no:
            subtitle_lines.append(f"RIA Reg No: {reg_no}")
        if basl_id:
            subtitle_lines.append(f"BASL ID: {basl_id}")
            
        header_right_html = f"<b>{entity_name.upper()}</b>"
        if subtitle_lines:
            header_right_html += f"<br/><font color='#475569'>{' | '.join(subtitle_lines)}</font>"
            
        p_header_right = Paragraph(header_right_html, title_style if not subtitle_lines else ParagraphStyle('HRight', parent=title_style, leading=13))

        # Put header elements in a 2-column Table
        header_data = [[logo_flowable, p_header_right]]
        header_table = Table(header_data, colWidths=[100, 387.27])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        
        header_table.wrapOn(canvas, 487.27, 60)
        header_table.drawOn(canvas, left_margin, 730)

        # 3. Dynamic Accent Bar
        canvas.setStrokeColor(brand_color)
        canvas.setLineWidth(2.0)
        canvas.line(left_margin, 720, right_margin, 720)

        # ─── FOOTER SECTION (Draws at y=35) ───
        
        # 1. Divider line above footer
        canvas.setStrokeColor(colors.HexColor("#e2e8f0")) # slate-200
        canvas.setLineWidth(0.5)
        canvas.line(left_margin, 90, right_margin, 90)

        # 2. Footer Typography
        footer_text_style = ParagraphStyle(
            'FooterText',
            parent=styles['Normal'],
            fontSize=7,
            leading=9.5,
            fontName='Helvetica',
            textColor=colors.HexColor("#334155") # slate-700
        )

        email = ia_data.get("registered_email_id")
        phone = ia_data.get("registered_contact_number")
        office_phone = ia_data.get("office_contact_number")
        address = ia_data.get("registered_address") or "Registered Office Address"
        po_name = ia_data.get("name_of_ia") or "Principal Officer"

        # Col 1: Contact
        contact_lines = []
        if phone:
            contact_lines.append(f"Phone: {phone}")
        if office_phone:
            contact_lines.append(f"Office: {office_phone}")
        if email:
            contact_lines.append(f"Email: {email}")
        contact_html = "<br/>".join(contact_lines) if contact_lines else "Contact details not provided"
        p_contact = Paragraph(f"<b>CONTACT DETAILS</b><br/>{contact_html}", footer_text_style)

        # Col 2: Regulatory Details
        creds_html = f"<b>REGULATORY INFORMATION</b><br/>Principal Officer: {po_name}"
        if reg_no:
            creds_html += f"<br/>Reg No: {reg_no}"
        if basl_id:
            creds_html += f"<br/>BASL Membership ID: {basl_id}"
        p_creds = Paragraph(creds_html, footer_text_style)

        # Col 3: Address
        p_address = Paragraph(f"<b>REGISTERED OFFICE</b><br/>{address}", footer_text_style)

        # Render 3-column table
        footer_data = [[p_contact, p_creds, p_address]]
        footer_table = Table(footer_data, colWidths=[150, 160, 177.27])
        footer_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        
        footer_table.wrapOn(canvas, 487.27, 50)
        footer_table.drawOn(canvas, left_margin, 35)

        # 3.Risk Disclaimer Footer
        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontSize=6,
            leading=7.5,
            alignment=1, # Centered
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor("#64748b") # slate-500
        )
        disclaimer_text = "<b>Disclaimer:</b> Registration granted by RIA, membership of BASL and certification from NISM in no way guarantee performance of the intermediary or provide any assurance of returns to investors. Investment in securities market are subject to market risks. Read all the related documents carefully before investing."
        p_disclaimer = Paragraph(disclaimer_text, disclaimer_style)
        
        p_disclaimer.wrapOn(canvas, 487.27, 20)
        p_disclaimer.drawOn(canvas, left_margin, 12)

        canvas.restoreState()

    doc.build(elements, onFirstPage=draw_letterhead, onLaterPages=draw_letterhead)
    buffer.seek(0)
    return buffer
