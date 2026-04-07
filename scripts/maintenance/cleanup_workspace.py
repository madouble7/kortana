import os
import shutil

FILES_TO_DELETE = [
    "AUDIT_COMPLETION.md",
    "AUDIT_SUMMARY.md",
    "AUTOMATED_COMPLETE_HO_CLASSIFICATION.md",
    "AUTONOMY_CORE_INTEGRATION.md",
    "AUTONOMY_DATABASE_ENHANCEMENT_COMPLETE.md",
    "AUTONOMY_FINAL_REPORT.md",
    "AUTONOMY_FINAL_SUMMARY.md",
    "AUTONOMY_IMPLEMENTATION_COMPLETE.md",
    "AUTONOMY_IMPLEMENTATION_GUIDE.md",
    "AUTONOMY_IMPLEMENTATION_SUMMARY.md",
    "AUTONOMY_MASTER_INDEX.md",
    "AUTONOMY_ONE_PAGE_SUMMARY.txt",
    "AUTONOMY_ROADMAP_ARCHITECTURE.md",
    "AUTONOMY_STATUS_COMPLETE.md",
    "AUTONOMY_SYSTEM_INDEX.md",
    "AUTONOMY_VERIFICATION_CHECKLIST.md",
    "CONFIG_INTEGRATION_COMPLETE.md",
    "DEPLOYMENT_DOCS_INDEX.md",
    "DEPLOYMENT_PROGRESS.md",
    "DEPLOYMENT_READINESS_REPORT.md",
    "ENHANCEMENT_SUMMARY.md",
    "EXECUTIVE_SUMMARY_AUTONOMY.md",
    "FINAL_COMPLETION_SUMMARY.md",
    "GITHUB_AUTONOMY_AUDIT.md",
    "HO_CLASSIFICATION_SUMMARY.txt",
    "IGNITION_COMPLETE.md",
    "KOR_TANA_COMPLETE.md",
    "KOR_TANA_PHASE_2_100_COMPLETE.md",
    "KOR_TANA_PHASE_2_FINAL.md",
    "MASTER_COMPLETION_REFERENCE.md",
    "OPTIMIZATION_COMPLETE.md",
    "OPTIMIZATION_PLAN.md",
    "OPTIMIZATION_ROADMAP.md",
    "ORGANIZATION_VERIFIED.md",
    "PHASE1_COMPLETE.md",
    "PHASE1_INTEGRATION_COMPLETE.md",
    "PHASE2_AUDIT.md",
    "PHASE3_AUDIT.md",
    "PHASE3_SUMMARY.md",
    "PHASE_1_COMPLETION_ANNOUNCEMENT.md",
    "PHASE_1_COMPLETION_INDEX.md",
    "PHASE_1_DELIVERY_REPORT.md",
    "PHASE_2_COMPLETION_SUMMARY.md",
    "PHASE_2_DELIVERY_REPORT.md",
    "PHASE_2_FINAL_CHECKLIST.md",
    "PHASE_2_FINAL_STATUS.md",
    "PHASE_2_IMPLEMENTATION_GUIDE.md",
    "PHASE_2_MASTER_INDEX.md",
    "PRODUCTION_READINESS.md",
    "SECRETS_COMPLETE.md",
    "SETUP_VERIFICATION_CHECKLIST.md",
    "check_hop_errors.py",
    "reset_tasks.py",
]


def cleanup():
    count = 0
    for f in FILES_TO_DELETE:
        if os.path.exists(f):
            try:
                if os.path.isfile(f):
                    os.remove(f)
                else:
                    shutil.rmtree(f)
                print(f"Removed: {f}")
                count += 1
            except Exception as e:
                print(f"Error removing {f}: {e}")
    print(f"Cleanup finished: {count} items removed.")


if __name__ == "__main__":
    cleanup()
