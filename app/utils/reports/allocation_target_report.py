import os
from datetime import datetime, timedelta
from typing import Optional
from app.utils.pdf_generator import BaseReportPDF


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


class AllocationTargetPDFGenerator:

    @staticmethod
    def _render_cover_page(
        pdf: BaseReportPDF,
        client_name: str,
        client_code: str,
        member_name: str,
        member_code: str,
        total_portfolio_size: float,
        ia_data: Optional[dict],
        generated_on: str,
        logo_path: Optional[str] = None,
        allocation_date: Optional[str] = None,
    ):
        pdf.add_page()

        primary_blue = (0, 70, 160)
        accent_blue = (0, 102, 204)
        text_dark = (20, 20, 20)
        text_muted = (120, 120, 120)

        # Full-page border
        pdf.set_draw_color(*primary_blue)
        pdf.set_line_width(0.5)
        pdf.rect(5, 5, 200, 287)
        pdf.set_line_width(0.2)

        # IA Logo
        pdf.set_y(40)
        if logo_path and os.path.exists(logo_path):
            pdf.image(logo_path, 85, pdf.get_y(), 40)
            pdf.set_y(pdf.get_y() + 50)
        else:
            pdf.set_y(60)

        # Entity name
        ia_entity = ""
        if ia_data:
            ia_entity = ia_data.get("name_of_entity") or ia_data.get("name_of_ia", "")
        if ia_entity:
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(*text_dark)
            pdf.cell(0, 8, ia_entity.upper(), ln=True, align="C")

        # Report title
        pdf.ln(15)
        pdf.set_font("helvetica", "B", 24)
        pdf.set_text_color(*accent_blue)
        pdf.cell(0, 14, "TARGET ASSET ALLOCATION REPORT", ln=True, align="C")

        # Subtitle
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(*text_muted)
        pdf.cell(0, 6, "Calculated Target Investment Breakdown", ln=True, align="C")

        # Decorative bar
        pdf.ln(4)
        pdf.set_fill_color(*accent_blue)
        pdf.set_xy(75, pdf.get_y())
        pdf.cell(60, 1.5, "", fill=True, ln=True)

        # Client info block
        pdf.ln(25)
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(*text_dark)
        pdf.cell(0, 10, client_name.upper(), ln=True, align="C")
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(*text_muted)
        pdf.cell(0, 6, f"CLIENT CODE: {client_code}", ln=True, align="C")

        # Determine if member is the client themselves
        is_same_person = (
            member_name.strip().upper() == client_name.strip().upper()
            or member_code.strip() == client_code.strip()
        )

        if not is_same_person:
            pdf.ln(6)
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(*text_dark)
            pdf.cell(0, 8, member_name.upper() if member_name else "--", ln=True, align="C")
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(*text_muted)
            pdf.cell(0, 6, f"INVESTOR SUB-CODE: {member_code}", ln=True, align="C")

        # Portfolio size badge (Centered at x = 45 for width = 120)
        pdf.ln(12)
        pdf.set_fill_color(235, 248, 235)
        pdf.set_draw_color(0, 120, 50)
        pdf.set_line_width(0.3)
        pdf.set_xy(45, pdf.get_y())
        pdf.set_font("helvetica", "B", 12)
        pdf.set_text_color(0, 100, 40)
        pdf.cell(120, 12, f"Total Portfolio Size: Rs. {format_indian_number(total_portfolio_size)}", border=1, fill=True, ln=True, align="C")
        pdf.set_line_width(0.2)

        # Asset Allocation Date line
        if allocation_date:
            pdf.ln(4)
            pdf.set_font("helvetica", "I", 10)
            pdf.set_text_color(*text_muted)
            pdf.cell(0, 6, f"Based on Asset Allocation Report dated {allocation_date}", ln=True, align="C")

        # Cover footer
        pdf.set_y(248)
        pdf.set_font("helvetica", "I", 9)
        pdf.set_text_color(*text_muted)
        pdf.cell(0, 6, f"Report Generated on: {generated_on}", ln=True, align="C")

        if ia_data:
            reg_no = ia_data.get("ia_registration_number", "")
            if reg_no:
                pdf.set_font("helvetica", "", 9)
                pdf.cell(0, 6, f"Investment Advisor Reg No: {reg_no}", ln=True, align="C")

    @staticmethod
    def generate_report(
        allocation_data: dict,
        total_portfolio_size: float,
        client_name: str,
        client_code: str,
        member_name: str,
        member_code: str,
        ia_data: Optional[dict] = None,
        logo_path: Optional[str] = None,
    ) -> bytes:
        advisor_name = ia_data.get("name_of_ia", "") if ia_data else ""
        entity_name = ia_data.get("name_of_entity", "") if ia_data else ""
        ia_reg_no = ia_data.get("ia_registration_number", "") if ia_data else ""

        pdf = BaseReportPDF(
            advisor_name=advisor_name,
            entity_name=entity_name,
            ia_reg_no=ia_reg_no,
            header_text="Target Allocation Report -- Confidential",
        )

        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        generated_on = now_ist.strftime("%d %b %Y, %I:%M %p")

        # Extract and format the asset allocation date from allocation_data
        raw_date = allocation_data.get("created_at")
        allocation_date_str = ""
        if raw_date:
            try:
                if "T" in raw_date:
                    dt_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    allocation_date_str = dt_obj.strftime("%d %b %Y")
                else:
                    allocation_date_str = raw_date
            except Exception:
                allocation_date_str = str(raw_date)[:10]

        # 1. Cover Page
        AllocationTargetPDFGenerator._render_cover_page(
            pdf=pdf,
            client_name=client_name,
            client_code=client_code,
            member_name=member_name,
            member_code=member_code,
            total_portfolio_size=total_portfolio_size,
            ia_data=ia_data,
            generated_on=generated_on,
            logo_path=logo_path,
            allocation_date=allocation_date_str or None,
        )

        # 2. Content Page
        pdf.add_page()

        # Colors
        navy = (0, 31, 63)
        accent_blue = (0, 70, 160)
        light_blue_bg = (235, 244, 255)
        table_header_bg = (220, 232, 246)
        border_color = (200, 210, 220)
        text_dark = (20, 20, 20)
        text_muted = (110, 110, 110)
        row_alt = (250, 251, 253)

        # Client details card header
        is_same_person = (
            member_name.strip().upper() == client_name.strip().upper()
            or member_code.strip() == client_code.strip()
        )

        pdf.set_fill_color(*light_blue_bg)
        pdf.rect(10, pdf.get_y(), 190, 14, "F")
        pdf.set_xy(13, pdf.get_y() + 2)
        pdf.set_font("helvetica", "B", 7)
        pdf.set_text_color(*text_muted)
        
        if is_same_person:
            pdf.cell(140, 3, "CLIENT")
            pdf.cell(50, 3, "PORTFOLIO SIZE")
            pdf.ln(3)
            pdf.set_x(13)
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(*text_dark)
            pdf.cell(140, 5, f"{client_name} ({client_code})")
            pdf.cell(50, 5, f"Rs. {format_indian_number(total_portfolio_size)}")
        else:
            pdf.cell(85, 3, "CLIENT")
            pdf.cell(55, 3, "INVESTOR")
            pdf.cell(50, 3, "PORTFOLIO SIZE")
            pdf.ln(3)
            pdf.set_x(13)
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(*text_dark)
            pdf.cell(85, 5, f"{client_name} ({client_code})")
            pdf.cell(55, 5, f"{member_name} ({member_code})")
            pdf.cell(50, 5, f"Rs. {format_indian_number(total_portfolio_size)}")
        
        pdf.set_y(pdf.get_y() + 10)
        pdf.ln(5)

        # Target Allocation Table
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(*navy)
        pdf.cell(0, 6, "Calculated Sub-Asset Targets Breakdown", ln=True)
        pdf.ln(2)

        # Table Header
        cols = [100, 45, 45]
        headers = ["Asset / Sub-Asset Class", "Recommended %", "Target Amount (Rs.)"]
        pdf.set_fill_color(*table_header_bg)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*navy)
        for h, w in zip(headers, cols):
            pdf.cell(w, 8, f" {h}", border=1, fill=True)
        pdf.ln()

        # Map categories
        categories = [
            {
                "label": "Equities",
                "pct_key": "equities_percentage",
                "items": [
                    ("stocks_percentage", "Stocks / Shares"),
                    ("mutual_fund_equity_percentage", "Mutual Fund (Equity)"),
                    ("ulip_equity_percentage", "ULIP (Equity)"),
                    ("etf_equity_percentage", "ETF (Equity)"),
                ]
            },
            {
                "label": "Debt Securities",
                "pct_key": "debt_securities_percentage",
                "items": [
                    ("fixed_deposits_bonds_percentage", "Fixed Deposits & Bonds"),
                    ("mutual_fund_debt_percentage", "Mutual Fund (Debt)"),
                    ("ulip_debt_percentage", "ULIP (Debt)"),
                    ("etf_debt_percentage", "ETF (Debt)"),
                ]
            },
            {
                "label": "Commodities",
                "pct_key": "commodities_percentage",
                "items": [
                    ("gold_etf_percentage", "Gold ETF"),
                    ("silver_etf_percentage", "Silver ETF"),
                    ("etf_commodity_percentage", "ETF (Commodity)"),
                ]
            }
        ]

        pdf.set_draw_color(*border_color)
        pdf.set_line_width(0.3)

        for cat in categories:
            cat_pct = float(allocation_data.get(cat["pct_key"]) or 0)
            cat_amt = (cat_pct / 100.0) * total_portfolio_size

            # Parent category row
            pdf.set_fill_color(240, 242, 245)
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(*navy)
            
            pdf.cell(cols[0], 8, f" {cat['label']}", border=1, fill=True)
            pdf.cell(cols[1], 8, f" {cat_pct:.1f}%", border=1, fill=True)
            pdf.cell(cols[2], 8, f" Rs. {format_indian_number(cat_amt)}", border=1, fill=True)
            pdf.ln()

            # Sub-asset rows
            pdf.set_font("helvetica", "", 8.5)
            pdf.set_text_color(*text_dark)
            
            sub_idx = 0
            for key, label in cat["items"]:
                item_pct = float(allocation_data.get(key) or 0)
                if item_pct <= 0:
                    continue
                
                item_amt = (item_pct / 100.0) * cat_amt

                fill_color = row_alt if sub_idx % 2 == 1 else (255, 255, 255)
                pdf.set_fill_color(*fill_color)

                pdf.cell(cols[0], 7.5, f"   •  {label}", border=1, fill=True)
                pdf.cell(cols[1], 7.5, f" {item_pct:.1f}%", border=1, fill=True)
                pdf.cell(cols[2], 7.5, f" Rs. {format_indian_number(item_amt)}", border=1, fill=True)
                pdf.ln()
                sub_idx += 1

            # Draw double-line separator at the bottom of the category block
            pdf.set_draw_color(*border_color)
            pdf.set_line_width(0.3)
            pdf.line(10, pdf.get_y() + 0.8, 200, pdf.get_y() + 0.8)
            pdf.set_y(pdf.get_y() + 1.6)

        pdf.ln(6)

        # Disclaimer
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(*text_muted)
        pdf.multi_cell(
            0, 4.5,
            "Declaration: This report provides the calculated target breakdown of asset allocation based "
            "strictly on the client's risk assessment and standard investment templates. It is intended "
            "to guide the client and advisor in finalizing specific product recommendations in the next step. "
            "This document is confidential and legally binding upon signature by both parties.",
            align="L"
        )
        pdf.ln(10)

        # Signature Block
        sig_y = pdf.get_y()
        if sig_y > 240:
            pdf.add_page()
            sig_y = pdf.get_y()

        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*navy)

        # Client sign
        pdf.set_xy(10, sig_y)
        pdf.cell(90, 5, "Client Signature:")
        pdf.line(10, sig_y + 18, 85, sig_y + 18)
        pdf.set_xy(10, sig_y + 19)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*text_dark)
        pdf.cell(90, 4, f"Name: {client_name}", ln=True)
        pdf.set_x(10)
        pdf.cell(90, 4, "Date: ____/____/________")

        # Advisor sign
        pdf.set_xy(110, sig_y)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*navy)
        pdf.cell(90, 5, "Investment Advisor Signature:")
        pdf.line(110, sig_y + 18, 185, sig_y + 18)
        pdf.set_xy(110, sig_y + 19)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*text_dark)
        pdf.cell(90, 4, f"Name: {advisor_name}", ln=True)
        if entity_name:
            pdf.set_x(110)
            pdf.cell(90, 4, f"For: {entity_name}", ln=True)
        pdf.set_x(110)
        pdf.cell(90, 4, "Date: ____/____/________")

        return bytes(pdf.output())
