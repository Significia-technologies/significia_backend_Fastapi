import io
import os
import base64
from datetime import datetime
from typing import Optional, List

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.models.ia_master import IAMaster
from app.models.asset_allocation import AssetAllocation

DEFAULT_ASSET_ALLOCATION_DISCLAIMER = """This asset allocation report is prepared based on the client's risk profile and financial goals as assessed by the Investment Advisor. The allocation percentages represent a recommended distribution of investable assets and should be reviewed periodically. Past performance is not indicative of future results. This report does not constitute investment advice and is prepared solely for informational and planning purposes in accordance with SEBI Investment Advisor Regulations."""

class AssetAllocationReportUtils:
    @staticmethod
    def create_pie_chart(labels: List[str], sizes: List[float], title: str, custom_colors: Optional[List[str]] = None) -> bytes:
        """Create a pie chart and return as bytes"""
        if custom_colors is None:
            custom_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
        
        plt.figure(figsize=(4, 3))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=custom_colors[:len(labels)])
        plt.axis('equal')
        plt.title(title, fontsize=10, fontweight='bold', pad=10)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        
        return buffer.getvalue()

    @staticmethod
    def add_page_number(canvas, doc):
        """Add unified footer and page number to each page"""
        canvas.saveState()
        canvas.setFont("Helvetica-Oblique", 7)
        canvas.setFillColor(colors.grey)
        
        # Resolve data from doc object
        advisor_name = getattr(doc, 'advisor_name', '')
        entity_name = getattr(doc, 'entity_name', '')
        ia_reg_no = getattr(doc, 'ia_reg_no', '')
        
        footer_parts = []
        if advisor_name: footer_parts.append(f"Prepared by: {advisor_name}")
        if entity_name: footer_parts.append(f"Entity: {entity_name}")
        if ia_reg_no: footer_parts.append(f"Reg No: {ia_reg_no}")
        footer_text = " , ".join(footer_parts)
        
        # Footer text on left
        canvas.drawString(0.5 * inch, 0.4 * inch, footer_text)
        
        # Page Number on right
        canvas.setFont("Helvetica", 8)
        page_num = canvas.getPageNumber()
        page_text = f"Page {page_num}"
        canvas.drawRightString(letter[0] - 0.5 * inch, 0.4 * inch, page_text)
        canvas.restoreState()

    @staticmethod
    def generate_blank_pdf(ia_master: Optional[IAMaster], ia_logo_path: Optional[str] = None) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.8*inch)
        
        # Attach footer data to doc
        doc.advisor_name = getattr(ia_master, 'name_of_ia', None) if ia_master else None
        doc.entity_name = getattr(ia_master, 'name_of_entity', None) if ia_master else None
        doc.ia_reg_no = getattr(ia_master, 'ia_registration_number', None) if ia_master else None
        story = []
        styles = getSampleStyleSheet()

        # Custom styles (Same as generate_pdf)
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1a2980'),
            alignment=1,
            spaceAfter=40,
            fontName="Helvetica-Bold",
            leading=34
        )
        cover_subtitle_style = ParagraphStyle('CoverSubTitle', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#45B7D1'), alignment=1, spaceAfter=60, fontName="Helvetica")
        cover_client_style = ParagraphStyle('CoverClient', parent=styles['Normal'], fontSize=18, textColor=colors.black, alignment=1, spaceAfter=15, fontName="Helvetica-Bold")
        cover_info_style = ParagraphStyle('CoverInfo', parent=styles['Normal'], fontSize=12, textColor=colors.grey, alignment=1, spaceAfter=10, fontName="Helvetica")
        heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1a2980'), spaceAfter=12, spaceBefore=20)
        subheading_style = ParagraphStyle('SubheadingStyle', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#2a5298'), spaceAfter=8, spaceBefore=15)
        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, spaceAfter=6)

        # --- COVER PAGE ---
        story.append(Spacer(1, 1.5*inch))
        if ia_logo_path and os.path.exists(ia_logo_path):
            try:
                story.append(Image(ia_logo_path, width=2.5*inch, height=1.25*inch))
            except: pass
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("ASSET ALLOCATION FORM", cover_title_style))
        story.append(Paragraph("Strategic Portfolio Distribution Template", cover_subtitle_style))
        story.append(Spacer(1, 0.5*inch))
        
        story.append(Paragraph("Client Name: _________________________________", cover_client_style))
        story.append(Paragraph("Client Code: _________________________________", cover_info_style))
        story.append(Paragraph("Target Risk Profile: __________________________", cover_info_style))
        
        story.append(Spacer(1, 1.2*inch))
        if ia_master:
            story.append(Paragraph(f"<b>Investment Advisor:</b>", cover_info_style))
            story.append(Paragraph(f"{ia_master.name_of_ia}", cover_info_style))
            story.append(Paragraph(f"Registration No: {ia_master.ia_registration_number}", cover_info_style))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Date: ________________________", cover_info_style))
        story.append(PageBreak())

        # --- BLANK TABLES ---
        story.append(Paragraph("ASSET ALLOCATION DETAILS", heading_style))
        
        story.append(Paragraph("MAIN ASSET CLASS ALLOCATION", subheading_style))
        main_data = [
            ["Asset Class", "Allocation %"],
            ["Equities", "__________%"],
            ["Debt Securities", "__________%"],
            ["Commodities", "__________%"],
            ["TOTAL", "100.0%"]
        ]
        main_table = Table(main_data, colWidths=[2.5*inch, 1.5*inch])
        main_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(main_table)

        story.append(Paragraph("SUB-ASSET CLASSES (EQUITIES)", subheading_style))
        eq_data = [
            ["Sub-asset", "Allocation %", "Within Equities", "Within Total Portfolio"],
            ["Stocks", "______%", "______%", "______%"],
            ["Mutual Funds (Equity)", "______%", "______%", "______%"],
            ["ETF (Equity)", "______%", "______%", "______%"],
            ["ULIP (Equity)", "______%", "______%", "______%"],
            ["TOTAL", "100.0%", "100.0%", "______%"]
        ]
        eq_table = Table(eq_data, colWidths=[2.3*inch, 1.2*inch, 1.2*inch, 1.8*inch])
        eq_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        story.append(eq_table)

        story.append(Paragraph("SUB-ASSET CLASSES (DEBT)", subheading_style))
        debt_data = [
            ["Sub-asset", "Allocation %", "Within Debt", "Within Total Portfolio"],
            ["Fixed Deposits & Bonds", "______%", "______%", "______%"],
            ["Mutual Funds (Debt)", "______%", "______%", "______%"],
            ["ETF (Debt)", "______%", "______%", "______%"],
            ["ULIP (Debt)", "______%", "______%", "______%"],
            ["TOTAL", "100.0%", "100.0%", "______%"]
        ]
        debt_table = Table(debt_data, colWidths=[2.3*inch, 1.2*inch, 1.2*inch, 1.8*inch])
        debt_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        story.append(debt_table)

        story.append(Paragraph("SUB-ASSET CLASSES (COMMODITIES)", subheading_style))
        comm_data = [
            ["Sub-asset", "Allocation %", "Within Commodities", "Within Total Portfolio"],
            ["Gold ETF", "______%", "______%", "______%"],
            ["Silver ETF", "______%", "______%", "______%"],
            ["ETF", "______%", "______%", "______%"],
            ["TOTAL", "100.0%", "100.0%", "______%"]
        ]
        comm_table = Table(comm_data, colWidths=[2.3*inch, 1.2*inch, 1.2*inch, 1.8*inch])
        comm_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('FONTSIZE', (0,0), (-1,-1), 8)]))
        story.append(comm_table)

        # Blank Space for Conclusion/Notes
        story.append(Paragraph("Discussions", heading_style))
        story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 2.0*inch))

        story.append(Paragraph("DISCLAIMER", heading_style))
        story.append(Paragraph(DEFAULT_ASSET_ALLOCATION_DISCLAIMER, styles['Italic']))

        story.append(Paragraph("All inputs provided above have been discussed with and confirmed by the client", normal_style))
        story.append(Spacer(1, 15))
        # Signatures
        story.append(Spacer(1, 0.5*inch))
        sig_data = [
            [Paragraph("__________________________<br/><br/><b>Client Signature</b><br/><br/>Date: ________________", normal_style),
             Paragraph("__________________________<br/><br/><b>Advisor Signature</b><br/><br/>Date: ________________", normal_style)],
            [Paragraph("__________________________", normal_style),
             Paragraph(f"{ia_master.name_of_ia if ia_master else 'Investment Advisor'}", normal_style)]
        ]
        sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('BOTTOMPADDING', (0,0), (-1,0), 30)]))
        story.append(sig_table)

        doc.build(story, onFirstPage=AssetAllocationReportUtils.add_page_number, onLaterPages=AssetAllocationReportUtils.add_page_number)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_existing_blank_pdf(ia_master: Optional[IAMaster], ia_logo_path: Optional[str] = None) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.8*inch)
        
        # Attach footer data to doc
        doc.advisor_name = getattr(ia_master, 'name_of_ia', None) if ia_master else None
        doc.entity_name = getattr(ia_master, 'name_of_entity', None) if ia_master else None
        doc.ia_reg_no = getattr(ia_master, 'ia_registration_number', None) if ia_master else None
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#1a2980'),
            alignment=1,
            spaceAfter=40,
            fontName="Helvetica-Bold",
            leading=32
        )
        cover_subtitle_style = ParagraphStyle('CoverSubTitle', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#45B7D1'), alignment=1, spaceAfter=60, fontName="Helvetica")
        cover_client_style = ParagraphStyle('CoverClient', parent=styles['Normal'], fontSize=18, textColor=colors.black, alignment=1, spaceAfter=15, fontName="Helvetica-Bold")
        cover_info_style = ParagraphStyle('CoverInfo', parent=styles['Normal'], fontSize=12, textColor=colors.grey, alignment=1, spaceAfter=10, fontName="Helvetica")
        heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1a2980'), spaceAfter=12, spaceBefore=20)
        subheading_style = ParagraphStyle('SubheadingStyle', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#2a5298'), spaceAfter=8, spaceBefore=15)
        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, spaceAfter=6)

        # --- COVER PAGE ---
        story.append(Spacer(1, 1.0*inch))
        if ia_logo_path and os.path.exists(ia_logo_path):
            try:
                story.append(Image(ia_logo_path, width=2.5*inch, height=1.25*inch))
            except: pass
        
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph("EXISTING ASSET ALLOCATION FORM", cover_title_style))
        story.append(Paragraph("Current Portfolio Valuation Template", cover_subtitle_style))
        story.append(Spacer(1, 0.4*inch))
        
        # Grid metadata block for Client Info
        label_style = ParagraphStyle('FormLabel', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=10, textColor=colors.HexColor('#1e293b'))
        fields_data = [
            [Paragraph("<b>Client Name</b>", label_style), ""],
            [Paragraph("<b>Client Code</b>", label_style), ""],
            [Paragraph("<b>Assigned Risk Tier</b>", label_style), ""],
            [Paragraph("<b>Date</b>", label_style), datetime.now().strftime('%d %B, %Y')]
        ]
        # Total width 6.0 inches
        fields_table = Table(fields_data, colWidths=[1.8*inch, 4.2*inch], rowHeights=28)
        fields_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        story.append(fields_table)
        
        story.append(Spacer(1, 1.0*inch))
        if ia_master:
            story.append(Paragraph(f"<b>Investment Advisor:</b>", cover_info_style))
            story.append(Paragraph(f"{ia_master.name_of_ia}", cover_info_style))
            story.append(Paragraph(f"Registration No: {ia_master.ia_registration_number}", cover_info_style))
        
        story.append(PageBreak())

        # --- BLANK TABLES ---
        story.append(Paragraph("EXISTING PORTFOLIO ALLOCATION WITH VALUES", heading_style))
        story.append(Paragraph("Please write down the current valuation amounts (in Rs.) for all assets you hold in the columns below. The Investment Advisor will calculate the final percentages.", normal_style))
        story.append(Spacer(1, 0.15*inch))

        table_data = [
            ["Asset Category", "Sub-Asset Class", "Holding Amount (Rs.)"],
            # Equities
            ["Equities", "Share", "Rs. __________________"],
            ["", "Mutual Fund", "Rs. __________________"],
            ["", "ULIP", "Rs. __________________"],
            ["", "ETF", "Rs. __________________"],
            ["", "Total Equities", "Rs. __________________"],
            # Debt
            ["Debt Securities", "Fixed Deposits & Bonds", "Rs. __________________"],
            ["", "Mutual Funds (Debt)", "Rs. __________________"],
            ["", "ETF (Debt)", "Rs. __________________"],
            ["", "ULIP (Debt)", "Rs. __________________"],
            ["", "Total Debt", "Rs. __________________"],
            # Commodities
            ["Commodities", "Gold ETF", "Rs. __________________"],
            ["", "Silver ETF", "Rs. __________________"],
            ["", "ETF (Commodity)", "Rs. __________________"],
            ["", "Total Commodities", "Rs. __________________"],
            # Grand Total
            ["GRAND TOTAL", "PORTFOLIO VALUATION", "Rs. __________________"]
        ]

        # 7.0 inch total width
        t = Table(table_data, colWidths=[2.2*inch, 2.6*inch, 2.2*inch])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('PADDING', (0,0), (-1,-1), 7),
            
            # Category spans
            ('SPAN', (0, 1), (0, 5)),
            ('SPAN', (0, 6), (0, 10)),
            ('SPAN', (0, 11), (0, 14)),
            
            # Grand total span
            ('SPAN', (0, 15), (1, 15)),
            
            # Make the category totals stand out
            ('BACKGROUND', (1, 5), (2, 5), colors.HexColor('#f8fafc')),
            ('FONTNAME', (1, 5), (2, 5), 'Helvetica-Bold'),
            ('BACKGROUND', (1, 10), (2, 10), colors.HexColor('#f8fafc')),
            ('FONTNAME', (1, 10), (2, 10), 'Helvetica-Bold'),
            ('BACKGROUND', (1, 14), (2, 14), colors.HexColor('#f8fafc')),
            ('FONTNAME', (1, 14), (2, 14), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 15), (-1, 15), colors.lightgrey),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 0.2*inch))

        # Regulatory Disclaimer
        story.append(Paragraph("DISCLAIMER", heading_style))
        story.append(Paragraph(DEFAULT_ASSET_ALLOCATION_DISCLAIMER, styles['Italic']))

        story.append(Paragraph("All inputs provided above have been discussed with and confirmed by the client", normal_style))
        story.append(Spacer(1, 15))
        # Signatures
        story.append(Spacer(1, 0.5*inch))
        sig_data = [
            [Paragraph("__________________________<br/><br/><b>Client Signature</b><br/><br/>Date: ________________", normal_style),
             Paragraph("__________________________<br/><br/><b>Advisor Signature</b><br/><br/>Date: ________________", normal_style)],
            [Paragraph("__________________________", normal_style),
             Paragraph(f"{ia_master.name_of_ia if ia_master else 'Investment Advisor'}", normal_style)]
        ]
        sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('BOTTOMPADDING', (0,0), (-1,0), 30)]))
        story.append(sig_table)

        doc.build(story, onFirstPage=AssetAllocationReportUtils.add_page_number, onLaterPages=AssetAllocationReportUtils.add_page_number)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_existing_pdf(
        allocation_data: dict, ia_master: Optional[any], ia_logo_path: Optional[str] = None
    ) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.8*inch)
        
        # Attach footer data to doc
        doc.advisor_name = getattr(ia_master, 'name_of_ia', None) or (ia_master.get('name_of_ia') if isinstance(ia_master, dict) else None)
        doc.entity_name = getattr(ia_master, 'name_of_entity', None) or (ia_master.get('name_of_entity') if isinstance(ia_master, dict) else None)
        doc.ia_reg_no = getattr(ia_master, 'ia_registration_number', None) or (ia_master.get('ia_registration_number') if isinstance(ia_master, dict) else (ia_master.get('registration_no') if isinstance(ia_master, dict) else None))
        
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=26,
            textColor=colors.HexColor('#1a2980'),
            alignment=1,
            spaceAfter=40,
            fontName="Helvetica-Bold",
            leading=32
        )
        cover_subtitle_style = ParagraphStyle('CoverSubTitle', parent=styles['Normal'], fontSize=16, textColor=colors.HexColor('#45B7D1'), alignment=1, spaceAfter=60, fontName="Helvetica")
        cover_client_style = ParagraphStyle('CoverClient', parent=styles['Normal'], fontSize=18, textColor=colors.black, alignment=1, spaceAfter=15, fontName="Helvetica-Bold")
        cover_info_style = ParagraphStyle('CoverInfo', parent=styles['Normal'], fontSize=12, textColor=colors.grey, alignment=1, spaceAfter=10, fontName="Helvetica")
        heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1a2980'), spaceAfter=12, spaceBefore=20)
        subheading_style = ParagraphStyle('SubheadingStyle', parent=styles['Heading3'], fontSize=12, textColor=colors.HexColor('#2a5298'), spaceAfter=8, spaceBefore=15)
        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontSize=10, spaceAfter=6)

        # --- COVER PAGE ---
        story.append(Spacer(1, 1.0*inch))
        if ia_logo_path and os.path.exists(ia_logo_path):
            try:
                story.append(Image(ia_logo_path, width=2.5*inch, height=1.25*inch))
            except: pass
        
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph("EXISTING ASSET ALLOCATION REPORT", cover_title_style))
        story.append(Paragraph("Existing Portfolio Allocation with values", cover_subtitle_style))
        story.append(Spacer(1, 0.4*inch))
        
        # Grid metadata block for Client Info
        created_at_str = allocation_data.get("created_at")
        date_str = ""
        if created_at_str:
            try:
                if created_at_str.endswith('Z'):
                    created_at_str = created_at_str[:-1] + '+00:00'
                dt = datetime.fromisoformat(created_at_str)
                date_str = dt.strftime('%d %B, %Y')
            except:
                date_str = datetime.now().strftime('%d %B, %Y')
        else:
            date_str = datetime.now().strftime('%d %B, %Y')

        label_style = ParagraphStyle('FormLabel', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=10, textColor=colors.HexColor('#1e293b'))
        val_style = ParagraphStyle('FormVal', parent=styles['Normal'], fontSize=9, fontName='Helvetica', leading=10, textColor=colors.black)
        
        client_name = allocation_data.get("client_name") or "____________________________"
        client_code = (allocation_data.get("client_code") or "________________").upper()
        risk_tier = allocation_data.get("assigned_risk_tier") or "________________"

        fields_data = [
            [Paragraph("<b>Client Name</b>", label_style), Paragraph(client_name, val_style)],
            [Paragraph("<b>Client Code</b>", label_style), Paragraph(client_code, val_style)],
            [Paragraph("<b>Assigned Risk Tier</b>", label_style), Paragraph(risk_tier, val_style)],
            [Paragraph("<b>Date</b>", label_style), Paragraph(date_str, val_style)]
        ]
        # Total width 6.0 inches
        fields_table = Table(fields_data, colWidths=[1.8*inch, 4.2*inch], rowHeights=28)
        fields_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        story.append(fields_table)
        
        story.append(Spacer(1, 1.0*inch))
        
        advisor_name = doc.advisor_name or "Investment Advisor"
        ia_reg_no = doc.ia_reg_no or "N/A"
        
        story.append(Paragraph(f"<b>Investment Advisor:</b>", cover_info_style))
        story.append(Paragraph(f"{advisor_name}", cover_info_style))
        if ia_reg_no:
            story.append(Paragraph(f"Registration No: {ia_reg_no}", cover_info_style))
        
        story.append(PageBreak())

        # --- REPORT TABLE ---
        story.append(Paragraph("EXISTING PORTFOLIO ALLOCATION WITH VALUES", heading_style))
        story.append(Paragraph("The table below details your current holdings, along with the category breakdown and total portfolio percentages.", normal_style))
        story.append(Spacer(1, 0.15*inch))

        def get_val(key):
            val = allocation_data.get(key)
            return float(val) if val is not None else 0.0

        stocks = get_val("stocks_amount")
        mf_eq = get_val("mutual_fund_equity_amount")
        ulip_eq = get_val("ulip_equity_amount")
        etf_eq = get_val("etf_equity_amount")
        eq_total = get_val("equities_amount")

        fd_bonds = get_val("fixed_deposits_bonds_amount")
        mf_debt = get_val("mutual_fund_debt_amount")
        etf_debt = get_val("etf_debt_amount")
        ulip_debt = get_val("ulip_debt_amount")
        debt_total = get_val("debt_securities_amount")

        gold = get_val("gold_etf_amount")
        silver = get_val("silver_etf_amount")
        etf_comm = get_val("etf_commodity_amount")
        comm_total = get_val("commodities_amount")

        total = get_val("total_amount")

        # Recalculate totals and percentages dynamically if total is 0.0 to prevent division by zero, and align perfectly.
        if total <= 0.0:
            total = eq_total + debt_total + comm_total

        # Recalculate percentages to match amounts perfectly and prevent any mismatch.
        if total > 0.0:
            stocks_port = (stocks / total) * 100
            mf_eq_port = (mf_eq / total) * 100
            ulip_eq_port = (ulip_eq / total) * 100
            etf_eq_port = (etf_eq / total) * 100
            eq_total_port = (eq_total / total) * 100

            fd_bonds_port = (fd_bonds / total) * 100
            mf_debt_port = (mf_debt / total) * 100
            etf_debt_port = (etf_debt / total) * 100
            ulip_debt_port = (ulip_debt / total) * 100
            debt_total_port = (debt_total / total) * 100

            gold_port = (gold / total) * 100
            silver_port = (silver / total) * 100
            etf_comm_port = (etf_comm / total) * 100
            comm_total_port = (comm_total / total) * 100
        else:
            stocks_port = mf_eq_port = ulip_eq_port = etf_eq_port = eq_total_port = 0.0
            fd_bonds_port = mf_debt_port = etf_debt_port = ulip_debt_port = debt_total_port = 0.0
            gold_port = silver_port = etf_comm_port = comm_total_port = 0.0

        if eq_total > 0.0:
            stocks_cat = (stocks / eq_total) * 100
            mf_eq_cat = (mf_eq / eq_total) * 100
            ulip_eq_cat = (ulip_eq / eq_total) * 100
            etf_eq_cat = (etf_eq / eq_total) * 100
        else:
            stocks_cat = mf_eq_cat = ulip_eq_cat = etf_eq_cat = 0.0

        if debt_total > 0.0:
            fd_bonds_cat = (fd_bonds / debt_total) * 100
            mf_debt_cat = (mf_debt / debt_total) * 100
            etf_debt_cat = (etf_debt / debt_total) * 100
            ulip_debt_cat = (ulip_debt / debt_total) * 100
        else:
            fd_bonds_cat = mf_debt_cat = etf_debt_cat = ulip_debt_cat = 0.0

        if comm_total > 0.0:
            gold_cat = (gold / comm_total) * 100
            silver_cat = (silver / comm_total) * 100
            etf_comm_cat = (etf_comm / comm_total) * 100
        else:
            gold_cat = silver_cat = etf_comm_cat = 0.0

        table_data = [
            ["Asset Category", "Sub-Asset Class", "Holding Amount (Rs.)", "Category %", "Portfolio %"],
            
            # Equities
            ["Equities", "Share", f"Rs. {stocks:,.2f}", f"{stocks_cat:.1f}%", f"{stocks_port:.1f}%"],
            ["", "Mutual Fund", f"Rs. {mf_eq:,.2f}", f"{mf_eq_cat:.1f}%", f"{mf_eq_port:.1f}%"],
            ["", "ULIP", f"Rs. {ulip_eq:,.2f}", f"{ulip_eq_cat:.1f}%", f"{ulip_eq_port:.1f}%"],
            ["", "ETF", f"Rs. {etf_eq:,.2f}", f"{etf_eq_cat:.1f}%", f"{etf_eq_port:.1f}%"],
            ["", "Total Equities", f"Rs. {eq_total:,.2f}", "100.0%", f"{eq_total_port:.1f}%"],
            
            # Debt
            ["Debt Securities", "Fixed Deposits & Bonds", f"Rs. {fd_bonds:,.2f}", f"{fd_bonds_cat:.1f}%", f"{fd_bonds_port:.1f}%"],
            ["", "Mutual Funds (Debt)", f"Rs. {mf_debt:,.2f}", f"{mf_debt_cat:.1f}%", f"{mf_debt_port:.1f}%"],
            ["", "ETF (Debt)", f"Rs. {etf_debt:,.2f}", f"{etf_debt_cat:.1f}%", f"{etf_debt_port:.1f}%"],
            ["", "ULIP (Debt)", f"Rs. {ulip_debt:,.2f}", f"{ulip_debt_cat:.1f}%", f"{ulip_debt_port:.1f}%"],
            ["", "Total Debt", f"Rs. {debt_total:,.2f}", "100.0%", f"{debt_total_port:.1f}%"],
            
            # Commodities
            ["Commodities", "Gold ETF", f"Rs. {gold:,.2f}", f"{gold_cat:.1f}%", f"{gold_port:.1f}%"],
            ["", "Silver ETF", f"Rs. {silver:,.2f}", f"{silver_cat:.1f}%", f"{silver_port:.1f}%"],
            ["", "ETF (Commodity)", f"Rs. {etf_comm:,.2f}", f"{etf_comm_cat:.1f}%", f"{etf_comm_port:.1f}%"],
            ["", "Total Commodities", f"Rs. {comm_total:,.2f}", "100.0%", f"{comm_total_port:.1f}%"],
            
            # Grand Total
            ["GRAND TOTAL", "PORTFOLIO VALUATION", f"Rs. {total:,.2f}", "-", "100.0%"]
        ]

        t = Table(table_data, colWidths=[1.8*inch, 2.0*inch, 1.4*inch, 0.9*inch, 0.9*inch])
        t.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('PADDING', (0,0), (-1,-1), 6),
            
            # Category spans
            ('SPAN', (0, 1), (0, 5)),
            ('SPAN', (0, 6), (0, 10)),
            ('SPAN', (0, 11), (0, 14)),
            
            # Grand total span
            ('SPAN', (0, 15), (1, 15)),
            
            # Make the category totals stand out
            ('BACKGROUND', (1, 5), (4, 5), colors.HexColor('#f8fafc')),
            ('FONTNAME', (1, 5), (4, 5), 'Helvetica-Bold'),
            ('BACKGROUND', (1, 10), (4, 10), colors.HexColor('#f8fafc')),
            ('FONTNAME', (1, 10), (4, 10), 'Helvetica-Bold'),
            ('BACKGROUND', (1, 14), (4, 14), colors.HexColor('#f8fafc')),
            ('FONTNAME', (1, 14), (4, 14), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 15), (-1, 15), colors.lightgrey),
        ]))
        
        story.append(t)
        story.append(Spacer(1, 0.15*inch))

        # Regulatory Disclaimer
        story.append(Paragraph("DISCLAIMER", heading_style))
        story.append(Paragraph(DEFAULT_ASSET_ALLOCATION_DISCLAIMER, styles['Italic']))

        custom_disclaimer = allocation_data.get("disclaimer_text")
        if custom_disclaimer:
            story.append(Spacer(1, 5))
            story.append(Paragraph(custom_disclaimer, styles['Italic']))

        story.append(Paragraph("All inputs provided above have been discussed with and confirmed by the client", normal_style))
        story.append(Spacer(1, 15))
        
        # Signatures
        story.append(Spacer(1, 0.4*inch))
        sig_data = [
            [Paragraph("__________________________<br/><br/><b>Client Signature</b><br/><br/>Date: ________________", normal_style),
             Paragraph("__________________________<br/><br/><b>Advisor Signature</b><br/><br/>Date: ________________", normal_style)],
            [Paragraph(f"{client_name}", normal_style),
             Paragraph(f"{advisor_name}", normal_style)]
        ]
        sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'BOTTOM'), ('BOTTOMPADDING', (0,0), (-1,0), 30)]))
        story.append(sig_table)

        doc.build(story, onFirstPage=AssetAllocationReportUtils.add_page_number, onLaterPages=AssetAllocationReportUtils.add_page_number)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_pdf(
        allocation: AssetAllocation, ia_master: Optional[IAMaster], ia_logo_path: Optional[str] = None) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.8*inch)
        
        # Attach footer data to doc
        doc.advisor_name = getattr(ia_master, 'name_of_ia', None) if ia_master else None
        doc.entity_name = getattr(ia_master, 'name_of_entity', None) if ia_master else None
        doc.ia_reg_no = getattr(ia_master, 'ia_registration_number', None) if ia_master else None
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        # Custom styles
        cover_title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#1a2980'),
            alignment=1,
            spaceAfter=40,
            fontName="Helvetica-Bold",
            leading=34
        )

        cover_subtitle_style = ParagraphStyle(
            'CoverSubTitle',
            parent=styles['Normal'],
            fontSize=16,
            textColor=colors.HexColor('#45B7D1'),
            alignment=1,
            spaceAfter=60,
            fontName="Helvetica"
        )

        cover_client_style = ParagraphStyle(
            'CoverClient',
            parent=styles['Normal'],
            fontSize=18,
            textColor=colors.black,
            alignment=1,
            spaceAfter=15,
            fontName="Helvetica-Bold"
        )

        cover_info_style = ParagraphStyle(
            'CoverInfo',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            alignment=1,
            spaceAfter=10,
            fontName="Helvetica"
        )

        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1a2980'),
            spaceAfter=12,
            spaceBefore=20
        )

        subheading_style = ParagraphStyle(
            'SubheadingStyle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#2a5298'),
            spaceAfter=8,
            spaceBefore=15
        )

        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1a2980'),
            spaceAfter=20,
            alignment=1
        )

        # --- COVER PAGE ---
        story.append(Spacer(1, 1.5*inch))
        
        # Centered Logo on Cover
        if ia_logo_path and os.path.exists(ia_logo_path):
            try:
                logo_img = Image(ia_logo_path, width=2.5*inch, height=1.25*inch)
                story.append(logo_img)
            except:
                pass
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph("ASSET ALLOCATION REPORT", cover_title_style))
        story.append(Paragraph("Strategic Portfolio Distribution Details", cover_subtitle_style))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Client: {allocation.client.client_name}", cover_client_style))
        story.append(Paragraph(f"Code: {allocation.client.client_code.upper()}", cover_info_style))
        story.append(Paragraph(f"Risk Profile: {allocation.assigned_risk_tier}", cover_info_style))
        
        story.append(Spacer(1, 1.2*inch))
        
        if ia_master:
            story.append(Paragraph(f"<b>Prepared By:</b>", cover_info_style))
            story.append(Paragraph(f"{ia_master.name_of_ia}", cover_info_style))
            story.append(Paragraph(f"SEBI Registration No: {ia_master.ia_registration_number}", cover_info_style))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Report Date: {datetime.now().strftime('%d %B, %Y')}", cover_info_style))
        
        story.append(PageBreak())

        # --- MAIN REPORT CONTENT ---
        # The report starts directly on page 2 after the cover page.
        story.append(Paragraph("ASSET ALLOCATION SUMMARY", heading_style))
        
        # Main Allocation
        story.append(Paragraph("MAIN ASSET CLASS ALLOCATION", subheading_style))
        main_data = [
            ["Asset Class", "Allocation %"],
            ["Equities", f"{allocation.equities_percentage:.1f}%"],
            ["Debt Securities", f"{allocation.debt_securities_percentage:.1f}%"],
            ["Commodities", f"{allocation.commodities_percentage:.1f}%"],
            ["TOTAL", f"{allocation.total_allocation:.1f}%"]
        ]
        main_table = Table(main_data, colWidths=[2.5*inch, 1.5*inch])
        main_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(main_table)
        
        # Pie Chart for Main Allocation
        if allocation.total_allocation > 0:
            labels = []
            sizes = []
            colors_list = []
            if allocation.equities_percentage > 0:
                labels.append('Equities')
                sizes.append(allocation.equities_percentage)
                colors_list.append('#FF6B6B')
            if allocation.debt_securities_percentage > 0:
                labels.append('Debt')
                sizes.append(allocation.debt_securities_percentage)
                colors_list.append('#4ECDC4')
            if allocation.commodities_percentage > 0:
                labels.append('Commodities')
                sizes.append(allocation.commodities_percentage)
                colors_list.append('#45B7D1')
            
            if sizes:
                chart_bytes = AssetAllocationReportUtils.create_pie_chart(labels, sizes, "Main Asset Class Allocation", colors_list)
                img = Image(io.BytesIO(chart_bytes), width=2.5*inch, height=2*inch)
                story.append(Spacer(1, 10))
                story.append(img)

        # Sub-Asset Details (Equities)
        if allocation.equities_percentage > 0:
            story.append(Paragraph("EQUITIES SUB-ASSET ALLOCATION", subheading_style))
            eq_data = [
                ["Sub-asset", "Allocation %", "Within Equities", "Within Total Portfolio"],
                ["Stocks", f"{allocation.stocks_percentage:.1f}%", f"{allocation.stocks_percentage:.1f}%", f"{(allocation.stocks_percentage * allocation.equities_percentage / 100):.1f}%"],
                ["Mutual Funds (Equity)", f"{allocation.mutual_fund_equity_percentage:.1f}%", f"{allocation.mutual_fund_equity_percentage:.1f}%", f"{(allocation.mutual_fund_equity_percentage * allocation.equities_percentage / 100):.1f}%"],
                ["ETF (Equity)", f"{allocation.etf_equity_percentage:.1f}%", f"{allocation.etf_equity_percentage:.1f}%", f"{(allocation.etf_equity_percentage * allocation.equities_percentage / 100):.1f}%"],
                ["ULIP (Equity)", f"{allocation.ulip_equity_percentage:.1f}%", f"{allocation.ulip_equity_percentage:.1f}%", f"{(allocation.ulip_equity_percentage * allocation.equities_percentage / 100):.1f}%"],
                ["TOTAL", "100.0%", "100.0%", f"{allocation.equities_percentage:.1f}%"]
            ]
            eq_table = Table(eq_data, colWidths=[2.3*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            eq_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('PADDING', (0,0), (-1,-1), 4),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(eq_table)

            # Pie Chart for Equities
            eq_labels = []
            eq_sizes = []
            if allocation.stocks_percentage > 0: eq_labels.append('Stocks'); eq_sizes.append(allocation.stocks_percentage)
            if allocation.mutual_fund_equity_percentage > 0: eq_labels.append('Mutual Funds'); eq_sizes.append(allocation.mutual_fund_equity_percentage)
            if allocation.etf_equity_percentage > 0: eq_labels.append('ETF'); eq_sizes.append(allocation.etf_equity_percentage)
            if allocation.ulip_equity_percentage > 0: eq_labels.append('ULIP'); eq_sizes.append(allocation.ulip_equity_percentage)
            
            if eq_sizes:
                chart_bytes = AssetAllocationReportUtils.create_pie_chart(eq_labels, eq_sizes, "Equities Sub-Asset Allocation", ['#ef4444', '#f06565', '#f38787', '#f87171'])
                img = Image(io.BytesIO(chart_bytes), width=2.5*inch, height=2*inch)
                story.append(Spacer(1, 10))
                story.append(img)
            story.append(Spacer(1, 15))

        # Sub-Asset Details (Debt)
        if allocation.debt_securities_percentage > 0:
            story.append(Paragraph("DEBT SECURITIES SUB-ASSET ALLOCATION", subheading_style))
            debt_data = [
                ["Sub-asset", "Allocation %", "Within Debt", "Within Total Portfolio"],
                ["Fixed Deposits & Bonds", f"{allocation.fixed_deposits_bonds_percentage:.1f}%", f"{allocation.fixed_deposits_bonds_percentage:.1f}%", f"{(allocation.fixed_deposits_bonds_percentage * allocation.debt_securities_percentage / 100):.1f}%"],
                ["Mutual Funds (Debt)", f"{allocation.mutual_fund_debt_percentage:.1f}%", f"{allocation.mutual_fund_debt_percentage:.1f}%", f"{(allocation.mutual_fund_debt_percentage * allocation.debt_securities_percentage / 100):.1f}%"],
                ["ETF (Debt)", f"{allocation.etf_debt_percentage:.1f}%", f"{allocation.etf_debt_percentage:.1f}%", f"{(allocation.etf_debt_percentage * allocation.debt_securities_percentage / 100):.1f}%"],
                ["ULIP (Debt)", f"{allocation.ulip_debt_percentage:.1f}%", f"{allocation.ulip_debt_percentage:.1f}%", f"{(allocation.ulip_debt_percentage * allocation.debt_securities_percentage / 100):.1f}%"],
                ["TOTAL", "100.0%", "100.0%", f"{allocation.debt_securities_percentage:.1f}%"]
            ]
            debt_table = Table(debt_data, colWidths=[2.3*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            debt_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('PADDING', (0,0), (-1,-1), 4),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(debt_table)

            # Pie Chart for Debt
            debt_labels = []
            debt_sizes = []
            if allocation.fixed_deposits_bonds_percentage > 0: debt_labels.append('FD/Bonds'); debt_sizes.append(allocation.fixed_deposits_bonds_percentage)
            if allocation.mutual_fund_debt_percentage > 0: debt_labels.append('Mutual Funds'); debt_sizes.append(allocation.mutual_fund_debt_percentage)
            if allocation.etf_debt_percentage > 0: debt_labels.append('ETF'); debt_sizes.append(allocation.etf_debt_percentage)
            if allocation.ulip_debt_percentage > 0: debt_labels.append('ULIP'); debt_sizes.append(allocation.ulip_debt_percentage)
            
            if debt_sizes:
                chart_bytes = AssetAllocationReportUtils.create_pie_chart(debt_labels, debt_sizes, "Debt Sub-Asset Allocation", ['#3b82f6', '#619bf8', '#88b4fa', '#93c5fd'])
                img = Image(io.BytesIO(chart_bytes), width=2.5*inch, height=2*inch)
                story.append(Spacer(1, 10))
                story.append(img)
            story.append(Spacer(1, 15))

        # Sub-Asset Details (Commodities)
        if allocation.commodities_percentage > 0:
            story.append(Paragraph("COMMODITIES SUB-ASSET ALLOCATION", subheading_style))
            comm_data = [
                ["Sub-asset", "Allocation %", "Within Commodities", "Within Total Portfolio"],
                ["Gold ETF", f"{allocation.gold_etf_percentage:.1f}%", f"{allocation.gold_etf_percentage:.1f}%", f"{(allocation.gold_etf_percentage * allocation.commodities_percentage / 100):.1f}%"],
                ["Silver ETF", f"{allocation.silver_etf_percentage:.1f}%", f"{allocation.silver_etf_percentage:.1f}%", f"{(allocation.silver_etf_percentage * allocation.commodities_percentage / 100):.1f}%"],
                ["ETF", f"{allocation.etf_commodity_percentage:.1f}%", f"{allocation.etf_commodity_percentage:.1f}%", f"{(allocation.etf_commodity_percentage * allocation.commodities_percentage / 100):.1f}%"],
                ["TOTAL", "100.0%", "100.0%", f"{allocation.commodities_percentage:.1f}%"]
            ]
            comm_table = Table(comm_data, colWidths=[2.3*inch, 1.2*inch, 1.2*inch, 1.8*inch])
            comm_table.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('PADDING', (0,0), (-1,-1), 4),
                ('FONTSIZE', (0,0), (-1,-1), 8),
            ]))
            story.append(comm_table)

            # Pie Chart for Commodities
            comm_labels = []
            comm_sizes = []
            if allocation.gold_etf_percentage > 0: comm_labels.append('Gold ETF'); comm_sizes.append(allocation.gold_etf_percentage)
            if allocation.silver_etf_percentage > 0: comm_labels.append('Silver ETF'); comm_sizes.append(allocation.silver_etf_percentage)
            if allocation.etf_commodity_percentage > 0: comm_labels.append('ETF'); comm_sizes.append(allocation.etf_commodity_percentage)
            
            if comm_sizes:
                chart_bytes = AssetAllocationReportUtils.create_pie_chart(comm_labels, comm_sizes, "Commodities Sub-Asset Allocation", ['#f59e0b', '#f7b13c', '#fac56d', '#fcd34d'])
                img = Image(io.BytesIO(chart_bytes), width=2.5*inch, height=2*inch)
                story.append(Spacer(1, 10))
                story.append(img)
            story.append(Spacer(1, 15))

        # Advisor Recommendation
        if allocation.tier_recommendation:
            story.append(Paragraph("ADVISOR RECOMMENDATION", heading_style))
            story.append(Paragraph(allocation.tier_recommendation, normal_style))
            story.append(Spacer(1, 10))

        # System Conclusion
        if allocation.system_conclusion:
            story.append(Paragraph("CONCLUSION", heading_style))
            for part in allocation.system_conclusion.split('\n\n'):
                story.append(Paragraph(part.replace('\n', '<br/>'), normal_style))
                story.append(Spacer(1, 6))

        # Disclaimer
        story.append(Paragraph("DISCLAIMER", heading_style))
        story.append(Paragraph(DEFAULT_ASSET_ALLOCATION_DISCLAIMER, styles['Italic']))
        
        if allocation.disclaimer_text:
            story.append(Spacer(1, 10))
            story.append(Paragraph(allocation.disclaimer_text, styles['Italic']))

        # Discussion Notes
        if allocation.discussion_notes:
            story.append(Paragraph("DISCUSSION NOTES", heading_style))
            story.append(Paragraph(allocation.discussion_notes, normal_style))
            story.append(Spacer(1, 15))

        # --- SIGNATURE SECTION ---
        story.append(Spacer(1, 0.5*inch))
        # Style for signatures with more spacing
        sig_style = ParagraphStyle(
            'SigStyle',
            parent=normal_style,
            leading=16  # Increased vertical spacing
        )
        
        sig_data = [
            [
                Paragraph("__________________________<br/><br/><b>Client Signature</b><br/><br/>Date: ________________", sig_style),
                Paragraph("__________________________<br/><br/><b>Advisor Signature</b><br/><br/>Date: ________________", sig_style)
            ],
            [
                Paragraph(f"{allocation.client.client_name}", sig_style),
                Paragraph(f"{ia_master.name_of_ia if ia_master else 'Investment Advisor'}", sig_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('BOTTOMPADDING', (0,0), (-1,0), 30),
        ]))
        story.append(sig_table)

        doc.build(story, onFirstPage=AssetAllocationReportUtils.add_page_number, onLaterPages=AssetAllocationReportUtils.add_page_number)
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_comparison_pdf(
        existing_data: dict, target_data: dict, ia_master: Optional[any], ia_logo_path: Optional[str] = None
    ) -> io.BytesIO:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.4*inch, bottomMargin=0.8*inch)
        
        # Attach footer data to doc
        doc.advisor_name = getattr(ia_master, 'name_of_ia', None) or (ia_master.get('name_of_ia') if isinstance(ia_master, dict) else None)
        doc.entity_name = getattr(ia_master, 'name_of_entity', None) or (ia_master.get('name_of_entity') if isinstance(ia_master, dict) else None)
        doc.ia_reg_no = getattr(ia_master, 'ia_registration_number', None) or (ia_master.get('ia_registration_number') if isinstance(ia_master, dict) else (ia_master.get('registration_no') if isinstance(ia_master, dict) else None))
        
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        cover_title_style = ParagraphStyle(
            'CoverTitleCompare',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a2980'),
            alignment=1,
            spaceAfter=30,
            fontName="Helvetica-Bold",
            leading=30
        )
        cover_subtitle_style = ParagraphStyle('CoverSubTitleCompare', parent=styles['Normal'], fontSize=15, textColor=colors.HexColor('#45B7D1'), alignment=1, spaceAfter=50, fontName="Helvetica")
        heading_style = ParagraphStyle('HeadingStyleCompare', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#1a2980'), spaceAfter=8, spaceBefore=15, fontName="Helvetica-Bold")
        normal_style = ParagraphStyle('NormalStyleCompare', parent=styles['Normal'], fontSize=8.5, spaceAfter=5)
        
        # --- COVER PAGE ---
        story.append(Spacer(1, 1.0*inch))
        if ia_logo_path and os.path.exists(ia_logo_path):
            try:
                story.append(Image(ia_logo_path, width=2.5*inch, height=1.25*inch))
            except: pass
        
        story.append(Spacer(1, 0.4*inch))
        story.append(Paragraph("PORTFOLIO ALLOCATION COMPARISON REPORT", cover_title_style))
        story.append(Paragraph("Current Holdings vs. Strategic Target Allocations", cover_subtitle_style))
        story.append(Spacer(1, 0.4*inch))
        
        # Grid metadata block for Client Info
        label_style = ParagraphStyle('FormLabelCompare', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=10, textColor=colors.HexColor('#1e293b'))
        val_style = ParagraphStyle('FormValCompare', parent=styles['Normal'], fontSize=9, fontName='Helvetica', leading=10, textColor=colors.black)

        def _parse_date(raw: str) -> str:
            if not raw:
                return "—"
            try:
                if raw.endswith('Z'):
                    raw = raw[:-1] + '+00:00'
                return datetime.fromisoformat(raw).strftime('%d %B, %Y')
            except:
                return raw

        existing_date_str = _parse_date(existing_data.get("created_at"))
        target_date_str   = _parse_date(target_data.get("created_at"))

        client_name = existing_data.get("client_name") or target_data.get("client_name") or "____________________________"
        client_code = ((existing_data.get("client_code") or target_data.get("client_code") or "________________")).upper()
        risk_tier   = existing_data.get("assigned_risk_tier") or target_data.get("assigned_risk_tier") or "________________"

        fields_data = [
            [Paragraph("<b>Client Name</b>", label_style),              Paragraph(client_name, val_style)],
            [Paragraph("<b>Client Code</b>", label_style),              Paragraph(client_code, val_style)],
            [Paragraph("<b>Assigned Risk Profile</b>", label_style),    Paragraph(risk_tier, val_style)],
            [Paragraph("<b>Existing Portfolio Date</b>", label_style),  Paragraph(existing_date_str, val_style)],
            [Paragraph("<b>Target Allocation Date</b>", label_style),   Paragraph(target_date_str, val_style)],
            [Paragraph("<b>Report Generated On</b>", label_style),      Paragraph(datetime.now().strftime('%d %B, %Y'), val_style)],
        ]
        fields_table = Table(fields_data, colWidths=[1.8*inch, 4.2*inch], rowHeights=26)
        fields_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (0,3), (-1,4), colors.HexColor('#eff6ff')),   # highlight the two date rows
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(fields_table)
        
        story.append(Spacer(1, 1.0*inch))
        
        advisor_name = doc.advisor_name or "Investment Advisor"
        ia_reg_no = doc.ia_reg_no or "N/A"
        
        sig_block_style = ParagraphStyle('SigBlockCompare', parent=styles['Normal'], fontSize=9, leading=14, textColor=colors.HexColor('#475569'))
        sig_data_cover = [
            [
                Paragraph(f"<b>Investment Advisor:</b><br/>{advisor_name}<br/>SEBI Reg No: {ia_reg_no}", sig_block_style),
                Paragraph("<b>Client Acknowledgment:</b><br/>I have reviewed the comparison report and targets.", sig_block_style)
            ]
        ]
        sig_table_cover = Table(sig_data_cover, colWidths=[3.2*inch, 2.8*inch])
        sig_table_cover.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(sig_table_cover)
        
        story.append(PageBreak())

        # --- PAGE 2: COMPARATIVE MATRIX & CHARTS ---
        story.append(Paragraph("ASSET ALLOCATION COMPARISON MATRIX", heading_style))
        
        col_header_style = ParagraphStyle('ColHeaderCompare', parent=styles['Normal'], fontSize=8.5, fontName='Helvetica-Bold', leading=10, textColor=colors.HexColor('#1e293b'))
        cell_style = ParagraphStyle('CellCompare', parent=styles['Normal'], fontSize=8, leading=9, textColor=colors.black)
        cell_style_right = ParagraphStyle('CellCompareRight', parent=styles['Normal'], fontSize=8, leading=9, alignment=2, textColor=colors.black)

        # --- Table: Existing % vs Target % vs Variance (NO amounts) ---
        table_data = [
            [
                Paragraph("<b>Asset Category</b>", col_header_style),
                Paragraph("<b>Sub-Asset Class</b>", col_header_style),
                Paragraph("<b>Existing %</b>", col_header_style),
                Paragraph("<b>Target %</b>", col_header_style),
                Paragraph("<b>Variance %</b>", col_header_style),
            ]
        ]

        items = [
            ("Equities", "Direct Equity (Stocks)", "stocks_percentage", "stocks_percentage"),
            ("Equities", "Mutual Funds (Equity)", "mutual_fund_equity_percentage", "mutual_fund_equity_percentage"),
            ("Equities", "ULIPs (Equity)", "ulip_equity_percentage", "ulip_equity_percentage"),
            ("Equities", "ETFs (Equity)", "etf_equity_percentage", "etf_equity_percentage"),
            ("Equities", "EQUITIES TOTAL", "equities_percentage", "equities_percentage"),
            ("Debt Securities", "Fixed Deposits & Bonds", "fixed_deposits_bonds_percentage", "fixed_deposits_bonds_percentage"),
            ("Debt Securities", "Mutual Funds (Debt)", "mutual_fund_debt_percentage", "mutual_fund_debt_percentage"),
            ("Debt Securities", "ULIPs (Debt)", "ulip_debt_percentage", "ulip_debt_percentage"),
            ("Debt Securities", "ETFs (Debt)", "etf_debt_percentage", "etf_debt_percentage"),
            ("Debt Securities", "DEBT SECURITIES TOTAL", "debt_securities_percentage", "debt_securities_percentage"),
            ("Commodities", "Gold ETFs", "gold_etf_percentage", "gold_etf_percentage"),
            ("Commodities", "Silver ETFs", "silver_etf_percentage", "silver_etf_percentage"),
            ("Commodities", "Other ETFs (Commodity)", "etf_commodity_percentage", "etf_commodity_percentage"),
            ("Commodities", "COMMODITIES TOTAL", "commodities_percentage", "commodities_percentage"),
        ]

        for cat, sub_class, ext_pct_key, tgt_pct_key in items:
            ext_pct = float(existing_data.get(ext_pct_key) or 0.0)
            tgt_pct = float(target_data.get(tgt_pct_key) or 0.0)
            variance = ext_pct - tgt_pct
            var_sign = "+" if variance > 0 else ""
            is_total = sub_class.endswith("TOTAL")

            if is_total:
                label_text = f"<b>{sub_class}</b>"
                ext_text = f"<b>{ext_pct:.1f}%</b>"
                tgt_text = f"<b>{tgt_pct:.1f}%</b>"
                var_text = f"<b>{var_sign}{variance:.1f}%</b>"
            else:
                label_text = sub_class
                ext_text = f"{ext_pct:.1f}%"
                tgt_text = f"{tgt_pct:.1f}%"
                var_text = f"{var_sign}{variance:.1f}%"

            table_data.append([
                Paragraph(cat if not is_total else "", cell_style),
                Paragraph(label_text, cell_style),
                Paragraph(ext_text, cell_style_right),
                Paragraph(tgt_text, cell_style_right),
                Paragraph(var_text, cell_style_right),
            ])

        # Grand Total row
        table_data.append([
            Paragraph("", cell_style),
            Paragraph("<b>GRAND TOTAL</b>", cell_style),
            Paragraph("<b>100.0%</b>", cell_style_right),
            Paragraph("<b>100.0%</b>", cell_style_right),
            Paragraph("<b>0.0%</b>", cell_style_right),
        ])

        matrix_table = Table(table_data, colWidths=[1.5*inch, 2.2*inch, 1.1*inch, 1.1*inch, 1.1*inch])
        matrix_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (2,1), (-1,-1), 'RIGHT'),
            ('SPAN', (0,1), (0,5)),
            ('SPAN', (0,6), (0,10)),
            ('SPAN', (0,11), (0,14)),
            ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (0,10), (-1,10), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (0,14), (-1,14), colors.HexColor('#f1f5f9')),
            ('BACKGROUND', (0,15), (-1,15), colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 3),
        ]))
        story.append(matrix_table)
        story.append(Spacer(1, 14))

        # --- HELPER: Premium Grouped Bar Chart (Existing vs Target %) ---
        def make_grouped_bar_chart(title: str, labels: list, existing_vals: list, target_vals: list,
                                   bar_color: str = '#6366f1', target_color: str = '#a5b4fc') -> bytes:
            n = len(labels)
            x = list(range(n))
            bar_w = 0.35
            fig, ax = plt.subplots(figsize=(6.5, 3.2))
            fig.patch.set_facecolor('white')
            ax.set_facecolor('#fafafa')

            # Draw bars
            bars_e = ax.bar([i - bar_w/2 for i in x], existing_vals, bar_w,
                            label='Existing %', color=bar_color, alpha=0.92,
                            edgecolor='white', linewidth=0.8, zorder=3)
            bars_t = ax.bar([i + bar_w/2 for i in x], target_vals, bar_w,
                            label='Target %', color=target_color, alpha=0.75,
                            edgecolor=bar_color, linewidth=1.2,
                            linestyle='--', zorder=3)

            # Value labels above bars
            for bar in bars_e:
                h = bar.get_height()
                if h >= 0:
                    ax.text(bar.get_x() + bar.get_width()/2, h + 0.5,
                            f'{h:.1f}%', ha='center', va='bottom',
                            fontsize=7, fontweight='bold', color=bar_color)
            for bar in bars_t:
                h = bar.get_height()
                if h >= 0:
                    ax.text(bar.get_x() + bar.get_width()/2, h + 0.5,
                            f'{h:.1f}%', ha='center', va='bottom',
                            fontsize=7, fontweight='bold', color=bar_color, alpha=0.75)

            # Variance delta label below x-axis per group
            y_min = ax.get_ylim()[0]
            for i, (ev, tv) in enumerate(zip(existing_vals, target_vals)):
                diff = ev - tv
                sign = '+' if diff > 0 else ''
                col = '#dc2626' if diff > 1 else '#16a34a' if diff < -1 else '#9ca3af'
                ax.text(i, -max(existing_vals + target_vals) * 0.09,
                        f'{sign}{diff:.1f}%', ha='center', va='top',
                        fontsize=6.5, fontweight='bold', color=col,
                        transform=ax.transData)

            # Axes styling
            ax.set_xticks(x)
            ax.set_xticklabels(labels, fontsize=8.5, fontweight='600')
            ax.set_ylabel('Allocation (%)', fontsize=8, labelpad=6)
            ax.set_title(title, fontsize=10.5, fontweight='bold', pad=12, color='#1e293b')
            ax.tick_params(axis='y', labelsize=7.5)

            # Grid and spines
            ax.yaxis.grid(True, alpha=0.25, linestyle='--', color='#94a3b8')
            ax.set_axisbelow(True)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#e2e8f0')
            ax.spines['bottom'].set_color('#e2e8f0')

            # Extend y-axis slightly for labels
            cur_max = max(existing_vals + target_vals) if existing_vals + target_vals else 10
            ax.set_ylim(-cur_max * 0.12, cur_max * 1.22)

            # Legend
            leg = ax.legend(fontsize=8, loc='upper right', framealpha=0.9,
                            edgecolor='#e2e8f0', fancybox=True)
            leg.get_frame().set_linewidth(0.8)

            # Outer border
            for spine in ax.spines.values():
                spine.set_linewidth(0.8)

            fig.tight_layout(pad=1.4)
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                        facecolor='white', edgecolor='none')
            buf.seek(0)
            plt.close(fig)
            return buf.getvalue()

        def get_e(key): return float(existing_data.get(key) or 0.0)
        def get_t(key): return float(target_data.get(key) or 0.0)

        # --- Chart 1 flows directly after the matrix table (fills blank space on same page) ---
        story.append(Spacer(1, 10))
        story.append(Paragraph("MAIN ASSET CLASS COMPARISON", heading_style))
        chart1_bytes = make_grouped_bar_chart(
            "Equities vs Debt vs Commodities (Existing vs Target %)",
            ["Equities", "Debt Securities", "Commodities"],
            [get_e("equities_percentage"), get_e("debt_securities_percentage"), get_e("commodities_percentage")],
            [get_t("equities_percentage"), get_t("debt_securities_percentage"), get_t("commodities_percentage")],
            bar_color='#7c3aed', target_color='#c4b5fd'
        )
        story.append(Image(io.BytesIO(chart1_bytes), width=6.5*inch, height=3.0*inch))

        # --- Sub-asset charts start on a new page ---
        story.append(PageBreak())
        story.append(Paragraph("SUB-ASSET ALLOCATION COMPARISON CHARTS", heading_style))
        story.append(Paragraph(
            "Detailed percentage comparison of existing vs target allocation across each sub-asset class.",
            ParagraphStyle('ChartSubtitle', parent=styles['Normal'], fontSize=8.5, leading=12,
                           textColor=colors.HexColor('#64748b'), spaceAfter=14)
        ))

        # Chart 2: Equities sub-assets
        chart2_bytes = make_grouped_bar_chart(
            "Equities Sub-Asset Breakdown (%)",
            ["Stocks", "MF Equity", "ULIP Eq.", "ETF Eq."],
            [get_e("stocks_percentage"), get_e("mutual_fund_equity_percentage"), get_e("ulip_equity_percentage"), get_e("etf_equity_percentage")],
            [get_t("stocks_percentage"), get_t("mutual_fund_equity_percentage"), get_t("ulip_equity_percentage"), get_t("etf_equity_percentage")],
            bar_color='#ec4899', target_color='#fbcfe8'
        )
        story.append(Image(io.BytesIO(chart2_bytes), width=6.5*inch, height=3.0*inch))
        story.append(Spacer(1, 16))

        # Chart 3: Debt sub-assets
        chart3_bytes = make_grouped_bar_chart(
            "Debt Securities Sub-Asset Breakdown (%)",
            ["FD & Bonds", "MF Debt", "ULIP Debt", "ETF Debt"],
            [get_e("fixed_deposits_bonds_percentage"), get_e("mutual_fund_debt_percentage"), get_e("ulip_debt_percentage"), get_e("etf_debt_percentage")],
            [get_t("fixed_deposits_bonds_percentage"), get_t("mutual_fund_debt_percentage"), get_t("ulip_debt_percentage"), get_t("etf_debt_percentage")],
            bar_color='#0ea5e9', target_color='#bae6fd'
        )
        story.append(Image(io.BytesIO(chart3_bytes), width=6.5*inch, height=3.0*inch))
        story.append(Spacer(1, 16))

        # Chart 4: Commodities sub-assets
        chart4_bytes = make_grouped_bar_chart(
            "Commodities Sub-Asset Breakdown (%)",
            ["Gold ETF", "Silver ETF", "Other ETF"],
            [get_e("gold_etf_percentage"), get_e("silver_etf_percentage"), get_e("etf_commodity_percentage")],
            [get_t("gold_etf_percentage"), get_t("silver_etf_percentage"), get_t("etf_commodity_percentage")],
            bar_color='#f59e0b', target_color='#fde68a'
        )
        story.append(Image(io.BytesIO(chart4_bytes), width=6.5*inch, height=3.0*inch))
        story.append(Spacer(1, 18))

        # --- DISCLAIMER ---
        story.append(Paragraph("REGULATORY DISCLAIMER", ParagraphStyle('Heading3Style', parent=styles['Heading3'], fontSize=9, textColor=colors.HexColor('#1a2980'), spaceAfter=4)))
        
        disclaimer_text = DEFAULT_ASSET_ALLOCATION_DISCLAIMER
        if existing_data.get("disclaimer_text"):
            disclaimer_text = existing_data["disclaimer_text"]
        elif target_data.get("disclaimer_text"):
            disclaimer_text = target_data["disclaimer_text"]
            
        story.append(Paragraph(disclaimer_text, ParagraphStyle('DisclaimerStyle', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#64748b'), fontName='Helvetica-Oblique')))
        story.append(Spacer(1, 10))

        # --- SIGNATURES ---
        sig_style = ParagraphStyle('SigStyleCompare', parent=normal_style, leading=12)
        sig_data = [
            [
                Paragraph("__________________________<br/><b>Client Signature</b><br/>Date: ________________", sig_style),
                Paragraph("__________________________<br/><b>Advisor Signature</b><br/>Date: ________________", sig_style)
            ],
            [
                Paragraph(f"{client_name}", sig_style),
                Paragraph(f"{advisor_name}", sig_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[3.7*inch, 3.7*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
            ('BOTTOMPADDING', (0,0), (-1,0), 15),
        ]))
        story.append(sig_table)

        doc.build(story, onFirstPage=AssetAllocationReportUtils.add_page_number, onLaterPages=AssetAllocationReportUtils.add_page_number)
        buffer.seek(0)
        return buffer
