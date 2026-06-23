"""
Investment Advice Note — PDF & DOCX Report Generator
─────────────────────────────────────────────────────
Generates SEBI-compliant Investment Advice Notes in PDF and DOCX formats.
Matches the layout defined in docs/SEBI_Investment_Advice_Note_Sample.md.

Uses:
  - fpdf2 (BaseReportPDF) for PDF generation
  - python-docx for Word document generation
"""
import io
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.utils.pdf_generator import BaseReportPDF





# ── Color Palette ──────────────────────────────────────────────────
_NAVY = (0, 31, 63)
_ACCENT_BLUE = (0, 70, 160)
_LIGHT_BLUE_BG = (235, 244, 255)
_SECTION_BG = (245, 246, 248)
_TABLE_HEADER_BG = (220, 232, 246)
_BORDER = (200, 210, 220)
_TEXT_DARK = (20, 20, 20)
_TEXT_MUTED = (110, 110, 110)
_ROW_ALT = (250, 251, 253)
_GREEN = (0, 120, 50)
_GREEN_BG = (235, 248, 235)
_RED_MUTED = (180, 60, 60)

# ── SEBI Disclaimer ───────────────────────────────────────────────
_SEBI_DISCLAIMER = (
    "Investment in securities is subject to market risks. This Investment Advice Note is prepared "
    "on the basis of information which the adviser considers reliable but does not represent or "
    "warrant its accuracy or completeness. This document does not constitute an offer or solicitation "
    "to buy or sell any security. Past performance is not indicative of future returns. The Investment "
    "Adviser does not guarantee any return and shall not incur any liability by reason of any loss "
    "which a client may suffer due to any depletion in the value of assets under advice, fluctuation "
    "in asset value, non-performance or underperformance of securities or funds or other market "
    "conditions. This note is issued exclusively for the addressee client and shall not be reproduced "
    "or redistributed. Registration of Investment Adviser does not guarantee quality of advice."
)

_RECORD_RETENTION = (
    "Record retention: 5 years from date of issue  |  Both IA and client must retain this document  |  "
    "Regulation 22, SEBI (Investment Advisers) Regulations 2013 as amended"
)


def format_indian_number(val):
    if val is None:
        return ""
    try:
        val_float = float(val)
        is_neg = val_float < 0
        val_float = abs(val_float)
        if val_float.is_integer():
            int_part = str(int(val_float))
            dec_part = ""
        else:
            s = f"{val_float:.2f}"
            int_part, dec_part = s.split('.')
            dec_part = "." + dec_part
            
        if len(int_part) <= 3:
            grouped = int_part
        else:
            last_three = int_part[-3:]
            rest = int_part[:-3]
            rest_groups = []
            while len(rest) > 2:
                rest_groups.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                rest_groups.insert(0, rest)
            grouped = ",".join(rest_groups) + "," + last_three
            
        formatted = grouped + dec_part
        if is_neg:
            return f"({formatted})"
        return formatted
    except Exception:
        return str(val)


def format_amount_units_python(rec):
    ttype = rec.get("transaction_type")
    if not ttype:
        return rec.get("amount_units") or ""
        
    freq = rec.get("frequency")
    amount = rec.get("amount")
    custom_inst = rec.get("custom_instruction")
    p_type = rec.get("product_type", "")
    
    is_life_insurance = False
    if p_type:
        is_life_insurance = p_type.lower() in ("life-insurance", "life_insurance")
        
    if ttype == 'HOLDING':
        return "Existing holding"
    elif ttype == 'TEXT_ONLY':
        return custom_inst or ""
    
    formatted_amount = format_indian_number(amount) if amount is not None else ""
    
    if ttype == 'LUMP_SUM':
        return f"Rs. {formatted_amount} lump sum"
    if ttype == 'SWITCH_IN':
        return f"Rs. {formatted_amount} Switch In"
    if ttype == 'SWITCH_OUT':
        return f"Rs. {formatted_amount} Switch Out"
    if ttype == 'TRANSFER_IN':
        return f"Rs. {formatted_amount} Transfer In"
    if ttype == 'TRANSFER_OUT':
        return f"Rs. {formatted_amount} Transfer Out"
        
    freq_label = ""
    if freq == 'MONTHLY':
        freq_label = "month"
    elif freq == 'QUARTERLY':
        freq_label = "quarter"
    elif freq == 'HALF_YEARLY':
        freq_label = "half-year"
    elif freq == 'YEARLY':
        freq_label = "year"
        
    if is_life_insurance and freq == 'YEARLY':
        return f"Annual prem. Rs. {formatted_amount}"
        
    if ttype in ('SIP', 'STP', 'SWP'):
        return f"Rs. {formatted_amount}/{freq_label} {ttype}"
        
    return rec.get("amount_units") or ""


def calculate_age(dob_str):
    if not dob_str:
        return None
    try:
        import re
        parts = re.findall(r'\d+', dob_str)
        if len(parts) >= 3:
            # Check if first part is year (4 digits)
            if len(parts[0]) == 4:
                year = int(parts[0])
            elif len(parts[2]) == 4:
                year = int(parts[2])
            else:
                return None
            return 2026 - year
    except Exception:
        pass
    return None


def format_dob(dob_str):
    if not dob_str:
        return "N/A"
    try:
        dt = datetime.strptime(dob_str.split('T')[0], "%Y-%m-%d")
        return dt.strftime("%d %B %Y")
    except Exception:
        return dob_str


def format_date_issue(date_str):
    if not date_str:
        return "N/A"
    try:
        dt = datetime.strptime(date_str.split('T')[0], "%Y-%m-%d")
        return dt.strftime("%d %B %Y")
    except Exception:
        return date_str


class InvestmentAdviceNotePDF:
    """Generates a SEBI-compliant Investment Advice Note PDF using fpdf2."""

    @staticmethod
    def _render_cover_page(
        pdf: BaseReportPDF,
        note_data: dict,
        ia_data: Optional[dict],
        client: dict,
        logo_path: Optional[str] = None,
    ):
        pdf.add_page()

        # Border
        pdf.set_draw_color(*_ACCENT_BLUE)
        pdf.set_line_width(0.5)
        pdf.rect(5, 5, 200, 287)
        pdf.set_line_width(0.2)

        # Logo
        pdf.set_y(35)
        if logo_path and os.path.exists(logo_path):
            pdf.image(logo_path, 85, pdf.get_y(), 40)
            pdf.set_y(pdf.get_y() + 50)
        else:
            pdf.set_y(60)

        # Entity name
        entity_name = ""
        if ia_data:
            entity_name = ia_data.get("name_of_entity") or ia_data.get("name_of_ia", "")
        if entity_name:
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(*_TEXT_DARK)
            pdf.cell(0, 8, entity_name.upper(), ln=True, align="C")

        # Report title
        pdf.ln(20)
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(*_ACCENT_BLUE)
        pdf.cell(0, 14, "INVESTMENT ADVICE NOTE", ln=True, align="C")

        # Subtitle
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.cell(0, 6, "Issued under SEBI (Investment Advisers) Regulations, 2013", ln=True, align="C")
        pdf.cell(0, 5, "Regulation 16 & 17  |  Master Circular dated 21 May 2024", ln=True, align="C")

        # Decorative bar
        pdf.ln(4)
        pdf.set_fill_color(*_ACCENT_BLUE)
        pdf.set_xy(75, pdf.get_y())
        pdf.cell(60, 1.5, "", fill=True, ln=True)

        # Client info
        pdf.ln(25)
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(*_TEXT_DARK)
        client_name = client.get("client_name", "Client").upper()
        pdf.cell(0, 10, client_name, ln=True, align="C")

        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(*_TEXT_MUTED)
        client_code = client.get("client_code", "N/A")
        pdf.cell(0, 6, f"CLIENT CODE: {client_code}", ln=True, align="C")

        filtered_member = note_data.get("filtered_member")
        if filtered_member:
            pdf.ln(2)
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(*_ACCENT_BLUE)
            m_name = filtered_member.get("full_name", "").upper()
            m_relation = filtered_member.get("relation", "").upper()
            pdf.cell(0, 6, f"INVESTOR: {m_name} ({m_relation})", ln=True, align="C")

        # Advice Note Number badge
        pdf.ln(8)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*_GREEN)
        advice_no = note_data.get("advice_note_no", "N/A")
        pdf.cell(0, 6, f"ADVICE NOTE: {advice_no}", ln=True, align="C")

        # Footer
        pdf.set_y(245)
        pdf.set_font("helvetica", "I", 9)
        pdf.set_text_color(*_TEXT_MUTED)
        date_str = note_data.get("date_of_issue", datetime.now().strftime("%d %B %Y"))
        pdf.cell(0, 6, f"Date of Issue: {date_str}", ln=True, align="C")

        if ia_data:
            reg_no = ia_data.get("ia_registration_number", "")
            if reg_no:
                pdf.set_font("helvetica", "", 9)
                pdf.cell(0, 6, f"SEBI Registration No: {reg_no}", ln=True, align="C")

        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(*_RED_MUTED)
        pdf.cell(0, 6, "CONFIDENTIAL - FOR CLIENT AND IA RECORDS ONLY", ln=True, align="C")

    @staticmethod
    def _section_header(pdf: BaseReportPDF, title: str):
        """Render a styled section header bar."""
        if pdf.get_y() > 255:
            pdf.add_page()

        pdf.set_fill_color(*_SECTION_BG)
        pdf.rect(10, pdf.get_y(), 190, 9, "F")
        pdf.set_draw_color(*_BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(10, pdf.get_y(), 190, 9, "D")
        pdf.set_fill_color(*_ACCENT_BLUE)
        pdf.rect(10, pdf.get_y(), 3, 9, "F")

        pdf.set_xy(16, pdf.get_y() + 2)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 5, title.upper(), ln=True)
        pdf.ln(4)

    @staticmethod
    def _kv_row(pdf: BaseReportPDF, label: str, value: str, label_w: int = 42, val_w: int = 53):
        """Render a label:value pair in a 2-column grid row with dynamic font size scaling to prevent overflow."""
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.set_draw_color(*_BORDER)
        pdf.cell(label_w, 7, f" {label}", border="LBT")
        
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*_TEXT_DARK)
        
        val_str = f" {value or 'N/A'}"
        
        # Calculate text width and scale down font size if it overflows the cell width (minus padding)
        font_size = 9.0
        width = pdf.get_string_width(val_str)
        max_allowed_w = val_w - 3  # 3mm safety margin for padding
        
        while width > max_allowed_w and font_size > 6.0:
            font_size -= 0.5
            pdf.set_font("helvetica", "", font_size)
            width = pdf.get_string_width(val_str)
            
        # If it still overflows at 6.0pt, truncate with ellipsis
        if width > max_allowed_w:
            while len(val_str) > 4 and width > max_allowed_w:
                val_str = val_str[:-4] + "..."
                width = pdf.get_string_width(val_str)
                
        pdf.cell(val_w, 7, val_str, border="RBT")

    @staticmethod
    def _kv_grid(pdf: BaseReportPDF, fields: List[tuple]):
        """Render key-value pairs in a 2x2 grid layout."""
        for i in range(0, len(fields), 2):
            pdf.set_x(10)
            f1 = fields[i]
            InvestmentAdviceNotePDF._kv_row(pdf, f1[0], f1[1])
            if i + 1 < len(fields):
                f2 = fields[i + 1]
                InvestmentAdviceNotePDF._kv_row(pdf, f2[0], f2[1])
            pdf.ln()

    @staticmethod
    def _full_width_text(pdf: BaseReportPDF, label: str, value: str):
        """Render a full-width label + multi-line text block."""
        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.set_draw_color(*_BORDER)
        pdf.cell(42, 7, f" {label}", border="LTB")
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*_TEXT_DARK)
        pdf.multi_cell(148, 7, f" {value or 'N/A'}", border="RTB")

    @staticmethod
    def generate_execution_log_pdf(
        note_data: dict,
        ia_data: Optional[dict] = None,
        logo_path: Optional[str] = None,
    ) -> bytes:
        """
        Generate a compact 1-page Execution Actions / Action Taken log sheet.
        """
        advisor_name = ia_data.get("name_of_ia", "") if ia_data else ""
        entity_name = ia_data.get("name_of_entity", "") if ia_data else ""
        ia_reg_no = ia_data.get("ia_registration_number", "") if ia_data else ""

        pdf = BaseReportPDF(
            advisor_name=advisor_name,
            entity_name=entity_name,
            ia_reg_no=ia_reg_no,
            header_text="Investment Advice Logs",
        )

        client = note_data.get("client_snapshot", {})
        recommendations = note_data.get("recommendations", [])

        # Start PDF
        pdf.add_page()

        # Border
        pdf.set_draw_color(*_ACCENT_BLUE)
        pdf.set_line_width(0.5)
        pdf.rect(5, 5, 200, 287)
        pdf.set_line_width(0.2)

        # Header Logo & Title
        pdf.set_y(15)
        logo_height = 0
        if logo_path and os.path.exists(logo_path):
            pdf.image(logo_path, 10, pdf.get_y(), 25)
            logo_height = 25
            pdf.set_xy(40, pdf.get_y() + 5)
        else:
            pdf.set_x(10)
        
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 8, "INVESTMENT ADVICE LOGS", ln=True)
        
        # Calculate Y position to ensure metadata grid starts below the logo image
        grid_start_y = max(pdf.get_y(), 15 + logo_height) + 5
        pdf.set_y(grid_start_y)

        # Compact Metadata Grid
        pdf.set_x(10)
        metadata = [
            ("Advice Note No.", note_data.get("advice_note_no", "N/A")),
            ("Client Name", client.get("client_name", "N/A")),
            ("Client ID", client.get("client_code", "N/A")),
            ("Date of Issue", note_data.get("date_of_issue", "N/A")),
        ]

        filtered_member = note_data.get("filtered_member")
        if filtered_member:
            metadata.append(("Investor Name", filtered_member.get("full_name", "N/A")))
            metadata.append(("Relation", filtered_member.get("relation", "N/A")))
        
        # Draw metadata fields inline
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.set_draw_color(*_BORDER)
        
        for idx, (label, val) in enumerate(metadata):
            pdf.cell(30, 6, f" {label}", border="1")
            pdf.set_font("helvetica", "", 8.5)
            pdf.set_text_color(*_TEXT_DARK)
            pdf.cell(65, 6, f" {val}", border="1")
            if idx % 2 == 1:
                pdf.ln()
            pdf.set_font("helvetica", "B", 8)
            pdf.set_text_color(*_TEXT_MUTED)
        
        pdf.ln(8)

        # Recommendations Title
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 6, "LOGGED ACTIONS & STATUSES", ln=True)
        pdf.ln(2)

        # Recommendations Table
        if recommendations:
            # Table header
            cols = [8, 56, 18, 32, 28, 28, 20]
            headers = ["#", "Product / Scheme Name", "Action", "Amount / Units", "Validity", "Validity Status", "Action Taken"]

            pdf.set_fill_color(*_NAVY)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(255, 255, 255)
            pdf.set_x(10)
            for h, w in zip(headers, cols):
                pdf.cell(w, 8, f" {h}", border=1, fill=True)
            pdf.ln()

            # Data rows
            h_unit = 5.0
            default_days = note_data.get("advice_validity_days", 60)
            issue_date_str = note_data.get("date_of_issue")
            
            for idx, rec in enumerate(recommendations):
                # Calculate validity status
                is_valid = True
                try:
                    issue_date_str_split = issue_date_str.split('T')[0]
                    issue_date = datetime.strptime(issue_date_str_split, "%Y-%m-%d").date()
                    
                    val_text = rec.get("advice_validity_text")
                    days = default_days or 60
                    if val_text:
                        match = re.search(r'(\d+)\s*Day', val_text, re.IGNORECASE)
                        if match:
                            days = int(match.group(1))
                        elif "immediate" in val_text.lower():
                            days = 1
                            
                    expiry_date = issue_date + timedelta(days=days)
                    today = datetime.now().date()
                    is_valid = expiry_date >= today
                except Exception:
                    is_valid = True
                
                val_status = "Valid" if is_valid else "Expired"
                
                prod_name = rec.get("product_name", "N/A")
                member_name = rec.get("member_name")
                if member_name:
                    prod_name = f"{prod_name}\n[Allotted to: {member_name}]"
                
                cell_texts = [
                    str(idx + 1),
                    f"{prod_name}\n{rec.get('isin_code_scheme_code_uin', '')}",
                    rec.get("action", "BUY"),
                    format_amount_units_python(rec),
                    rec.get("advice_validity_text") or f"{default_days} Days",
                    val_status,
                    rec.get("action_taken") or "No"
                ]

                lines_per_col = [
                    max(len(pdf.multi_cell(w, h_unit - 1, str(t), split_only=True)), 1)
                    for t, w in zip(cell_texts, cols)
                ]
                row_h = max(max(lines_per_col) * (h_unit - 1), 8)

                if pdf.get_y() + row_h > 240:
                    pdf.add_page()

                fill_color = _ROW_ALT if idx % 2 == 1 else (255, 255, 255)
                pdf.set_font("helvetica", "", 7.5)
                pdf.set_text_color(*_TEXT_DARK)

                row_x, row_y = 10, pdf.get_y()
                for col_idx, (t, w) in enumerate(zip(cell_texts, cols)):
                    pdf.set_fill_color(*fill_color)
                    pdf.rect(row_x, row_y, w, row_h, "F")
                    pdf.rect(row_x, row_y, w, row_h, "D")
                    pdf.set_xy(row_x + 1, row_y + 1)
                    
                    # Highlight colors for status
                    if col_idx == 5:  # Validity Status
                        pdf.set_font("helvetica", "B", 7.5)
                        if t == "Valid":
                            pdf.set_text_color(*_GREEN)
                        else:
                            pdf.set_text_color(*_RED_MUTED)
                    elif col_idx == 6:  # Action Taken
                        pdf.set_font("helvetica", "B", 7.5)
                        if t == "Yes":
                            pdf.set_text_color(*_GREEN)
                        elif t == "Partial":
                            pdf.set_text_color(180, 110, 0)
                        else:
                            pdf.set_text_color(*_TEXT_MUTED)
                    else:
                        pdf.set_font("helvetica", "", 7.5)
                        pdf.set_text_color(*_TEXT_DARK)
                        
                    pdf.multi_cell(w - 2, h_unit - 1.5, str(t), align="L")
                    row_x += w
                pdf.set_y(row_y + row_h)
        else:
            pdf.set_font("helvetica", "I", 9)
            pdf.set_text_color(*_TEXT_MUTED)
            pdf.cell(0, 10, "No recommendations found.", ln=True, align="C")
        
        pdf.ln(10)

        # Disclaimer
        if pdf.get_y() > 215:
            pdf.add_page()
            
        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_RED_MUTED)
        pdf.cell(0, 5, "DISCLAIMER & RECORD RETENTION", ln=True)
        pdf.set_font("helvetica", "I", 6.5)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.multi_cell(0, 4, "These logs represent client-reported execution actions taken on the recommendations provided in this Investment Advice Note. The adviser does not handle trade execution, client funds, or hold custody of securities. Both the client and the investment adviser must retain these logs for a mandatory compliance period of 5 years.", align="L")
        pdf.ln(10)

        # Signature Block
        sig_y = pdf.get_y()
        pdf.set_y(sig_y)

        # Left: IA Signature
        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_NAVY)
        entity = entity_name or advisor_name or "Investment Advisor"
        pdf.cell(90, 5, f"For {entity}", ln=True)
        pdf.set_y(sig_y + 12)
        pdf.set_x(10)
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(*_TEXT_DARK)
        pdf.cell(90, 4, "________________________________", ln=True)
        pdf.set_x(10)
        po_name = note_data.get("principal_officer_name", "Principal Officer")
        pdf.cell(90, 5, po_name, ln=True)
        pdf.set_x(10)
        pdf.set_font("helvetica", "I", 7)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.cell(90, 4, f"Principal Officer  |  Reg No: {ia_reg_no}", ln=True)
        pdf.set_x(10)
        pdf.cell(90, 4, f"Date: {datetime.now().strftime('%d %B %Y')}", ln=True)

        # Right: Client Acknowledgement
        pdf.set_xy(110, sig_y)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_NAVY)
        pdf.cell(90, 5, "Client Verification Signature", ln=True)
        pdf.set_xy(110, sig_y + 12)
        pdf.set_font("helvetica", "", 7.5)
        pdf.set_text_color(*_TEXT_DARK)
        pdf.cell(90, 4, "________________________________", ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.set_font("helvetica", "B", 7.5)
        pdf.cell(90, 5, client.get("client_name", "Client"), ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.set_font("helvetica", "I", 7)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.cell(90, 4, f"Client ID: {client.get('client_code', 'N/A')}", ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(90, 4, "Date: ___________________", ln=True)

        return bytes(pdf.output())

    @staticmethod
    def generate_pdf(
        note_data: dict,
        ia_data: Optional[dict] = None,
        logo_path: Optional[str] = None,
        export_type: str = "full",
    ) -> bytes:
        """
        Generate a complete SEBI Investment Advice Note PDF.
        """
        if export_type == "execution_log":
            return InvestmentAdviceNotePDF.generate_execution_log_pdf(note_data, ia_data, logo_path)

        advisor_name = ia_data.get("name_of_ia", "") if ia_data else ""
        entity_name = ia_data.get("name_of_entity", "") if ia_data else ""
        ia_reg_no = ia_data.get("ia_registration_number", "") if ia_data else ""

        pdf = BaseReportPDF(
            advisor_name=advisor_name,
            entity_name=entity_name,
            ia_reg_no=ia_reg_no,
            header_text="Investment Advice Note - Confidential",
        )

        client = note_data.get("client_snapshot", {})
        recommendations = note_data.get("recommendations", [])

        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        generated_on = now_ist.strftime("%d %b %Y, %I:%M %p")

        # ══════════════════ COVER PAGE ══════════════════
        InvestmentAdviceNotePDF._render_cover_page(pdf, note_data, ia_data, client, logo_path)

        # ══════════════════ SECTION A - IA Details ══════════════════
        pdf.add_page()
        InvestmentAdviceNotePDF._section_header(pdf, "Section A - Investment Adviser Details")

        basl_id = ia_data.get("basl_membership_id", "") if ia_data else ""
        website_val = ia_data.get("website", "") if ia_data else ""

        ia_fields = [
            ("IA / Firm Name", entity_name or advisor_name),
            ("Advice Note No.", note_data.get("advice_note_no", "N/A")),
            ("SEBI Reg. No.", ia_reg_no),
            ("Date of Issue", note_data.get("date_of_issue", "N/A")),
            ("IAASB", f"BSE Limited (IAASB) - {basl_id}" if basl_id else "BSE Limited (IAASB)"),
            ("Advice Validity", note_data.get("advice_validity_custom_text", "N/A")),
            ("Principal Officer", note_data.get("principal_officer_name", "N/A")),
            ("PO Reg. No.", note_data.get("principal_officer_reg_no", "N/A")),
            ("Website", website_val or "N/A"),
            ("Advice Category", note_data.get("advice_category", "Comprehensive Advisory")),
        ]
        InvestmentAdviceNotePDF._kv_grid(pdf, ia_fields)

        # Registered address (full width)
        if ia_data:
            addr = ia_data.get("registered_address", "")
            if addr:
                InvestmentAdviceNotePDF._full_width_text(pdf, "Registered Address", addr)
        pdf.ln(6)

        # ══════════════════ SECTION B - Client Details ══════════════════
        InvestmentAdviceNotePDF._section_header(pdf, "Section B - Client Details and Risk Profile")

        risk_score = client.get("risk_profile_score")
        risk_profile_str = client.get("risk_profile", "N/A")
        if risk_score and risk_score != "N/A":
            risk_profile_str = f"{risk_profile_str} (Score: {risk_score}/100)"

        liabilities_val = client.get("existing_liabilities")
        if liabilities_val is not None:
            try:
                liabilities_str = f"Rs. {float(liabilities_val):,.0f}"
            except Exception:
                liabilities_str = str(liabilities_val)
        else:
            liabilities_str = "N/A"

        filtered_member = note_data.get("filtered_member")
        if filtered_member:
            client_fields = [
                ("Client Full Name", client.get("client_name", "N/A")),
                ("Client ID", client.get("client_code", "N/A")),
                ("Investor Name", filtered_member.get("full_name", "N/A")),
                ("Investor Code", filtered_member.get("investor_code", "N/A")),
                ("Relation", filtered_member.get("relation", "N/A")),
                ("Investor PAN", filtered_member.get("pan_number", "N/A")),
                ("Investor CKYC", filtered_member.get("ckyc_number") or filtered_member.get("ckyc") or "N/A"),
                ("Investor DOB", format_dob(filtered_member.get("date_of_birth"))),
                ("Email", client.get("email", "N/A")),
                ("Mobile", client.get("phone_number", "N/A")),
                ("Risk Profile", risk_profile_str),
                ("Risk Profile Date", client.get("risk_profile_date", "N/A")),
                ("Investment Horizon", client.get("investment_horizon", "N/A")),
                ("Annual Income Band", note_data.get("annual_income_band", "N/A")),
                ("Existing Liabilities", liabilities_str),
                ("Assets Under Advice", f"Rs. {float(note_data.get('assets_under_advice', 0)):,.0f}"),
                ("Fee Mode", note_data.get("fee_mode", "N/A").replace("_", " ").title()),
                ("Fee Amount", f"Rs. {float(note_data.get('fee_amount', 0)):,.0f}"),
            ]
        else:
            client_fields = [
                ("Client Full Name", client.get("client_name", "N/A")),
                ("Client ID", client.get("client_code", "N/A")),
                ("PAN Number", client.get("pan_number", "N/A")),
                ("Client DOB", client.get("date_of_birth", "N/A")),
                ("Email", client.get("email", "N/A")),
                ("Mobile", client.get("phone_number", "N/A")),
                ("Risk Profile", risk_profile_str),
                ("Risk Profile Date", client.get("risk_profile_date", "N/A")),
                ("Investment Horizon", client.get("investment_horizon", "N/A")),
                ("Annual Income Band", note_data.get("annual_income_band", "N/A")),
                ("Existing Liabilities", liabilities_str),
                ("Assets Under Advice", f"Rs. {float(note_data.get('assets_under_advice', 0)):,.0f}"),
                ("Fee Mode", note_data.get("fee_mode", "N/A").replace("_", " ").title()),
                ("Fee Amount", f"Rs. {float(note_data.get('fee_amount', 0)):,.0f}"),
            ]
        InvestmentAdviceNotePDF._kv_grid(pdf, client_fields)
        
        # Address & Primary Financial Goal as full-width multi-line text boxes to prevent grid collision
        InvestmentAdviceNotePDF._full_width_text(pdf, "Address", client.get("address", "N/A"))
        InvestmentAdviceNotePDF._full_width_text(
            pdf, "Primary Financial Goal", note_data.get("primary_financial_goal", "N/A")
        )

        # Recommended Asset Allocation
        rec_alloc = note_data.get("recommended_asset_allocation")
        alloc_text = "N/A"
        sub_allocs = {}
        if rec_alloc:
            if isinstance(rec_alloc, str):
                try:
                    import json as _json
                    rec_alloc = _json.loads(rec_alloc)
                except Exception:
                    pass
            if isinstance(rec_alloc, dict):
                sub_allocs = rec_alloc.get("sub_assets") or {}
                alloc_parts = []
                for k in ("Debt", "Equity", "Commodities"):
                    if k in rec_alloc:
                        alloc_parts.append(f"{k}: {rec_alloc[k]}%")
                for k, v in rec_alloc.items():
                    if k not in ("Debt", "Equity", "Commodities", "sub_assets"):
                        alloc_parts.append(f"{k}: {v}%")
                alloc_text = "  |  ".join(alloc_parts) if alloc_parts else "N/A"
            elif isinstance(rec_alloc, str) and rec_alloc != "{}":
                alloc_text = rec_alloc

        InvestmentAdviceNotePDF._full_width_text(pdf, "Recommended Asset Allocation", alloc_text)

        # Render sub-asset allocations if present
        if sub_allocs:
            # Group sub-assets by category
            equity_map = {
                "stocks_percentage": "Direct Equity (Stocks)",
                "mutual_fund_equity_percentage": "Equity Mutual Funds",
                "ulip_equity_percentage": "Equity ULIPs",
                "etf_equity_percentage": "Equity ETFs"
            }
            debt_map = {
                "fixed_deposits_bonds_percentage": "Fixed Deposits / Bonds",
                "mutual_fund_debt_percentage": "Debt Mutual Funds",
                "ulip_debt_percentage": "Debt ULIPs",
                "etf_debt_percentage": "Debt ETFs"
            }
            comm_map = {
                "gold_etf_percentage": "Gold ETFs",
                "silver_etf_percentage": "Silver ETFs",
                "etf_commodity_percentage": "Commodity ETFs"
            }

            eq_list = []
            dt_list = []
            cm_list = []

            for k, val in sub_allocs.items():
                try:
                    num_val = float(val) if val is not None else 0.0
                except Exception:
                    num_val = 0.0
                if num_val > 0:
                    pct_str = f"{num_val:.1f}%"
                    if k in equity_map:
                        eq_list.append((equity_map[k], pct_str))
                    elif k in debt_map:
                        dt_list.append((debt_map[k], pct_str))
                    elif k in comm_map:
                        cm_list.append((comm_map[k], pct_str))

            if eq_list or dt_list or cm_list:
                pdf.set_x(10)
                pdf.set_font("helvetica", "B", 8)
                pdf.set_text_color(*_TEXT_MUTED)
                pdf.set_draw_color(*_BORDER)
                pdf.cell(190, 7, " Recommended Sub-Asset Allocation Breakdown", border="LRT", ln=True)

                # Column Headers
                pdf.set_x(10)
                pdf.set_fill_color(*_TABLE_HEADER_BG)
                pdf.set_font("helvetica", "B", 8)
                pdf.set_text_color(*_NAVY)
                pdf.cell(63, 6, "  Equity Sub-Assets", border="1", fill=True, align="L")
                pdf.cell(63, 6, "  Debt Sub-Assets", border="1", fill=True, align="L")
                pdf.cell(64, 6, "  Commodities Sub-Assets", border="1", fill=True, align="L")
                pdf.ln()

                # Print Rows
                max_len = max(len(eq_list), len(dt_list), len(cm_list))
                pdf.set_font("helvetica", "", 7.5) # Compact font size
                pdf.set_text_color(*_TEXT_DARK)

                for idx in range(max_len):
                    pdf.set_x(10)
                    fill = idx % 2 == 1
                    if fill:
                        pdf.set_fill_color(*_ROW_ALT)

                    # 1. Equity Column (width: 47 name, 16 percentage)
                    if idx < len(eq_list):
                        name, pct = eq_list[idx]
                        pdf.cell(47, 6, f"  {name}", border="1", fill=fill)
                        pdf.cell(16, 6, f"{pct} ", border="1", fill=fill, align="R")
                    else:
                        pdf.cell(47, 6, "", border="1", fill=fill)
                        pdf.cell(16, 6, "", border="1", fill=fill)

                    # 2. Debt Column (width: 47 name, 16 percentage)
                    if idx < len(dt_list):
                        name, pct = dt_list[idx]
                        pdf.cell(47, 6, f"  {name}", border="1", fill=fill)
                        pdf.cell(16, 6, f"{pct} ", border="1", fill=fill, align="R")
                    else:
                        pdf.cell(47, 6, "", border="1", fill=fill)
                        pdf.cell(16, 6, "", border="1", fill=fill)

                    # 3. Commodities Column (width: 48 name, 16 percentage)
                    if idx < len(cm_list):
                        name, pct = cm_list[idx]
                        pdf.cell(48, 6, f"  {name}", border="1", fill=fill)
                        pdf.cell(16, 6, f"{pct} ", border="1", fill=fill, align="R")
                    else:
                        pdf.cell(48, 6, "", border="1", fill=fill)
                        pdf.cell(16, 6, "", border="1", fill=fill)

                    pdf.ln()
                pdf.ln(1)

        date_of_alloc = note_data.get("date_of_allocation", "N/A")
        if date_of_alloc and date_of_alloc != "N/A":
            pdf.set_x(10)
            InvestmentAdviceNotePDF._kv_row(pdf, "Date of Allocation", str(date_of_alloc), 42, 148)
            pdf.ln()
        pdf.ln(6)

        # ══════════════════ SECTION C - Suitability ══════════════════
        InvestmentAdviceNotePDF._section_header(pdf, "Section C - Suitability Assessment [Regulation 17]")

        InvestmentAdviceNotePDF._full_width_text(
            pdf, "Advice Suitable?", note_data.get("suitability_assessment", "N/A")
        )
        InvestmentAdviceNotePDF._full_width_text(
            pdf, "Suitability Basis", note_data.get("suitability_basis", "N/A")
        )
        InvestmentAdviceNotePDF._full_width_text(
            pdf, "Investor Advice", note_data.get("investor_advice", "N/A")
        )

        pdf.ln(6)

        # ══════════════════ SECTION D - Recommendations ══════════════════
        InvestmentAdviceNotePDF._section_header(pdf, "Section D - Investment Recommendations")

        if recommendations:
            # Table header
            cols = [8, 52, 30, 30, 16, 28, 26]
            headers = ["#", "Product / Scheme Name", "ISIN / Scheme Code", "Product Type", "Action", "Amount / Units", "Price / NAV"]

            pdf.set_fill_color(*_NAVY)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(255, 255, 255)
            pdf.set_x(10)
            for h, w in zip(headers, cols):
                pdf.cell(w, 8, f" {h}", border=1, fill=True)
            pdf.ln()

            # Data rows
            h_unit = 4.5
            for idx, rec in enumerate(recommendations):
                prod_name = rec.get("product_name", "N/A")
                member_name = rec.get("member_name")
                if member_name:
                    prod_name = f"{prod_name}\n[Allotted to: {member_name}]"

                cell_texts = [
                    str(idx + 1),
                    prod_name,
                    rec.get("isin_code_scheme_code_uin", ""),
                    rec.get("product_type", "").replace("_", " ").title(),
                    rec.get("action", "BUY"),
                    format_amount_units_python(rec),
                    f"Rs. {float(rec['indicative_price_nav']):,.2f}" if rec.get("indicative_price_nav") else "N/A",
                ]

                lines_per_col = [
                    max(len(pdf.multi_cell(w, h_unit, str(t), split_only=True)), 1)
                    for t, w in zip(cell_texts, cols)
                ]
                row_h = max(max(lines_per_col) * h_unit, 8)

                if pdf.get_y() + row_h > 272:
                    pdf.add_page()

                fill_color = _ROW_ALT if idx % 2 == 1 else (255, 255, 255)
                pdf.set_font("helvetica", "", 7)
                pdf.set_text_color(*_TEXT_DARK)

                row_x, row_y = 10, pdf.get_y()
                for t, w in zip(cell_texts, cols):
                    pdf.set_fill_color(*fill_color)
                    pdf.rect(row_x, row_y, w, row_h, "F")
                    pdf.rect(row_x, row_y, w, row_h, "D")
                    pdf.set_xy(row_x + 1, row_y + 1)
                    pdf.multi_cell(w - 2, h_unit, str(t), align="L")
                    row_x += w
                pdf.set_y(row_y + row_h)

            # Indicative price note
            pdf.ln(2)
            pdf.set_font("helvetica", "I", 6.5)
            pdf.set_text_color(*_TEXT_MUTED)
            pdf.set_x(10)
            pdf.multi_cell(
                190, 4,
                "* Prices and NAVs are indicative. Actual execution price will be the prevailing "
                "market price or NAV at time of transaction. Insurance premiums are annual. "
                "Items marked * are IRDAI-regulated products outside SEBI purview.",
                align="L",
            )
        else:
            pdf.set_font("helvetica", "I", 9)
            pdf.set_text_color(*_TEXT_MUTED)
            pdf.cell(0, 10, "No recommendations attached to this advice note.", ln=True, align="C")
        pdf.ln(6)

        # ══════════════════ SECTION E - Rationale ══════════════════
        if recommendations and any(r.get("rationale") for r in recommendations):
            if pdf.get_y() > 230:
                pdf.add_page()
            InvestmentAdviceNotePDF._section_header(pdf, "Section E - Rationale for Advice")

            for rec in recommendations:
                rationale = rec.get("rationale", "")
                if rationale:
                    name = rec.get("product_name", "Product")
                    action = rec.get("action", "")
                    pdf.set_x(10)
                    pdf.set_font("helvetica", "B", 8)
                    pdf.set_text_color(*_NAVY)
                    
                    name_txt = f" {name}"
                    font_size = 8.0
                    width = pdf.get_string_width(name_txt)
                    max_allowed_w = 40  # 42mm total width, 2mm padding safety
                    
                    while width > max_allowed_w and font_size > 6.0:
                        font_size -= 0.5
                        pdf.set_font("helvetica", "B", font_size)
                        width = pdf.get_string_width(name_txt)
                        
                    if width > max_allowed_w:
                        while len(name_txt) > 4 and width > max_allowed_w:
                            name_txt = name_txt[:-4] + "..."
                            width = pdf.get_string_width(name_txt)
                            
                    pdf.cell(42, 6, name_txt, border="LT")
                    pdf.set_font("helvetica", "", 7.5)
                    pdf.set_text_color(*_TEXT_DARK)
                    pdf.multi_cell(148, 6, f" {action}. {rationale}", border="RT")
                    # Bottom border
                    pdf.set_x(10)
                    pdf.cell(190, 0, "", border="T")
                    pdf.ln(1)
            pdf.ln(6)

        # ══════════════════ SECTION F - Risk Disclosures ══════════════════
        if pdf.get_y() > 230:
            pdf.add_page()
        InvestmentAdviceNotePDF._section_header(pdf, "Section F - Risk Disclosures")

        risk_disclosures = [
            ("Market / Price Risk", "Equity and ETF investments are subject to market fluctuations. Past performance is not indicative of future returns. The value of investments may fall below the invested amount."),
            ("Mutual Fund Risk", "Mutual Fund investments are subject to market risks. Please read all scheme documents (SID and KIM) carefully before investing. NAV may go up or down depending on market conditions."),
            ("Interest Rate / Duration Risk", "SBI Magnum Medium Duration Fund carries interest rate duration risk. A rise in interest rates will negatively affect NAV. Suitable only for investors with a minimum 2-3 year horizon."),
            ("Gold / Commodity Risk", "Gold Bees ETF tracks domestic gold prices influenced by global commodity prices, INR/USD exchange rates and geopolitical factors. Gold does not generate any income (no dividend or interest)."),
            ("Concentration / Stock Risk", "Individual equity positions carry stock-specific risk including regulatory action, management changes, sector headwinds and liquidity events. Portfolio diversification is recommended."),
        ]

        has_insurance = recommendations and any(
            rec.get("product_type", "").lower() in ("life-insurance", "life_insurance") 
            for rec in recommendations
        )
        if has_insurance:
            risk_disclosures.append((
                "Life Insurance — IRDAI Regulated *",
                "Life insurance is regulated by IRDAI, NOT SEBI. SEBI has no jurisdiction over this product. Any grievance relating to insurance advice must be directed to IRDAI (www.irdai.gov.in). The IA's advisory services for this product are outside SEBI's regulatory purview and no recourse is available from SEBI or IAASB. Client has signed a separate non-SEBI disclosure and declaration."
            ))

        for label, text in risk_disclosures:
            if pdf.get_y() > 265:
                pdf.add_page()
            pdf.set_x(10)
            
            is_insurance = label.startswith("Life Insurance")
            
            if is_insurance:
                pdf.set_fill_color(254, 236, 236)  # Pink background for insurance key cell
                pdf.set_font("helvetica", "B", 7.5)
                pdf.set_text_color(180, 60, 60)   # Red text color
                pdf.cell(38, 6, f" {label}", border="LTB", fill=True)
            else:
                pdf.set_font("helvetica", "B", 7.5)
                pdf.set_text_color(*_NAVY)
                pdf.cell(38, 6, f" {label}", border="LTB")
                
            pdf.set_font("helvetica", "", 7)
            pdf.set_text_color(*_TEXT_DARK)
            pdf.multi_cell(152, 6, f" {text}", border="RTB")
        pdf.ln(6)

        # ══════════════════ SECTION G - Disclosures ══════════════════
        if pdf.get_y() > 210:
            pdf.add_page()
        InvestmentAdviceNotePDF._section_header(
            pdf, "Section G - Conflict of Interest and AI Usage Disclosure"
        )

        disclosure_fields = [
            ("Conflict of Interest", note_data.get("conflict_of_interest_text", "No conflicts of interest declared.")),
            ("No Execution by IA", note_data.get("no_execution_text", "The IA is not authorised to execute trades on behalf of the client.")),
            ("AI Tool Disclosure", note_data.get("ai_usage_text", "No AI tools were used in the preparation of this advice note.")),
        ]

        for label, text in disclosure_fields:
            if pdf.get_y() > 260:
                pdf.add_page()
            pdf.set_x(10)
            pdf.set_font("helvetica", "B", 7.5)
            pdf.set_text_color(*_NAVY)
            pdf.cell(38, 6, f" {label}", border="LTB")
            pdf.set_font("helvetica", "", 7)
            pdf.set_text_color(*_TEXT_DARK)
            pdf.multi_cell(152, 6, f" {text}", border="RTB")
        pdf.ln(8)

        # ══════════════════ DISCLAIMER ══════════════════
        if pdf.get_y() > 220:
            pdf.add_page()
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_RED_MUTED)
        pdf.cell(0, 6, "IMPORTANT DISCLAIMER", ln=True, align="C")
        pdf.set_font("helvetica", "I", 6.5)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.multi_cell(0, 4, _SEBI_DISCLAIMER, align="C")
        pdf.ln(3)

        # ══════════════════ SIGNATURES ══════════════════
        if pdf.get_y() > 240:
            pdf.add_page()

        sig_y = pdf.get_y() + 5
        pdf.set_y(sig_y)

        # Left: IA Signature
        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_NAVY)
        entity = entity_name or advisor_name or "Investment Advisor"
        pdf.cell(90, 5, f"For {entity}", ln=True)
        pdf.set_x(10)
        pdf.ln(12)
        pdf.set_x(10)
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(*_TEXT_DARK)
        pdf.cell(90, 4, "________________________________", ln=True)
        pdf.set_x(10)
        po_name = note_data.get("principal_officer_name", "Principal Officer")
        pdf.cell(90, 5, po_name, ln=True)
        pdf.set_x(10)
        pdf.set_font("helvetica", "I", 7)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.cell(90, 4, f"Principal Officer  |  Reg No: {ia_reg_no}", ln=True)
        pdf.set_x(10)
        pdf.cell(90, 4, f"Date: {note_data.get('date_of_issue', 'N/A')}", ln=True)

        # Right: Client Acknowledgement
        client_sig_y = sig_y
        pdf.set_xy(110, client_sig_y)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_NAVY)
        pdf.cell(90, 5, "Client Acknowledgement", ln=True)
        pdf.set_xy(110, client_sig_y + 17)
        pdf.set_font("helvetica", "", 7)
        pdf.set_text_color(*_TEXT_DARK)
        pdf.cell(90, 4, "________________________________", ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(90, 5, "I have read and understood this", ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(90, 5, "Investment Advice Note.", ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.set_font("helvetica", "B", 7)
        pdf.cell(90, 5, client.get("client_name", "Client"), ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.set_font("helvetica", "I", 7)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.cell(90, 4, f"Client ID: {client.get('client_code', 'N/A')}", ln=True)
        pdf.set_xy(110, pdf.get_y())
        pdf.cell(90, 4, "Date: ___________________", ln=True)

        # Record retention footer
        pdf.ln(8)
        pdf.set_font("helvetica", "I", 6)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.multi_cell(0, 4, _RECORD_RETENTION, align="C")

        return bytes(pdf.output())
