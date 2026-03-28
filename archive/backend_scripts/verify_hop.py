#!/usr/bin/env python
"""Verify HumanOnlyProtocol classification engine operational status."""

from src.kortana.human_only_protocol import HumanOnlyProtocol, TaskClassification

hop = HumanOnlyProtocol()

tests = [
    ("fix_syntax_error", {"branch": "evolution/phase7"}, TaskClassification.AUTO),
    ("update_documentation", {"branch": "main"}, TaskClassification.AUTO),
    ("github_token_rotation", {}, TaskClassification.HO),
    ("unknown_advanced_task", {"branch": "main"}, TaskClassification.AUTO),
]

print("🔍 HumanOnlyProtocol Classification Testing\n")
results = []
for task, ctx, expected in tests:
    actual = hop.classify_task(task, ctx)
    results.append((task, actual, expected))
    status = "✅" if actual == expected else "❌"
    print(f"{status} {task}: {actual} (expected {expected})")

passed = sum(1 for _, actual, expected in results if actual == expected)
print(f"\nResult: {passed}/{len(tests)} tests PASSED")

if passed == len(tests):
    print("\n🚀 Status: READY FOR AUTONOMOUS EVOLUTION")
else:
    print("\n⚠️  Status: CLASSIFICATION ISSUES DETECTED")
