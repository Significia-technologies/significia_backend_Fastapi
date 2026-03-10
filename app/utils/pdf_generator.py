import io
from datetime import datetime
from fpdf import FPDF
from typing import List

class IAPDFGenerator:
    @staticmethod
    def generate_ia_report(ia_data: dict, employees: List[dict]) -> bytes:
        pdf = FPDF()
        pdf.add_page()
        
        # Add Logo if exists (simulated for now with text box if path exists)
        # In a real scenario, we'd use pdf.image(ia_data['ia_logo_path'], ...)
        
        # Set font
        pdf.set_font("helvetica", "B", 20)
        pdf.set_text_color(33, 37, 41) # Dark grey
        pdf.cell(0, 15, "INVESTMENT ADVISOR MASTER REPORT", ln=True, align="C")
        
        pdf.set_font("helvetica", "I", 10)
        pdf.set_text_color(108, 117, 125) # Muted grey
        current_date = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        pdf.cell(0, 10, f"Generated on: {current_date}", ln=True, align="R")
        pdf.ln(5)

        # Draw a horizontal line using a thin cell
        pdf.set_fill_color(0, 123, 255) # Primary blue
        pdf.cell(0, 1, "", ln=True, fill=True)
        pdf.ln(10)
        
        # Section Header helper
        def section_header(title):
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(0, 123, 255)
            pdf.cell(0, 10, title, ln=True)
            pdf.ln(2)

        section_header("Investment Advisor Profile")
        
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(33, 37, 41)
        
        fields = [
            ("Name of IA", ia_data.get('name_of_ia')),
            ("Nature of Entity", ia_data.get('nature_of_entity', '').capitalize()),
            ("Entity Name", ia_data.get('name_of_entity') or "N/A"),
            ("Reg Number", ia_data.get('ia_registration_number')),
            ("Reg Date", str(ia_data.get('date_of_registration'))),
            ("Expiry Date", str(ia_data.get('date_of_registration_expiry'))),
            ("Address", ia_data.get('registered_address')),
            ("Email", ia_data.get('registered_email_id')),
            ("Phone", ia_data.get('registered_contact_number'))
        ]
        
        for field, value in fields:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(50, 8, f"{field}:", 0)
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 8, str(value), 0, ln=True)
        
        pdf.ln(10)
        section_header("Bank Details")
        
        bank_fields = [
            ("A/C Number", ia_data.get('bank_account_number')),
            ("Bank Name", ia_data.get('bank_name')),
            ("Branch", ia_data.get('bank_branch')),
            ("IFSC Code", ia_data.get('ifsc_code'))
        ]
        
        for field, value in bank_fields:
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(50, 8, f"{field}:", 0)
            pdf.set_font("helvetica", "", 10)
            pdf.cell(0, 8, str(value), 0, ln=True)
        
        # Employee Details Section
        if employees:
            pdf.ln(10)
            section_header("Registered Professionals (Employees)")
            
            # Table Header
            pdf.set_fill_color(248, 249, 250)
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(50, 10, "Name", 1, 0, 'C', fill=True)
            pdf.cell(50, 10, "Designation", 1, 0, 'C', fill=True)
            pdf.cell(40, 10, "IA Reg No", 1, 0, 'C', fill=True)
            pdf.cell(50, 10, "Expiry Date", 1, 1, 'C', fill=True)
            
            pdf.set_font("helvetica", "", 9)
            for emp in employees:
                # Use multi_cell for name if it's too long, or just truncate for now to keep table clean
                name = emp.get('name_of_employee', '')[:25]
                designation = emp.get('designation', '')[:25]
                reg_no = emp.get('ia_registration_number', '')
                expiry = str(emp.get('date_of_registration_expiry', ''))
                
                pdf.cell(50, 10, name, 1, 0, 'L')
                pdf.cell(50, 10, designation, 1, 0, 'L')
                pdf.cell(40, 10, reg_no, 1, 0, 'C')
                pdf.cell(50, 10, expiry, 1, 1, 'C')

        # Return the PDF bytes
        return bytes(pdf.output())
