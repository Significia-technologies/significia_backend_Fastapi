"""
Audit Trail Report Generator
─────────────────────────────
Generates SEBI compliance audit trail exports in CSV and JSON formats.
Used by IA Masters to submit audit records to SEBI or external auditors.

Supported formats:
  - CSV: Standard tabular format suitable for Excel / data processing
  - JSON: Machine-readable structured format for regulatory systems
"""

import io
import csv
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


class AuditTrailReportGenerator:
    """
    Converts raw audit trail entries into exportable CSV or JSON format
    with proper headers, metadata, and SEBI-compliant structure.
    """

    # CSV column order and display headers
    CSV_COLUMNS = [
        ("created_at", "Timestamp"),
        ("user_name", "Changed By"),
        ("target_display_name", "Target Record"),
        ("record_type_label", "Record Type"),
        ("action_type", "Action"),
        ("field_changed", "Field Changed"),
        ("old_value", "Old Value"),
        ("new_value", "New Value"),
        ("change_reason_type", "Reason Type"),
        ("change_reason_text", "Reason Text"),
        ("entity_version", "Version"),
        ("user_ip", "IP Address"),
        # Technical IDs moved to the end as reference
        ("table_name", "Source Table"),
        ("record_id", "Record ID"),
        ("user_id", "User ID"),
        ("id", "Audit Entry ID"),
    ]

    @staticmethod
    def _get_record_type_label(table_name: str) -> str:
        """Helper to format table names into human-readable labels."""
        mapping = {
            "iamaster": "IA Master",
            "clients": "Client",
            "report_history": "Regulatory Report",
            "audit_trail": "System Audit",
            "employee_details": "Employee",
            "risk_assessments": "Risk Assessment",
            "risk_questionnaires": "Questionnaire",
            "financial_analysis_profiles": "Financial Profile",
            "asset_allocations": "Asset Allocation",
        }
        return mapping.get(table_name.lower(), table_name.capitalize())

    @staticmethod
    def _format_timestamp(ts_str: str) -> str:
        """Parse ISO timestamp and format for readable report."""
        if not ts_str:
            return ""
        try:
            # Handle ISO format (from Bridge)
            dt = datetime.fromisoformat(ts_str)
            return dt.strftime("%d-%m-%Y %H:%M:%S")
        except Exception:
            return ts_str

    @staticmethod
    def generate_csv(
        entries: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
        ia_data: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate a CSV audit trail report.
        
        Returns raw bytes of a UTF-8 encoded CSV file with BOM header 
        for Excel compatibility.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)

        # ── Metadata Header Rows ────────────────────────────────────
        writer.writerow(["SEBI AUDIT TRAIL REPORT"])
        writer.writerow([""])

        # IA Identity block
        if ia_data:
            writer.writerow(["Entity Name", ia_data.get("name_of_entity", "")])
            writer.writerow(["IA Name", ia_data.get("name_of_ia", "")])
            writer.writerow(["Registration No", ia_data.get("ia_registration_number", "")])
        
        # Blank space for manual regulation reference
        writer.writerow(["Regulation Reference", ""])  # IA fills manually
        writer.writerow([""])

        # Date range / filters
        if filters:
            from_date = filters.get("from_date") or "All Time"
            to_date = filters.get("to_date") or "Present"
            writer.writerow(["Report Period", f"{from_date} to {to_date}"])
            if filters.get("table_name"):
                writer.writerow(["Filtered Table", AuditTrailReportGenerator._get_record_type_label(filters["table_name"])])
            if filters.get("record_id"):
                writer.writerow(["Filtered Record ID", filters["record_id"]])
        else:
            writer.writerow(["Report Period", "All Time"])

        exported_at = datetime.now().strftime("%d-%m-%Y %H:%M:%S IST")
        writer.writerow(["Exported At", exported_at])
        writer.writerow(["Total Entries", str(len(entries))])
        writer.writerow([""])

        # ── Column Headers ──────────────────────────────────────────
        headers = [col[1] for col in AuditTrailReportGenerator.CSV_COLUMNS]
        writer.writerow(headers)

        # ── Data Rows ───────────────────────────────────────────────
        for entry in entries:
            # Inject helper labels
            entry["record_type_label"] = AuditTrailReportGenerator._get_record_type_label(entry.get("table_name", ""))
            if not entry.get("target_display_name"):
                entry["target_display_name"] = entry.get("record_id", "")
            
            # Format timestamp for CSV readability
            display_ts = AuditTrailReportGenerator._format_timestamp(entry.get("created_at", ""))

            row = []
            for col_key, _ in AuditTrailReportGenerator.CSV_COLUMNS:
                if col_key == "created_at":
                    row.append(display_ts)
                    continue
                    
                val = entry.get(col_key, "")
                if val is None:
                    val = ""
                row.append(str(val))
            writer.writerow(row)

        # UTF-8 BOM for Excel compatibility
        csv_content = output.getvalue()
        return ("\ufeff" + csv_content).encode("utf-8")

    @staticmethod
    def generate_json(
        entries: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
        ia_data: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate a JSON audit trail report.
        
        Returns structured JSON with metadata envelope and entries array.
        """
        exported_at = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+05:30")

        report = {
            "report_type": "SEBI_AUDIT_TRAIL",
            "report_title": "SEBI Audit Trail Report",
            "regulation_reference": "",  # IA fills manually
            "metadata": {
                "exported_at": exported_at,
                "total_entries": len(entries),
                "filters": filters or {},
            },
        }

        # IA Identity
        if ia_data:
            report["ia_identity"] = {
                "entity_name": ia_data.get("name_of_entity", ""),
                "ia_name": ia_data.get("name_of_ia", ""),
                "registration_number": ia_data.get("ia_registration_number", ""),
                "registered_email": ia_data.get("registered_email_id", ""),
                "registered_address": ia_data.get("registered_address", ""),
            }

        # Clean entries — ensure all values are JSON-serializable
        clean_entries = []
        for entry in entries:
            # Inject helper labels for readability
            entry["record_type_label"] = AuditTrailReportGenerator._get_record_type_label(entry.get("table_name", ""))
            if not entry.get("target_display_name"):
                entry["target_display_name"] = entry.get("record_id", "")

            clean = {}
            for key, val in entry.items():
                if isinstance(val, datetime):
                    clean[key] = val.isoformat()
                elif val is None:
                    clean[key] = None
                else:
                    clean[key] = val
            clean_entries.append(clean)

        report["entries"] = clean_entries

        return json.dumps(report, indent=2, ensure_ascii=False, default=str).encode("utf-8")

    @staticmethod
    def get_filename(format: str, from_date: Optional[str] = None, to_date: Optional[str] = None) -> str:
        """Generate a descriptive filename for the export."""
        date_suffix = datetime.now().strftime("%Y%m%d")
        
        if from_date and to_date:
            period = f"{from_date}_to_{to_date}"
        elif from_date:
            period = f"from_{from_date}"
        elif to_date:
            period = f"until_{to_date}"
        else:
            period = "all_time"

        return f"SEBI_Audit_Trail_{period}_{date_suffix}.{format}"
