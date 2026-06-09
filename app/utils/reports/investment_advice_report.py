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

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor, Cm, Emu
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


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
            
        return grouped + dec_part
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
        pdf.ln(2)

    @staticmethod
    def _kv_row(pdf: BaseReportPDF, label: str, value: str, label_w: int = 42, val_w: int = 53):
        """Render a label:value pair in a 2-column grid row."""
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*_TEXT_MUTED)
        pdf.set_draw_color(*_BORDER)
        pdf.cell(label_w, 7, f" {label}", border="LBT")
        pdf.set_font("helvetica", "", 9)
        pdf.set_text_color(*_TEXT_DARK)
        pdf.cell(val_w, 7, f" {value or 'N/A'}", border="RBT")

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
    def generate_pdf(
        note_data: dict,
        ia_data: Optional[dict] = None,
        logo_path: Optional[str] = None,
    ) -> bytes:
        """
        Generate a complete SEBI Investment Advice Note PDF.
        
        Args:
            note_data: Full advice note dict from Bridge (includes client_snapshot, recommendations)
            ia_data: IA Master data dict
            logo_path: Absolute path to the IA logo file
        """
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

        client_fields = [
            ("Client Full Name", client.get("client_name", "N/A")),
            ("Client ID", client.get("client_code", "N/A")),
            ("PAN Number", client.get("pan_number", "N/A")),
            ("Client DOB", client.get("date_of_birth", "N/A")),
            ("Address", client.get("address", "N/A")),
            ("Email", client.get("email", "N/A")),
            ("Mobile", client.get("phone_number", "N/A")),
            ("Risk Profile", risk_profile_str),
            ("Risk Profile Date", client.get("risk_profile_date", "N/A")),
            ("Investment Horizon", client.get("investment_horizon", "N/A")),
            ("Annual Income Band", note_data.get("annual_income_band", "N/A")),
            ("Existing Liabilities", liabilities_str),
            ("Assets Under Advice", f"Rs. {float(note_data.get('assets_under_advice', 0)):,.0f}"),
            ("Primary Financial Goal", note_data.get("primary_financial_goal", "N/A")),
            ("Fee Mode", note_data.get("fee_mode", "N/A").replace("_", " ").title()),
            ("Fee Amount", f"Rs. {float(note_data.get('fee_amount', 0)):,.0f}"),
        ]
        InvestmentAdviceNotePDF._kv_grid(pdf, client_fields)

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
            label_map = {
                "fixed_deposits_bonds_percentage": "Fixed Deposits / Bonds",
                "mutual_fund_debt_percentage": "Debt Mutual Funds",
                "ulip_debt_percentage": "Debt ULIPs",
                "etf_debt_percentage": "Debt ETFs",
                "stocks_percentage": "Direct Equity (Stocks)",
                "mutual_fund_equity_percentage": "Equity Mutual Funds",
                "ulip_equity_percentage": "Equity ULIPs",
                "etf_equity_percentage": "Equity ETFs",
                "gold_etf_percentage": "Gold ETFs",
                "silver_etf_percentage": "Silver ETFs",
                "etf_commodity_percentage": "Commodity ETFs"
            }
            sub_parts = []
            for k, val in sub_allocs.items():
                try:
                    num_val = float(val) if val is not None else 0.0
                except Exception:
                    num_val = 0.0
                if num_val > 0:
                    friendly_name = label_map.get(k, k.replace("_percentage", "").replace("_", " ").title())
                    sub_parts.append(f"{friendly_name}: {num_val}%")
            if sub_parts:
                sub_text = "  |  ".join(sub_parts)
                InvestmentAdviceNotePDF._full_width_text(pdf, "Sub-Asset Breakdown", sub_text)

        date_of_alloc = note_data.get("date_of_allocation", "N/A")
        if date_of_alloc and date_of_alloc != "N/A":
            pdf.set_x(10)
            InvestmentAdviceNotePDF._kv_row(pdf, "Date of Allocation", str(date_of_alloc), 42, 148)
            pdf.ln()
        pdf.ln(6)

        # ══════════════════ SECTION C - Suitability ══════════════════
        InvestmentAdviceNotePDF._section_header(pdf, "Section C - Suitability Assessment [Regulation 17]")

        suit_fields = [
            ("Advice Suitable?", note_data.get("suitability_assessment", "N/A")),
            ("Suitability Basis", note_data.get("suitability_basis", "N/A")),
        ]
        InvestmentAdviceNotePDF._kv_grid(pdf, suit_fields)

        # Current Asset Allocation & Rebalancing (manual text areas)
        InvestmentAdviceNotePDF._full_width_text(
            pdf, "Current Allocation", note_data.get("current_asset_allocation", "N/A")
        )
        InvestmentAdviceNotePDF._full_width_text(
            pdf, "Rebalancing Rationale", note_data.get("rebalancing_rationale", "N/A")
        )
        pdf.ln(6)

        # ══════════════════ SECTION D - Recommendations ══════════════════
        InvestmentAdviceNotePDF._section_header(pdf, "Section D - Investment Recommendations [Regulation 16]")

        if recommendations:
            # Table header
            cols = [8, 52, 30, 30, 16, 28, 26]
            headers = ["#", "Product / Scheme", "ISIN / Code", "Type", "Action", "Amount", "Price/NAV"]

            pdf.set_fill_color(*_TABLE_HEADER_BG)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(*_NAVY)
            pdf.set_x(10)
            for h, w in zip(headers, cols):
                pdf.cell(w, 8, f" {h}", border=1, fill=True)
            pdf.ln()

            # Data rows
            h_unit = 4.5
            for idx, rec in enumerate(recommendations):
                cell_texts = [
                    str(idx + 1),
                    rec.get("product_name", "N/A"),
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
            InvestmentAdviceNotePDF._section_header(pdf, "Section E - Rationale for Advice [Regulation 16(c)]")

            for rec in recommendations:
                rationale = rec.get("rationale", "")
                if rationale:
                    name = rec.get("product_name", "Product")
                    action = rec.get("action", "")
                    pdf.set_x(10)
                    pdf.set_font("helvetica", "B", 8)
                    pdf.set_text_color(*_NAVY)
                    pdf.cell(42, 6, f" {name}", border="LT")
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
        InvestmentAdviceNotePDF._section_header(pdf, "Section F - Risk Disclosures [Regulation 16(d)]")

        risk_disclosures = [
            ("Market / Price Risk", "Equity and ETF investments are subject to market fluctuations. Past performance is not indicative of future returns."),
            ("Mutual Fund Risk", "Mutual Fund investments are subject to market risks. Please read all scheme documents carefully before investing."),
            ("Interest Rate Risk", "Debt fund NAVs are affected by interest rate movements. Suitable only for investors with appropriate horizon."),
            ("Commodity Risk", "Gold/Silver ETFs track commodity prices influenced by global factors and INR/USD exchange rates."),
            ("Concentration Risk", "Individual equity positions carry stock-specific risk. Portfolio diversification is recommended."),
        ]

        for label, text in risk_disclosures:
            if pdf.get_y() > 265:
                pdf.add_page()
            pdf.set_x(10)
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
            pdf, "Section G - Conflict of Interest and AI Usage Disclosure [Reg. 18 & 15(14)]"
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


# ════════════════════════════════════════════════════════════════════
# DOCX Generator
# ════════════════════════════════════════════════════════════════════

class InvestmentAdviceNoteDOCX:
    """Generates a SEBI-compliant Investment Advice Note Word document."""

    @staticmethod
    def _add_kv_table(doc, fields: List[tuple], style: str = "Table Grid"):
        """Add a 2-column key-value table."""
        table = doc.add_table(rows=len(fields), cols=2)
        table.style = style
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        for i, (label, value) in enumerate(fields):
            cell_label = table.cell(i, 0)
            cell_value = table.cell(i, 1)

            p_label = cell_label.paragraphs[0]
            run_label = p_label.add_run(str(label))
            run_label.bold = True
            run_label.font.size = Pt(9)

            p_value = cell_value.paragraphs[0]
            run_value = p_value.add_run(str(value or "N/A"))
            run_value.font.size = Pt(9)

    @staticmethod
    def _add_recommendation_table(doc, recommendations: List[dict]):
        """Add the recommendations table (Section D)."""
        headers = ["#", "Product / Scheme", "ISIN / Code", "Type", "Action", "Amount / Units", "Price / NAV"]
        table = doc.add_table(rows=1 + len(recommendations), cols=len(headers))
        table.style = "Light Grid Accent 1"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Header row
        hdr_row = table.rows[0]
        for i, h in enumerate(headers):
            cell = hdr_row.cells[i]
            p = cell.paragraphs[0]
            run = p.add_run(h)
            run.bold = True
            run.font.size = Pt(8)

        # Data rows
        for idx, rec in enumerate(recommendations):
            row = table.rows[idx + 1]
            values = [
                str(idx + 1),
                rec.get("product_name", "N/A"),
                rec.get("isin_code_scheme_code_uin", ""),
                rec.get("product_type", "").replace("_", " ").title(),
                rec.get("action", "BUY"),
                format_amount_units_python(rec),
                f"Rs. {float(rec['indicative_price_nav']):,.2f}" if rec.get("indicative_price_nav") else "N/A",
            ]
            for i, val in enumerate(values):
                cell = row.cells[i]
                p = cell.paragraphs[0]
                run = p.add_run(str(val))
                run.font.size = Pt(8)

    @staticmethod
    def generate_docx(
        note_data: dict,
        ia_data: Optional[dict] = None,
    ) -> io.BytesIO:
        """
        Generate a SEBI Investment Advice Note as a Word document.
        """
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx is not installed on this system.")

        doc = Document()
        client = note_data.get("client_snapshot", {})
        recommendations = note_data.get("recommendations", [])

        advisor_name = ia_data.get("name_of_ia", "") if ia_data else ""
        entity_name = ia_data.get("name_of_entity", "") if ia_data else ""
        ia_reg_no = ia_data.get("ia_registration_number", "") if ia_data else ""

        # ── Header ──
        section = doc.sections[0]
        header = section.header
        h_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        h_para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        h_run = h_para.add_run(f"{entity_name}\nSEBI Reg: {ia_reg_no}")
        h_run.font.size = Pt(8)
        h_run.font.color.rgb = RGBColor(0x60, 0x60, 0x60)

        # ── Title ──
        title = doc.add_heading("INVESTMENT ADVICE NOTE", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle = doc.add_paragraph(
            "Issued under SEBI (Investment Advisers) Regulations, 2013  |  Regulation 16 & 17"
        )
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in subtitle.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

        doc.add_paragraph()

        # ══════════════════ SECTION A ══════════════════
        doc.add_heading("Section A - Investment Adviser Details", level=1)
        basl_id = ia_data.get("basl_membership_id", "") if ia_data else ""
        website_val = ia_data.get("website", "") if ia_data else ""

        InvestmentAdviceNoteDOCX._add_kv_table(doc, [
            ("IA / Firm Name", entity_name or advisor_name),
            ("SEBI Registration No.", ia_reg_no),
            ("IAASB", f"BSE Limited (IAASB) - {basl_id}" if basl_id else "BSE Limited (IAASB)"),
            ("Website", website_val or "N/A"),
            ("Advice Note No.", note_data.get("advice_note_no", "N/A")),
            ("Date of Issue", note_data.get("date_of_issue", "N/A")),
            ("Principal Officer", note_data.get("principal_officer_name", "N/A")),
            ("PO Reg. No.", note_data.get("principal_officer_reg_no", "N/A")),
            ("Advice Category", note_data.get("advice_category", "Comprehensive Advisory")),
            ("Advice Validity", note_data.get("advice_validity_custom_text", "N/A")),
            ("Registered Address", ia_data.get("registered_address", "N/A") if ia_data else "N/A"),
        ])
        doc.add_paragraph()

        # ══════════════════ SECTION B ══════════════════
        doc.add_heading("Section B - Client Details and Risk Profile", level=1)

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

        if sub_allocs:
            label_map = {
                "fixed_deposits_bonds_percentage": "Fixed Deposits / Bonds",
                "mutual_fund_debt_percentage": "Debt Mutual Funds",
                "ulip_debt_percentage": "Debt ULIPs",
                "etf_debt_percentage": "Debt ETFs",
                "stocks_percentage": "Direct Equity (Stocks)",
                "mutual_fund_equity_percentage": "Equity Mutual Funds",
                "ulip_equity_percentage": "Equity ULIPs",
                "etf_equity_percentage": "Equity ETFs",
                "gold_etf_percentage": "Gold ETFs",
                "silver_etf_percentage": "Silver ETFs",
                "etf_commodity_percentage": "Commodity ETFs"
            }
            sub_parts = []
            for k, val in sub_allocs.items():
                try:
                    num_val = float(val) if val is not None else 0.0
                except Exception:
                    num_val = 0.0
                if num_val > 0:
                    friendly_name = label_map.get(k, k.replace("_percentage", "").replace("_", " ").title())
                    sub_parts.append(f"{friendly_name}: {num_val}%")
            if sub_parts:
                alloc_text += "\nSub-Asset Breakdown:\n" + "\n".join(f"• {x}" for x in sub_parts)

        InvestmentAdviceNoteDOCX._add_kv_table(doc, [
            ("Client Full Name", client.get("client_name", "N/A")),
            ("Client ID", client.get("client_code", "N/A")),
            ("PAN Number", client.get("pan_number", "N/A")),
            ("Client DOB", client.get("date_of_birth", "N/A")),
            ("Address", client.get("address", "N/A")),
            ("Email", client.get("email", "N/A")),
            ("Mobile", client.get("phone_number", "N/A")),
            ("Risk Profile", risk_profile_str),
            ("Risk Profile Date", client.get("risk_profile_date", "N/A")),
            ("Investment Horizon", client.get("investment_horizon", "N/A")),
            ("Annual Income Band", note_data.get("annual_income_band", "N/A")),
            ("Existing Liabilities", liabilities_str),
            ("Assets Under Advice", f"Rs. {float(note_data.get('assets_under_advice', 0)):,.0f}"),
            ("Primary Financial Goal", note_data.get("primary_financial_goal", "N/A")),
            ("Fee Mode", note_data.get("fee_mode", "N/A").replace("_", " ").title()),
            ("Fee Amount", f"Rs. {float(note_data.get('fee_amount', 0)):,.0f}"),
            ("Recommended Asset Allocation", alloc_text),
            ("Date of Allocation", str(note_data.get("date_of_allocation", "N/A"))),
        ])
        doc.add_paragraph()

        # ══════════════════ SECTION C ══════════════════
        doc.add_heading("Section C - Suitability Assessment [Regulation 17]", level=1)
        InvestmentAdviceNoteDOCX._add_kv_table(doc, [
            ("Advice Suitable?", note_data.get("suitability_assessment", "N/A")),
            ("Suitability Basis", note_data.get("suitability_basis", "N/A")),
            ("Current Asset Allocation", note_data.get("current_asset_allocation", "N/A")),
            ("Rebalancing Rationale", note_data.get("rebalancing_rationale", "N/A")),
        ])
        doc.add_paragraph()

        # ══════════════════ SECTION D ══════════════════
        doc.add_heading("Section D - Investment Recommendations [Regulation 16]", level=1)
        if recommendations:
            InvestmentAdviceNoteDOCX._add_recommendation_table(doc, recommendations)
        else:
            doc.add_paragraph("No recommendations attached to this advice note.").italic = True
        doc.add_paragraph()

        # ══════════════════ SECTION E ══════════════════
        if recommendations and any(r.get("rationale") for r in recommendations):
            doc.add_heading("Section E - Rationale for Advice [Regulation 16(c)]", level=1)
            rationale_rows = [
                (rec.get("product_name", "Product"), f"{rec.get('action', '')}. {rec.get('rationale', '')}")
                for rec in recommendations if rec.get("rationale")
            ]
            InvestmentAdviceNoteDOCX._add_kv_table(doc, rationale_rows)
            doc.add_paragraph()

        # ══════════════════ SECTION F ══════════════════
        doc.add_heading("Section F - Risk Disclosures [Regulation 16(d)]", level=1)
        InvestmentAdviceNoteDOCX._add_kv_table(doc, [
            ("Market / Price Risk", "Equity and ETF investments are subject to market fluctuations. Past performance is not indicative of future returns."),
            ("Mutual Fund Risk", "Mutual Fund investments are subject to market risks. Please read all scheme documents carefully before investing."),
            ("Interest Rate Risk", "Debt fund NAVs are affected by interest rate movements."),
            ("Commodity Risk", "Gold/Silver ETFs track commodity prices influenced by global factors and INR/USD exchange rates."),
            ("Concentration Risk", "Individual equity positions carry stock-specific risk. Portfolio diversification is recommended."),
        ])
        doc.add_paragraph()

        # ══════════════════ SECTION G ══════════════════
        doc.add_heading("Section G - Conflict of Interest and AI Usage Disclosure", level=1)
        InvestmentAdviceNoteDOCX._add_kv_table(doc, [
            ("Conflict of Interest", note_data.get("conflict_of_interest_text", "No conflicts of interest declared.")),
            ("No Execution by IA", note_data.get("no_execution_text", "The IA is not authorised to execute trades on behalf of the client.")),
            ("AI Tool Disclosure", note_data.get("ai_usage_text", "No AI tools were used in the preparation of this advice note.")),
        ])
        doc.add_paragraph()

        # ══════════════════ DISCLAIMER ══════════════════
        doc.add_heading("IMPORTANT DISCLAIMER", level=2)
        disclaimer_para = doc.add_paragraph(_SEBI_DISCLAIMER)
        disclaimer_para.style = doc.styles["Intense Quote"]
        for run in disclaimer_para.runs:
            run.font.size = Pt(8)

        # ══════════════════ SIGNATURES ══════════════════
        doc.add_paragraph()
        sig_table = doc.add_table(rows=4, cols=2)
        # Left: IA
        sig_table.cell(0, 0).text = f"For {entity_name or advisor_name or 'Investment Advisor'}"
        sig_table.cell(1, 0).text = "\n\n__________________________"
        po_name = note_data.get("principal_officer_name", "Principal Officer")
        sig_table.cell(2, 0).text = f"{po_name}\nPrincipal Officer\nSEBI Reg. No.: {ia_reg_no}"
        sig_table.cell(3, 0).text = f"Date: {note_data.get('date_of_issue', '_____________')}"
        # Right: Client
        sig_table.cell(0, 1).text = "Client Acknowledgement"
        sig_table.cell(1, 1).text = "\n\n__________________________"
        sig_table.cell(2, 1).text = (
            "I have read and understood this Investment Advice Note "
            "and the risks disclosed herein."
        )
        sig_table.cell(3, 1).text = (
            f"{client.get('client_name', 'Client')}\n"
            f"Client ID: {client.get('client_code', 'N/A')}\n"
            f"Date: ___________________"
        )

        # Format signature cells
        for row in sig_table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(9)

        # Record retention
        doc.add_paragraph()
        retention = doc.add_paragraph(_RECORD_RETENTION)
        retention.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in retention.runs:
            run.font.size = Pt(7)
            run.italic = True
            run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

        # ── Footer ──
        footer = section.footer
        f_p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        f_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f_run = f_p.add_run(
            f"Prepared by: {advisor_name}  |  Entity: {entity_name}  |  Reg No: {ia_reg_no}"
        )
        f_run.font.size = Pt(7)
        f_run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)
        f_run.italic = True

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
