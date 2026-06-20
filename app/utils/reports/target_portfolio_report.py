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


# ── Landscape A4 dimensions ────────────────────────────────────────────────
# Page: 297mm wide × 210mm tall
# Usable: left=10, right=287, width=277; top=10, bottom ~195 (auto page break at 15mm)
PAGE_W = 277   # usable width
LEFT   = 10    # left margin x
PAGE_BREAK_Y = 185  # y threshold before adding a new page


class TargetPortfolioPDFGenerator:

    @staticmethod
    def _generate_pie_chart(sections: dict) -> Optional[str]:
        labels = []
        sizes = []
        for ac_key, section in sections.items():
            total_ac_pct = sum(float(e.get("percentage") or 0) for e in section.get("entries", []))
            if total_ac_pct > 0:
                labels.append(section.get("label", ac_key.upper()))
                sizes.append(total_ac_pct)
        if not sizes:
            return None
        try:
            colors_list = ['#001F3F', '#0046A0', '#00A896', '#F08080', '#FFA07A']
            fig, ax = plt.subplots(figsize=(5, 3.5))
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors_list[:len(sizes)],
                textprops=dict(color="black", fontsize=8)
            )
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
        labels = []
        sizes = []
        for e in entries:
            pct = float(e.get("percentage") or 0)
            if pct > 0:
                prod_name = e.get("product_name") or "Product"
                if len(prod_name) > 20:
                    prod_name = prod_name[:17] + "..."
                labels.append(prod_name)
                sizes.append(pct)
        if not sizes:
            return None
        try:
            colors_list = ['#4A90E2', '#50E3C2', '#F5A623', '#F8E71C', '#BD10E0', '#9013FE', '#7ED321', '#4A90E2']
            fig, ax = plt.subplots(figsize=(5, 3.5))
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                colors=colors_list[:len(sizes)],
                textprops=dict(color="black", fontsize=8)
            )
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
    def _draw_wrapped_header_row(pdf, headers, cols, line_h, table_header_bg, navy):
        """Draw a table header row where each cell wraps its text."""
        start_y = pdf.get_y()

        # Measure max lines needed across all headers
        max_lines = 1
        for h, w in zip(headers, cols):
            lines = pdf.multi_cell(w - 2, line_h, h, split_only=True)
            max_lines = max(max_lines, len(lines))
        row_h = max(8, max_lines * line_h + 1)

        pdf.set_fill_color(*table_header_bg)
        pdf.set_font("helvetica", "B", 8)
        pdf.set_text_color(*navy)
        x = LEFT
        for h, w in zip(headers, cols):
            # Draw filled border cell at uniform height
            pdf.set_xy(x, start_y)
            pdf.cell(w, row_h, '', border=1, fill=True)
            # Draw wrapped text on top
            pdf.set_xy(x + 1, start_y + 1)
            pdf.multi_cell(w - 2, line_h, h, border=0, fill=False, align='L')
            x += w

        pdf.set_xy(LEFT, start_y + row_h)

    @staticmethod
    def _render_cover_page(
        pdf, client_name, client_code, member_name, investor_code,
        objective, ia_data, generated_on, logo_path=None,
        export_basis="objective", asset_classes=None, allocation_date=None,
        version_number=None, is_draft=False,
    ):
        pdf.add_page()

        primary_blue = (0, 70, 160)
        accent_blue  = (0, 102, 204)
        text_dark    = (20, 20, 20)
        text_muted   = (120, 120, 120)
        draft_red    = (180, 30, 30)

        # Full-page border (landscape: 287mm wide × 200mm tall)
        pdf.set_draw_color(*primary_blue)
        pdf.set_line_width(0.5)
        pdf.rect(5, 5, 287, 200)
        pdf.set_line_width(0.2)

        # DRAFT watermark diagonal across page
        if is_draft:
            pdf.set_font("helvetica", "B", 60)
            pdf.set_text_color(220, 50, 50)
            pdf.set_xy(60, 70)
            pdf.rotate(30)
            pdf.cell(0, 0, "DRAFT", align="C")
            pdf.rotate(0)
            pdf.set_text_color(*text_dark)

        # Logo (centered on 297mm wide landscape page → centre x ≈ 148mm)
        pdf.set_y(25)
        if logo_path and os.path.exists(logo_path):
            pdf.image(logo_path, 124, pdf.get_y(), 40)
            pdf.set_y(pdf.get_y() + 45)
        else:
            pdf.set_y(40)

        # Entity name
        ia_entity = ""
        if ia_data:
            ia_entity = ia_data.get("name_of_entity") or ia_data.get("name_of_ia", "")
        if ia_entity:
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(*text_dark)
            pdf.cell(0, 8, ia_entity.upper(), ln=True, align="C")

        # Report title
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 26)
        pdf.set_text_color(*accent_blue)
        pdf.cell(0, 14, "TARGET PORTFOLIO REPORT", ln=True, align="C")

        # Version badge
        if version_number is not None or is_draft:
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(*draft_red if is_draft else (0, 100, 40))
            if is_draft and version_number is not None:
                status_label = f"DRAFT  —  Version {version_number}"
            elif is_draft:
                status_label = "DRAFT"
            else:
                status_label = f"Version {version_number}"
            pdf.cell(0, 7, status_label, ln=True, align="C")

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
        pdf.set_xy(119, pdf.get_y())
        pdf.cell(60, 1.5, "", fill=True, ln=True)

        # Client & investor info block
        pdf.ln(14)
        pdf.set_font("helvetica", "B", 16)
        pdf.set_text_color(*text_dark)
        pdf.cell(0, 10, client_name.upper(), ln=True, align="C")
        pdf.set_font("helvetica", "B", 11)
        pdf.set_text_color(*text_muted)
        pdf.cell(0, 6, f"CLIENT CODE: {client_code}", ln=True, align="C")

        # Show investor sub-block only when the member is not the client themselves
        is_self = member_name and client_name and member_name.strip().upper() == client_name.strip().upper()
        if not is_self and member_name:
            pdf.ln(4)
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(*text_dark)
            pdf.cell(0, 8, member_name.upper(), ln=True, align="C")
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(*text_muted)
            pdf.cell(0, 6, f"INVESTOR SUB-CODE: {investor_code}", ln=True, align="C")

        # Objective / filter badge
        pdf.ln(4)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_text_color(0, 100, 40)
        if export_basis == "product" and asset_classes:
            friendly_labels = {
                "shares": "Shares", "mf": "Mutual Funds", "etf": "ETF",
                "life_insurance": "Life Insurance", "health_insurance": "Health Insurance",
            }
            names = [friendly_labels.get(ac, ac.upper()) for ac in asset_classes]
            filter_text = f"PRODUCT FILTER:  {', '.join(names).upper()}"
        elif export_basis == "investor":
            filter_text = "CONSOLIDATED FAMILY PORTFOLIO"
        else:
            filter_text = f"OBJECTIVE FILTER:  {objective.upper()}"
        pdf.cell(0, 6, filter_text, ln=True, align="C")

        if allocation_date:
            pdf.ln(3)
            pdf.set_font("helvetica", "I", 10)
            pdf.set_text_color(*text_muted)
            pdf.cell(0, 6, f"Based on Asset Allocation dated {allocation_date}", ln=True, align="C")

        # Cover footer — sit below content but anchored near bottom (landscape ~210mm)
        pdf.set_y(max(pdf.get_y() + 8, 178))
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
        version_number: Optional[int] = None,
        is_draft: bool = False,
    ) -> bytes:
        advisor_name = ia_data.get("name_of_ia", "") if ia_data else ""
        entity_name  = ia_data.get("name_of_entity", "") if ia_data else ""
        ia_reg_no    = ia_data.get("ia_registration_number", "") if ia_data else ""

        if version_number is not None:
            ver_label = f"DRAFT  v{version_number}" if is_draft else f"Version {version_number}"
        elif is_draft:
            ver_label = "DRAFT"
        else:
            ver_label = ""

        pdf = BaseReportPDF(
            orientation='L',
            advisor_name=advisor_name,
            entity_name=entity_name,
            ia_reg_no=ia_reg_no,
            header_text="Target Portfolio Report -- Confidential",
            version=ver_label,
        )

        member_name:   str  = report_data.get("member_name", "")
        investor_code: str  = report_data.get("investor_code", "")
        objective:     str  = report_data.get("objective", "")
        sections:      dict = report_data.get("sections", {})

        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        generated_on = now_ist.strftime("%d %b %Y, %I:%M %p")

        # ── Cover page ──────────────────────────────────────────────────────
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
            version_number=version_number,
            is_draft=is_draft,
        )

        # ── Content page ─────────────────────────────────────────────────────
        pdf.add_page()

        # Color palette
        navy            = (0, 31, 63)
        accent_blue     = (0, 70, 160)
        light_blue_bg   = (235, 244, 255)
        accent_grey     = (245, 246, 248)
        table_header_bg = (220, 232, 246)
        border_color    = (200, 210, 220)
        text_dark       = (20, 20, 20)
        text_muted      = (110, 110, 110)
        row_alt         = (250, 251, 253)
        green_bg        = (235, 248, 235)
        draft_red       = (180, 30, 30)

        # ── Info summary bar ─────────────────────────────────────────────────
        pdf.set_fill_color(*light_blue_bg)
        pdf.rect(LEFT, pdf.get_y(), PAGE_W, 22, "F")
        info_y = pdf.get_y() + 4

        def info_col(label, value, x):
            pdf.set_xy(x, info_y)
            pdf.set_font("helvetica", "B", 7)
            pdf.set_text_color(*text_muted)
            pdf.cell(70, 4, label.upper(), ln=True)
            pdf.set_x(x)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(*text_dark)
            pdf.cell(70, 6, str(value or "--"))

        if export_basis == "investor":
            info_col("Client", f"{client_name} ({client_code})", 13)
            info_col("Investor", "All Active Members", 105)
            info_col("Sub-code", "ALL", 210)
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
            info_col("Investor", member_name, 105)
            info_col("Sub-code", investor_code, 210)
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
                    "shares": "Shares", "mf": "Mutual Funds", "etf": "ETF",
                    "life_insurance": "Life Ins", "health_insurance": "Health Ins",
                }
                names = [friendly_labels.get(ac, ac.upper()) for ac in asset_classes]
                pdf.cell(120, 6, f"  {', '.join(names)}  ", border=1, fill=True, align="C")
            else:
                pdf.cell(32, 4, "OBJECTIVE FILTER")
                pdf.set_xy(47, info_y + 11)
                pdf.set_fill_color(*green_bg)
                pdf.set_font("helvetica", "B", 9)
                pdf.set_text_color(0, 120, 50)
                pdf.cell(50, 6, f"  {objective}  ", border=1, fill=True, align="C")

        # Version badge in info bar
        if version_number is not None:
            ver_label = f"{'DRAFT · ' if is_draft else ''}v{version_number}"
            pdf.set_xy(230, info_y + 11)
            pdf.set_fill_color(*(220, 100, 100) if is_draft else (220, 232, 246))
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(*(180, 30, 30) if is_draft else navy)
            pdf.cell(40, 6, f"  {ver_label}  ", border=1, fill=True, align="C")

        pdf.set_y(info_y + 26)
        pdf.ln(5)

        # ── Transaction type helpers ─────────────────────────────────────────
        TX_TYPE_MAP = {
            "LUMP_SUM": "Lumpsum", "SIP": "SIP", "STP": "STP",
            "SWITCH_IN": "Switch In", "SINGLE_PAY": "Single Pay", "RECURRING": "Recurring",
            "HOLD": "Hold",
        }
        FREQ_MAP = {
            "WEEKLY": "Weekly", "MONTHLY": "Monthly", "QUARTERLY": "Quarterly",
            "HALF_YEARLY": "Half-yearly", "ANNUALLY": "Annually", "ANNUAL": "Annual",
            "BI_YEARLY": "Bi-yearly", "SINGLE_PAY": "Single Pay",
        }

        def build_tx_str(e):
            tx = e.get("transaction_type") or ""
            freq = e.get("frequency") or ""
            action = e.get("action") or ""
            tx_label = TX_TYPE_MAP.get(tx, tx)
            freq_label = FREQ_MAP.get(freq, freq)
            if tx == "LUMP_SUM":
                return f"Lumpsum ({action})" if action in ("Buy", "Sell") else "Lumpsum"
            parts = [p for p in [tx_label, freq_label] if p and p != tx_label or not freq_label]
            if tx_label and freq_label and tx_label != freq_label:
                return f"{tx_label}\n{freq_label}"
            return tx_label or freq_label or "--"

        # ── Column definitions ────────────────────────────────────────────────
        # Landscape usable width = 277mm  (left=10 .. right=287)
        # Non-insurance: 11 columns
        cols_std = [44, 13, 22, 22, 22, 11, 25, 13, 23, 34, 48]
        hdrs_std = [
            "Product", "% Invest", "Tx Type", "Existing Invest.",
            "Suggested Amt", "Inst.", "Anticipated Val",
            "Action", "Objective", "Reason for Inv.", "Remarks",
        ]

        # Life insurance: 8 columns
        cols_life = [48, 13, 26, 26, 25, 28, 38, 73]
        hdrs_life = [
            "Product", "% HLV", "Sum Assured", "Curr Sum Assured",
            "Suggested Amt", "Objective", "Reason", "Remarks",
        ]

        # Health insurance: 7 columns
        cols_health = [55, 14, 26, 26, 25, 30, 101]
        hdrs_health = [
            "Product", "% Health", "Sum Insured", "Curr Sum Insured",
            "Suggested Amt", "Objective", "Remarks",
        ]

        # Collect chart paths to render at the end
        chart_paths = []

        # ── Section renderer ─────────────────────────────────────────────────
        ASSET_CLASS_ORDER = ["shares", "mf", "etf", "life_insurance", "health_insurance"]

        def draw_section(ac_key: str, section: dict):
            label:   str  = section["label"]
            entries: list = section["entries"]
            is_life   = ac_key == "life_insurance"
            is_health = ac_key == "health_insurance"

            # Section header bar
            pdf.set_fill_color(*accent_grey)
            pdf.rect(LEFT, pdf.get_y(), PAGE_W, 9, "F")
            pdf.set_draw_color(*border_color)
            pdf.set_line_width(0.3)
            pdf.rect(LEFT, pdf.get_y(), PAGE_W, 9, "D")
            pdf.set_fill_color(*accent_blue)
            pdf.rect(LEFT, pdf.get_y(), 3, 9, "F")

            pdf.set_xy(16, pdf.get_y() + 2)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(*navy)
            pdf.cell(0, 5, label.upper(), ln=True)
            pdf.ln(1)

            if is_life:
                cols, headers = cols_life, hdrs_life
            elif is_health:
                cols, headers = cols_health, hdrs_health
            else:
                cols, headers = cols_std, hdrs_std

            # Wrapped header row
            TargetPortfolioPDFGenerator._draw_wrapped_header_row(
                pdf, headers, cols, 4.5, table_header_bg, navy
            )

            # Data rows
            h_unit = 4.5
            for idx, e in enumerate(entries):
                # Build product name (no tx info embedded — goes in its own column)
                product = e["product_name"]
                subtype = e.get("product_subtype")
                nature_val = e.get("nature")
                if subtype:
                    suffix = f" — {nature_val}" if nature_val else ""
                    product = f"{product} ({subtype}{suffix})"

                pct = f"{e['percentage']:.1f}%"
                obj_val  = e.get("objective") or "--"
                reason   = e.get("reason_for_investment") or "--"
                remarks  = e.get("remarks") or "--"

                suggested_val = e.get("suggested_investment_amount")
                action = e.get("action") or ""
                if suggested_val is not None:
                    suggested_str = f"(-Rs. {format_indian_number(suggested_val)})" if action == "Sell" \
                                    else f"Rs. {format_indian_number(suggested_val)}"
                else:
                    suggested_str = "--"

                if is_life:
                    sa  = e.get("sum_assured")
                    csa = e.get("current_sum_assured")
                    cell_texts = [
                        product, pct,
                        f"Rs. {format_indian_number(sa)}"  if sa  else "--",
                        f"Rs. {format_indian_number(csa)}" if csa else "--",
                        suggested_str, obj_val, reason, remarks,
                    ]
                elif is_health:
                    si  = e.get("sum_insured")
                    csi = e.get("current_sum_insured")
                    cell_texts = [
                        product, pct,
                        f"Rs. {format_indian_number(si)}"  if si  else "--",
                        f"Rs. {format_indian_number(csi)}" if csi else "--",
                        suggested_str, obj_val, remarks,
                    ]
                else:
                    tx = e.get("transaction_type") or ""
                    tx_str  = build_tx_str(e)
                    cur_acc = e.get("current_accumulation")
                    cur_acc_str = f"Rs. {format_indian_number(cur_acc)}" \
                                  if cur_acc is not None and tx in ("SIP", "LUMP_SUM") else "--"
                    noi = e.get("no_of_installments")
                    if tx == "SIP" and noi:
                        inst_str      = str(noi)
                        anticipated   = float(suggested_val or 0) * int(noi)
                        anticipated_str = f"Rs. {format_indian_number(anticipated)}"
                    else:
                        inst_str        = "--"
                        anticipated_str = "--"

                    action_str = "Hold" if tx == "HOLD" else (action if action in ("Buy", "Sell") else "--")
                    cell_texts = [
                        product, pct, tx_str, cur_acc_str,
                        suggested_str, inst_str, anticipated_str,
                        action_str, obj_val, reason, remarks,
                    ]

                # Measure row height — use w-2 to match the rendered inner width
                pdf.set_font("helvetica", "", 8)
                lines_per_col = [
                    max(len(pdf.multi_cell(w - 2, h_unit, str(t), split_only=True)), 1)
                    for t, w in zip(cell_texts, cols)
                ]
                row_h = max(max(lines_per_col) * h_unit + 4.0, 10.0)

                if pdf.get_y() + row_h > PAGE_BREAK_Y:
                    pdf.add_page()

                fill_color = row_alt if idx % 2 == 1 else (255, 255, 255)
                pdf.set_font("helvetica", "", 8)
                pdf.set_text_color(*text_dark)

                row_x, row_y = LEFT, pdf.get_y()
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

            # Collect chart for later (not rendered inline)
            if len(entries) > 1:
                chart_file = TargetPortfolioPDFGenerator._generate_product_pie_chart(entries, label)
                if chart_file and os.path.exists(chart_file):
                    chart_paths.append((label, chart_file))

        # ── Render sections ──────────────────────────────────────────────────
        if export_basis == "investor":
            for m_idx, member_item in enumerate(report_data.get("members", [])):
                member_sections = member_item.get("sections", {})
                if not member_sections:
                    continue
                if m_idx > 0:
                    pdf.add_page()
                pdf.ln(2)
                pdf.set_fill_color(*light_blue_bg)
                pdf.rect(LEFT, pdf.get_y(), PAGE_W, 10, "F")
                pdf.set_xy(13, pdf.get_y() + 2.5)
                pdf.set_font("helvetica", "B", 10)
                pdf.set_text_color(*navy)
                m_name = member_item.get("member_name", "")
                m_code = member_item.get("investor_code", "")
                pdf.cell(0, 5, f"INVESTOR: {m_name.upper()} ({m_code.upper()})")
                pdf.ln(12)
                for ac_key in ASSET_CLASS_ORDER:
                    if ac_key in member_sections:
                        if pdf.get_y() > PAGE_BREAK_Y:
                            pdf.add_page()
                        draw_section(ac_key, member_sections[ac_key])
        else:
            for ac_key in ASSET_CLASS_ORDER:
                if ac_key in sections:
                    if pdf.get_y() > PAGE_BREAK_Y:
                        pdf.add_page()
                    draw_section(ac_key, sections[ac_key])

        # ── Charts — second-to-last page(s) ─────────────────────────────────
        all_sections = {}
        if export_basis == "investor":
            for member_item in report_data.get("members", []):
                for ac_key, sec in member_item.get("sections", {}).items():
                    if ac_key not in all_sections:
                        all_sections[ac_key] = {"label": sec["label"], "entries": []}
                    all_sections[ac_key]["entries"].extend(sec.get("entries", []))
        else:
            all_sections = sections

        overall_chart = TargetPortfolioPDFGenerator._generate_pie_chart(all_sections)
        if overall_chart or chart_paths:
            pdf.add_page()
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(*navy)
            pdf.cell(0, 8, "PORTFOLIO ALLOCATION CHARTS", ln=True, align="C")
            pdf.ln(4)

            if overall_chart and os.path.exists(overall_chart):
                pdf.image(overall_chart, x=98, y=pdf.get_y(), w=100)
                pdf.set_y(pdf.get_y() + 80)
                pdf.ln(4)
                try:
                    os.remove(overall_chart)
                except Exception:
                    pass

            for i, (label, chart_file) in enumerate(chart_paths):
                x_pos = LEFT if i % 2 == 0 else LEFT + 140
                if i % 2 == 0 and i > 0:
                    pdf.set_y(pdf.get_y() + 75)
                if pdf.get_y() + 75 > PAGE_BREAK_Y and i % 2 == 0:
                    pdf.add_page()
                pdf.set_font("helvetica", "B", 9)
                pdf.set_text_color(*navy)
                pdf.set_xy(x_pos, pdf.get_y())
                pdf.cell(130, 5, label.upper())
                pdf.image(chart_file, x=x_pos, y=pdf.get_y() + 5, w=120)
                try:
                    os.remove(chart_file)
                except Exception:
                    pass

        # ── Disclaimer & signature — always last page ─────────────────────
        pdf.add_page()
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
        pdf.ln(10)

        sig_y = pdf.get_y()
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*navy)

        pdf.set_xy(10, sig_y)
        pdf.cell(130, 5, "Client Signature:")
        pdf.line(10, sig_y + 18, 110, sig_y + 18)
        pdf.set_xy(10, sig_y + 19)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*text_dark)
        pdf.cell(130, 4, f"Name: {client_name}", ln=True)
        pdf.set_x(10)
        pdf.cell(130, 4, "Date: ____/____/________")

        pdf.set_xy(160, sig_y)
        pdf.set_font("helvetica", "B", 9)
        pdf.set_text_color(*navy)
        pdf.cell(120, 5, "Investment Advisor Signature:")
        pdf.line(160, sig_y + 18, 280, sig_y + 18)
        pdf.set_xy(160, sig_y + 19)
        pdf.set_font("helvetica", "", 8)
        pdf.set_text_color(*text_dark)
        pdf.cell(120, 4, f"Name: {advisor_name}", ln=True)
        if entity_name:
            pdf.set_x(160)
            pdf.cell(120, 4, f"For: {entity_name}", ln=True)
        pdf.set_x(160)
        pdf.cell(120, 4, "Date: ____/____/________")

        return bytes(pdf.output())
