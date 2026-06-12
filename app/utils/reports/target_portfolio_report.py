import os
import io
import tempfile
from datetime import datetime, timedelta
from typing import Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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


class TargetPortfolioPDFGenerator:

    @staticmethod
    def _generate_pie_chart(sections: dict) -> Optional[str]:
        """Create a pie chart for target portfolio sections and return its temp file path."""
        labels = []
        sizes = []
        
        # Calculate sum of percentages per asset class
        for ac_key, section in sections.items():
            total_ac_pct = sum(float(e.get("percentage") or 0) for e in section.get("entries", []))
            if total_ac_pct > 0:
                labels.append(section.get("label", ac_key.upper()))
                sizes.append(total_ac_pct)

        if not sizes:
            return None

        try:
            # Sleek, professional color palette matching the report
            # Navy, medium blue, teal, coral, peach
            colors_list = ['#001F3F', '#0046A0', '#00A896', '#F08080', '#FFA07A']
            
            fig, ax = plt.subplots(figsize=(4, 3))
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors_list[:len(sizes)],
                textprops=dict(color="black", fontsize=8)
            )
            # Make percentage labels bold and white for readability inside pie
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
                autotext.set_color('white')
                
            ax.axis('equal')
            plt.title("Target Portfolio Asset Allocation", fontsize=10, fontweight='bold', pad=10, color='#001F3F')
            
            fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            
            plt.savefig(temp_path, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            return temp_path
        except Exception:
            return None

    @staticmethod
    def _generate_product_pie_chart(entries: list, label: str) -> Optional[str]:
        """Create a pie chart for products within an asset class and return its temp file path."""
        labels = []
        sizes = []
        
        for e in entries:
            pct = float(e.get("percentage") or 0)
            if pct > 0:
                # Truncate product name if too long for the chart label
                prod_name = e.get("product_name") or "Product"
                if len(prod_name) > 20:
                    prod_name = prod_name[:17] + "..."
                labels.append(prod_name)
                sizes.append(pct)

        if not sizes:
            return None

        try:
            # Sleek, harmonized colors for products (using light/accent tones)
            colors_list = ['#4A90E2', '#50E3C2', '#F5A623', '#F8E71C', '#BD10E0', '#9013FE', '#7ED321', '#4A90E2']
            
            fig, ax = plt.subplots(figsize=(4, 3))
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors_list[:len(sizes)],
                textprops=dict(color="black", fontsize=8)
            )
            # Make percentage labels bold and white for readability inside pie
            for autotext in autotexts:
                autotext.set_fontsize(8)
                autotext.set_weight('bold')
                autotext.set_color('white')
                
            ax.axis('equal')
            plt.title(f"{label} Distribution", fontsize=10, fontweight='bold', pad=10, color='#001F3F')
            
            fd, temp_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            
            plt.savefig(temp_path, format='png', dpi=150, bbox_inches='tight')
            plt.close(fig)
            return temp_path
        except Exception:
            return None

    @staticmethod
    def _render_cover_page(
        pdf: BaseReportPDF,
        client_name: str,
        client_code: str,
        member_name: str,
        investor_code: str,
        objective: str,
        ia_data: Optional[dict],
        generated_on: str,
        logo_path: Optional[str] = None,
        export_basis: str = "objective",
        asset_classes: Optional[list] = None,
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

        # IA Logo (centered)
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
        pdf.ln(20)
        pdf.set_font("helvetica", "B", 26)
        pdf.set_text_color(*accent_blue)
        pdf.cell(0, 14, "TARGET PORTFOLIO REPORT", ln=True, align="C")

        # Subtitle
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(*text_muted)
        if export_basis == "product":
            pdf.cell(0, 6, "Product-wise Investment Summary", ln=True, align="C")
        elif export_basis == "investor":
            pdf.cell(0, 6, "Investor-wise Investment Summary", ln=True, align="C")
        else:
            pdf.cell(0, 6, "Objective-wise Investment Summary", ln=True, align="C")

        # Decorative bar
        pdf.ln(4)
        pdf.set_fill_color(*accent_blue)
        pdf.set_xy(75, pdf.get_y())
        pdf.cell(60, 1.5, "", fill=True, ln=True)

        # Client & investor info block
        pdf.ln(30)
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(*text_dark)
        pdf.cell(0, 10, client_name.upper(), ln=True, align="C")
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(*text_muted)
        pdf.cell(0, 6, f"CLIENT CODE: {client_code}", ln=True, align="C")

        pdf.ln(6)
        pdf.set_font("helvetica", "B", 13)
        pdf.set_text_color(*text_dark)
        pdf.cell(0, 8, member_name.upper() if member_name else "--", ln=True, align="C")
        pdf.set_font("helvetica", "", 10)
        pdf.set_text_color(*text_muted)
        pdf.cell(0, 6, f"INVESTOR SUB-CODE: {investor_code}", ln=True, align="C")

        # Objective badge
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 100, 40)
        if export_basis == "product" and asset_classes:
            friendly_labels = {
                "shares": "Shares",
                "mf": "Mutual Funds",
                "etf": "ETF",
                "life_insurance": "Life Insurance",
                "health_insurance": "Health Insurance",
            }
            names = [friendly_labels.get(ac, ac.upper()) for ac in asset_classes]
            filter_text = f"PRODUCT FILTER:  {', '.join(names).upper()}"
        elif export_basis == "investor":
            filter_text = "CONSOLIDATED FAMILY PORTFOLIO"
        else:
            filter_text = f"OBJECTIVE FILTER:  {objective.upper()}"
        pdf.cell(0, 6, filter_text, ln=True, align="C")


        # Asset Allocation Date line
        if allocation_date:
            pdf.ln(4)
            pdf.set_font("helvetica", "I", 10)
            pdf.set_text_color(*text_muted)
            pdf.cell(0, 6, f"Based on Asset Allocation dated {allocation_date}", ln=True, align="C")

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
        report_data: dict,
        client_name: str,
        client_code: str,
        ia_data: Optional[dict] = None,
        logo_path: Optional[str] = None,
        export_basis: str = "objective",
        asset_classes: Optional[list] = None,
        allocation_date: Optional[str] = None,
    ) -> bytes:
        advisor_name = ia_data.get("name_of_ia", "") if ia_data else ""
        entity_name = ia_data.get("name_of_entity", "") if ia_data else ""
        ia_reg_no = ia_data.get("ia_registration_number", "") if ia_data else ""

        pdf = BaseReportPDF(
            advisor_name=advisor_name,
            entity_name=entity_name,
            ia_reg_no=ia_reg_no,
            header_text="Target Portfolio Report -- Confidential",
        )

        member_name: str = report_data.get("member_name", "")
        investor_code: str = report_data.get("investor_code", "")
        objective: str = report_data.get("objective", "")
        sections: dict = report_data.get("sections", {})

        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        generated_on = now_ist.strftime("%d %b %Y, %I:%M %p")

        # ── Cover page ──
        TargetPortfolioPDFGenerator._render_cover_page(
            pdf=pdf,
            client_name=client_name,
            client_code=client_code,
            member_name=member_name,
            investor_code=investor_code,
            objective=objective,
            ia_data=ia_data,
            generated_on=generated_on,
            logo_path=logo_path,
            export_basis=export_basis,
            asset_classes=asset_classes,
            allocation_date=allocation_date,
        )

        # ── Content page ──
        pdf.add_page()

        # Color palette
        navy = (0, 31, 63)
        accent_blue = (0, 70, 160)
        light_blue_bg = (235, 244, 255)
        accent_grey = (245, 246, 248)
        table_header_bg = (220, 232, 246)
        border_color = (200, 210, 220)
        text_dark = (20, 20, 20)
        text_muted = (110, 110, 110)
        row_alt = (250, 251, 253)
        green_bg = (235, 248, 235)

        # ── Info summary bar ──
        pdf.set_fill_color(*light_blue_bg)
        pdf.rect(10, pdf.get_y(), 190, 22, "F")
        info_y = pdf.get_y() + 4

        def info_col(label, value, x):
            pdf.set_xy(x, info_y)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(*text_muted)
            pdf.cell(60, 4, label.upper(), ln=True)
            pdf.set_x(x)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(*text_dark)
            pdf.cell(60, 6, str(value or "--"))
        if export_basis == "investor":
            info_col("Client", f"{client_name} ({client_code})", 13)
            info_col("Investor", "All Active Members", 85)
            info_col("Sub-code", "ALL", 148)

            pdf.set_xy(13, info_y + 12)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(*text_muted)
            pdf.cell(32, 4, "EXPORT BASIS")
            pdf.set_xy(47, info_y + 11)
            pdf.set_fill_color(*green_bg)
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(0, 120, 50)
            pdf.cell(40, 6, "  Investor-wise  ", border=1, fill=True, align="C")
        else:
            info_col("Client", f"{client_name} ({client_code})", 13)
            info_col("Investor", member_name, 85)
            info_col("Sub-code", investor_code, 148)

            pdf.set_xy(13, info_y + 12)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(*text_muted)

            if export_basis == "product" and asset_classes:
                pdf.cell(32, 4, "PRODUCT FILTER")
                pdf.set_xy(47, info_y + 11)
                pdf.set_fill_color(*green_bg)
                pdf.set_font("helvetica", "B", 8)
                pdf.set_text_color(0, 120, 50)
                friendly_labels = {
                    "shares": "Shares",
                    "mf": "Mutual Funds",
                    "etf": "ETF",
                    "life_insurance": "Life Ins",
                    "health_insurance": "Health Ins",
                }
                names = [friendly_labels.get(ac, ac.upper()) for ac in asset_classes]
                pdf.cell(100, 6, f"  {', '.join(names)}  ", border=1, fill=True, align="C")
            else:
                pdf.cell(32, 4, "OBJECTIVE FILTER")
                pdf.set_xy(47, info_y + 11)
                pdf.set_fill_color(*green_bg)
                pdf.set_font("helvetica", "B", 9)
                pdf.set_text_color(0, 120, 50)
                pdf.cell(40, 6, f"  {objective}  ", border=1, fill=True, align="C")

        pdf.set_y(info_y + 26)
        pdf.ln(5)

        # ── Section renderer ──
        ASSET_CLASS_ORDER = ["shares", "mf", "etf", "life_insurance", "health_insurance"]

        def draw_section(ac_key: str, section: dict):
            label: str = section["label"]
            entries: list = section["entries"]
            is_life = ac_key == "life_insurance"
            is_health = ac_key == "health_insurance"

            # Section header bar
            pdf.set_fill_color(*accent_grey)
            pdf.rect(10, pdf.get_y(), 190, 9, "F")
            pdf.set_draw_color(*border_color)
            pdf.set_line_width(0.3)
            pdf.rect(10, pdf.get_y(), 190, 9, "D")
            pdf.set_fill_color(*accent_blue)
            pdf.rect(10, pdf.get_y(), 3, 9, "F")

            pdf.set_xy(16, pdf.get_y() + 2)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(*navy)
            pdf.cell(0, 5, label.upper(), ln=True)
            pdf.ln(1)

            # Column definitions
            if is_life:
                cols = [55, 18, 25, 27, 30, 35]
                headers = ["Product", "% HLV", "Suggested Amt", "Objective", "Reason", "Suitability"]
            elif is_health:
                cols = [60, 20, 27, 33, 50]
                headers = ["Product", "% Health", "Suggested Amt", "Objective", "Suitability"]
            else:
                cols = [65, 20, 27, 33, 45]
                headers = ["Product", "% Invest", "Suggested Amt", "Objective", "Suitability"]

            # Table header row
            pdf.set_fill_color(*table_header_bg)
            pdf.set_font("helvetica", "B", 8)
            pdf.set_text_color(*navy)
            for h, w in zip(headers, cols):
                pdf.cell(w, 8, f" {h}", border=1, fill=True)
            pdf.ln()

            # Data rows
            h_unit = 4.5
            for idx, e in enumerate(entries):
                product = e["product_name"]
                subtype = e.get("product_subtype")
                nature_val = e.get("nature")
                if subtype:
                    suffix = f" — {nature_val}" if nature_val else ""
                    product = f"{product} ({subtype}{suffix})"

                tx_type = e.get("transaction_type")
                freq = e.get("frequency")
                if tx_type or freq:
                    tx_type_map = {
                        "LUMP_SUM": "Lumpsum",
                        "SIP": "SIP",
                        "STP": "STP",
                        "SINGLE_PAY": "Single Pay",
                        "RECURRING": "Recurring",
                    }
                    freq_map = {
                        "LUMP_SUM": "Lumpsum",
                        "WEEKLY": "Weekly",
                        "MONTHLY": "Monthly",
                        "QUARTERLY": "Quarterly",
                        "HALF_YEARLY": "Half-yearly",
                        "ANNUAL": "Annual",
                        "BI_YEARLY": "Bi-yearly",
                        "SINGLE_PAY": "Single Pay",
                        "ANNUALLY": "Annually",
                    }
                    tx_label = tx_type_map.get(tx_type, str(tx_type)) if tx_type else ""
                    freq_label = freq_map.get(freq, str(freq)) if freq else ""
                    if tx_label and freq_label:
                        if tx_label == freq_label:
                            tx_desc = tx_label
                        else:
                            tx_desc = f"{tx_label} ({freq_label})"
                    else:
                        tx_desc = tx_label or freq_label
                    product = f"{product}\n{tx_desc}"

                pct = f"{e['percentage']:.1f}%"
                obj_val = e["objective"]
                reason = e["reason_for_investment"]
                suitability = e["remarks"] or "--"

                suggested_val = e.get("suggested_investment_amount")
                suggested_str = f"Rs. {format_indian_number(suggested_val)}" if suggested_val is not None else "--"

                if is_life:
                    cell_texts = [product, pct, suggested_str, obj_val, reason, suitability]
                elif is_health:
                    cell_texts = [product, pct, suggested_str, obj_val, suitability]
                else:
                    cell_texts = [product, pct, suggested_str, obj_val, suitability]

                lines_per_col = [
                    max(len(pdf.multi_cell(w, h_unit, str(t), split_only=True)), 1)
                    for t, w in zip(cell_texts, cols)
                ]
                row_h = max(max(lines_per_col) * h_unit + 4.0, 10.0)

                if pdf.get_y() + row_h > 272:
                    pdf.add_page()

                fill_color = row_alt if idx % 2 == 1 else (255, 255, 255)
                pdf.set_font("helvetica", "", 8)
                pdf.set_text_color(*text_dark)

                row_x, row_y = pdf.get_x(), pdf.get_y()
                for t, w, lines_cnt in zip(cell_texts, cols, lines_per_col):
                    pdf.set_fill_color(*fill_color)
                    pdf.rect(row_x, row_y, w, row_h, "F")
                    pdf.rect(row_x, row_y, w, row_h, "D")
                    y_offset = (row_h - (lines_cnt * h_unit)) / 2.0
                    pdf.set_xy(row_x + 1, row_y + y_offset)
                    pdf.multi_cell(w - 2, h_unit, str(t), align="L")
                    row_x += w

                pdf.set_y(row_y + row_h)

            pdf.ln(7)

            if len(entries) > 1:
                chart_file = TargetPortfolioPDFGenerator._generate_product_pie_chart(entries, label)
                if chart_file and os.path.exists(chart_file):
                    if pdf.get_y() > 200:
                        pdf.add_page()
                    pdf.image(chart_file, x=65, y=pdf.get_y(), w=80)
                    pdf.set_y(pdf.get_y() + 65)
                    pdf.ln(7)
                    try:
                        os.remove(chart_file)
                    except Exception:
                        pass

        if export_basis == "investor":
            for m_idx, member_item in enumerate(report_data.get("members", [])):
                member_sections = member_item.get("sections", {})
                if not member_sections:
                    continue

                if m_idx > 0:
                    pdf.add_page()

                pdf.ln(2)
                pdf.set_fill_color(*light_blue_bg)
                pdf.rect(10, pdf.get_y(), 190, 10, "F")
                pdf.set_xy(13, pdf.get_y() + 2.5)
                pdf.set_font("helvetica", "B", 10)
                pdf.set_text_color(*navy)
                m_name = member_item.get("member_name", "")
                m_code = member_item.get("investor_code", "")
                pdf.cell(0, 5, f"INVESTOR: {m_name.upper()} ({m_code.upper()})")
                pdf.ln(12)

                # Render Member Pie Chart
                chart_file = TargetPortfolioPDFGenerator._generate_pie_chart(member_sections)
                if chart_file and os.path.exists(chart_file):
                    if pdf.get_y() > 200:
                        pdf.add_page()
                    pdf.image(chart_file, x=65, y=pdf.get_y(), w=80)
                    pdf.set_y(pdf.get_y() + 65)
                    pdf.ln(5)
                    try:
                        os.remove(chart_file)
                    except Exception:
                        pass

                for ac_key in ASSET_CLASS_ORDER:
                    if ac_key in member_sections:
                        if pdf.get_y() > 252:
                            pdf.add_page()
                        draw_section(ac_key, member_sections[ac_key])
        else:
            # Render Single Member Pie Chart
            chart_file = TargetPortfolioPDFGenerator._generate_pie_chart(sections)
            if chart_file and os.path.exists(chart_file):
                pdf.image(chart_file, x=65, y=pdf.get_y(), w=80)
                pdf.set_y(pdf.get_y() + 65)
                pdf.ln(5)
                try:
                    os.remove(chart_file)
                except Exception:
                    pass

            for ac_key in ASSET_CLASS_ORDER:
                if ac_key in sections:
                    if pdf.get_y() > 252:
                        pdf.add_page()
                    draw_section(ac_key, sections[ac_key])

        pdf.ln(4)
        pdf.set_font("helvetica", "I", 8)
        pdf.set_text_color(*text_muted)
        pdf.multi_cell(
            0, 5,
            "This report is generated for internal record and analytical purposes only. "
            "The information is based on data recorded in the system and does not constitute investment advice. "
            "Only active portfolio entries matching the selected filter are included.",
            align="C",
        )
        pdf.ln(6)

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
