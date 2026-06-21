"""
Run after all pytest modules complete to produce SUMMARY.json.
Usage: python generate_test_summary.py
"""
import json
import os
from datetime import datetime

REPORT_DIR = os.path.join(os.path.dirname(__file__), "test_reports")
SUMMARY_FILE = os.path.join(REPORT_DIR, "SUMMARY.json")

MODULE_FILES = [
    ("module_01_health.json",      "health"),
    ("module_02_auth.json",        "auth"),
    ("module_03_tenant.json",      "tenant"),
    ("module_04_ia_auth.json",     "ia_auth"),
    ("module_05_client_auth.json", "client_auth"),
    ("module_06_ia_master.json",   "ia_master"),
    ("module_07_client_crud.json", "client_crud"),
    ("module_08_risk_profile.json","risk_profile"),
    ("module_12_billing.json",     "billing"),
    ("module_13_e2e.json",         "e2e_tenant_flow"),
]


def load_report(filename):
    path = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def main():
    summary_modules = []
    total_passed = 0
    total_failed = 0
    slowest = {"id": None, "ms": 0}
    fastest = {"id": None, "ms": float("inf")}

    for filename, module in MODULE_FILES:
        data = load_report(filename)
        if not data:
            summary_modules.append({
                "module": module, "passed": 0, "failed": 0,
                "total": 0, "file": filename, "status": "NOT_RUN"
            })
            continue

        summary_modules.append({
            "module": module,
            "passed": data["passed"],
            "failed": data["failed"],
            "total": data["total"],
            "file": filename,
            "status": "OK" if data["failed"] == 0 else "FAILURES",
        })
        total_passed += data["passed"]
        total_failed += data["failed"]

        for test in data.get("tests", []):
            ms = test.get("response_time_ms", 0)
            tid = test.get("id", "?")
            if ms > slowest["ms"]:
                slowest = {"id": tid, "ms": ms}
            if ms > 0 and ms < fastest["ms"]:
                fastest = {"id": tid, "ms": ms}

    summary = {
        "run_at": datetime.utcnow().isoformat(),
        "total_passed": total_passed,
        "total_failed": total_failed,
        "modules": summary_modules,
        "slowest_test": slowest,
        "fastest_test": fastest if fastest["id"] else None,
    }

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*55}")
    print(f"  TEST SUMMARY")
    print(f"{'='*55}")
    print(f"  Total passed : {total_passed}")
    print(f"  Total failed : {total_failed}")
    print(f"{'='*55}")
    for m in summary_modules:
        icon = "OK" if m["status"] == "OK" else ("--" if m["status"] == "NOT_RUN" else "!!")
        print(f"  [{icon}] {m['module']:<20} {m['passed']}/{m['total']} passed")
    print(f"{'='*55}")
    if slowest["id"]:
        print(f"  Slowest : {slowest['id']} ({slowest['ms']:.0f}ms)")
    if fastest["id"]:
        print(f"  Fastest : {fastest['id']} ({fastest['ms']:.0f}ms)")
    print(f"\n  Full report: {SUMMARY_FILE}\n")


if __name__ == "__main__":
    main()
