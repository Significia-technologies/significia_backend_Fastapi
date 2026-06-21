"""Generate SUMMARY.json from all per-module test report files."""
import json
import os
from datetime import datetime

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "test_reports")
SUMMARY_FILE = os.path.join(REPORT_DIR, "SUMMARY.json")

MODULE_ORDER = [
    ("module_01_health.json", "Health"),
    ("module_02_auth.json", "Backend Auth"),
    ("module_03_tenant.json", "Tenant Resolution"),
    ("module_04_ia_auth.json", "IA Staff Auth Bridge"),
    ("module_05_client_auth.json", "Client Auth Bridge"),
    ("module_06_ia_master.json", "IA Master Profile"),
    ("module_07_client_crud.json", "Client CRUD"),
    ("module_08_risk_profile.json", "Risk Profile"),
    ("module_09_financial_analysis.json", "Financial Analysis"),
    ("module_10_advisory.json", "Advisory Notes"),
    ("module_11_sebi_audit.json", "SEBI Audit"),
    ("module_12_billing.json", "Billing"),
    ("module_13_e2e.json", "E2E Tenant Flow"),
]

modules = []
total_tests = total_passed = total_failed = total_skipped = 0

for filename, label in MODULE_ORDER:
    path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(path):
        print(f"  MISSING: {filename}")
        continue
    with open(path) as f:
        data = json.load(f)

    passed = data.get("passed", 0)
    failed = data.get("failed", 0)
    total = data.get("total", 0)
    skipped = 0

    response_times = [t.get("response_time_ms", 0) for t in data.get("tests", []) if t.get("response_time_ms")]
    avg_ms = round(sum(response_times) / len(response_times), 1) if response_times else 0
    max_ms = round(max(response_times), 1) if response_times else 0

    modules.append({
        "module": label,
        "file": filename,
        "run_at": data.get("run_at"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{round(passed/total*100)}%" if total else "N/A",
        "avg_response_ms": avg_ms,
        "max_response_ms": max_ms,
    })

    total_tests += total
    total_passed += passed
    total_failed += failed

summary = {
    "generated_at": datetime.utcnow().isoformat(),
    "overall": {
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "pass_rate": f"{round(total_passed/total_tests*100)}%" if total_tests else "N/A",
        "modules_run": len(modules),
    },
    "modules": modules,
}

with open(SUMMARY_FILE, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n{'='*60}")
print(f"  SIGNIFICIA TEST SUMMARY")
print(f"  Generated: {summary['generated_at']}")
print(f"{'='*60}")
print(f"  Total Tests : {total_tests}")
print(f"  Passed      : {total_passed}")
print(f"  Failed      : {total_failed}")
print(f"  Pass Rate   : {summary['overall']['pass_rate']}")
print(f"{'='*60}")
for m in modules:
    status = "PASS" if m["failed"] == 0 else "FAIL"
    print(f"  {status} {m['module']:30s} {m['passed']:3d}/{m['total']:3d}  avg {m['avg_response_ms']:7.1f}ms")
print(f"{'='*60}")
print(f"  Report: {SUMMARY_FILE}")
