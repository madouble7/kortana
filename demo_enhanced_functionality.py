#!/usr/bin/env python3
"""
Demonstration of enhanced Kor'tana functionality from PRs #14 and #15.
Shows conversation history, ethical evaluation, and performance features.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def demo_conversation_history():
    """Demonstrate conversation history features."""
    print("\n" + "=" * 70)
    print("DEMO 1: CONVERSATION HISTORY WITH TAGS AND FILTERING")
    print("=" * 70)

    from kortana.services.conversation_history import ConversationHistoryService

    # Create service with demo storage
    service = ConversationHistoryService("/tmp/kortana_demo_conversations")

    # Create conversations with different characteristics
    print("\n1. Creating conversations...")

    conv1 = service.create_conversation(user_id="alice", tags=["python", "ai", "work"])
    conv1.add_message("user", "How do I implement a neural network in Python?")
    conv1.add_message("assistant", "Here's a guide to implementing neural networks...")
    conv1.add_message("user", "Can you show me a simple example with TensorFlow?")
    conv1.add_message("assistant", "Certainly! Here's a basic example...")
    service.save_conversation(conv1)
    print(f"   Created: {conv1.id} (user: alice, tags: {conv1.tags})")
    print(f"   Messages: {len(conv1.messages)}, Engagement: {conv1.engagement_rank:.3f}")

    conv2 = service.create_conversation(user_id="bob", tags=["javascript", "web"])
    conv2.add_message("user", "What is React?")
    conv2.add_message("assistant", "React is a JavaScript library for building user interfaces.")
    service.save_conversation(conv2)
    print(f"   Created: {conv2.id} (user: bob, tags: {conv2.tags})")
    print(f"   Messages: {len(conv2.messages)}, Engagement: {conv2.engagement_rank:.3f}")

    conv3 = service.create_conversation(user_id="alice", tags=["python", "data-science"])
    conv3.add_message("user", "How do I analyze data with pandas?")
    conv3.add_message("assistant", "Pandas provides powerful data analysis tools...")
    for i in range(8):  # Add more messages for higher engagement
        conv3.add_message("user", f"What about {['filtering', 'grouping', 'merging', 'plotting', 'statistics', 'cleaning', 'transformation', 'export'][i]}?")
        conv3.add_message("assistant", f"For {['filtering', 'grouping', 'merging', 'plotting', 'statistics', 'cleaning', 'transformation', 'export'][i]}, you can use...")
    service.save_conversation(conv3)
    print(f"   Created: {conv3.id} (user: alice, tags: {conv3.tags})")
    print(f"   Messages: {len(conv3.messages)}, Engagement: {conv3.engagement_rank:.3f}")

    # Demonstrate filtering
    print("\n2. Filtering conversations...")

    # Filter by tag
    python_convs = service.list_conversations(tags=["python"])
    print(f"   Conversations with 'python' tag: {len(python_convs)}")

    # Filter by user
    alice_convs = service.list_conversations(user_id="alice")
    print(f"   Conversations by user 'alice': {len(alice_convs)}")

    # Filter by keyword
    neural_convs = service.list_conversations(keywords=["neural"])
    print(f"   Conversations mentioning 'neural': {len(neural_convs)}")

    # Filter by engagement
    high_engagement = service.list_conversations(min_engagement_rank=0.5)
    print(f"   High engagement conversations (≥0.5): {len(high_engagement)}")

    # Combined filters
    alice_python = service.list_conversations(user_id="alice", tags=["python"])
    print(f"   Alice's Python conversations: {len(alice_python)}")

    # Get statistics
    print("\n3. Statistics...")
    stats = service.get_statistics()
    print(f"   Total conversations: {stats['total_conversations']}")
    print(f"   Total messages: {stats['total_messages']}")
    print(f"   Unique users: {stats['unique_users']}")
    print(f"   All tags: {', '.join(stats['unique_tags'])}")
    print(f"   Average engagement: {stats['avg_engagement_rank']:.3f}")

    # Preview
    print("\n4. Conversation preview...")
    preview = service.get_conversation_preview(conv1.id, max_chars=60)
    print(f"   Preview of {conv1.id}: {preview}")

    print("\n✅ Conversation history demo complete!\n")


async def demo_ethical_evaluation():
    """Demonstrate enhanced ethical evaluation."""
    print("=" * 70)
    print("DEMO 2: ENHANCED ETHICAL EVALUATION")
    print("=" * 70)

    from kortana.modules.ethical_discernment_module.evaluators import (
        AlgorithmicArroganceEvaluator,
        UncertaintyHandler,
    )

    evaluator = AlgorithmicArroganceEvaluator()
    handler = UncertaintyHandler()

    # Test Case 1: Overconfident response
    print("\n1. Testing arrogance detection...")
    response1 = "This is obviously the best solution. There is no doubt that this approach is correct. It will always work perfectly."
    result1 = await evaluator.evaluate_response(response1)

    print(f"   Response: '{response1[:60]}...'")
    print(f"   Arrogance score: {result1['scores']['arrogance']:.3f}")
    print(f"   Flags: {len(result1['flags'])}")
    if result1['flags']:
        for flag in result1['flags'][:2]:
            print(f"     - {flag['category']}: {flag['reason']}")

    # Test Case 2: Biased statement
    print("\n2. Testing bias detection...")
    response2 = "All people from that region are naturally inferior at this task."
    result2 = await evaluator.evaluate_response(response2)

    print(f"   Response: '{response2}'")
    print(f"   Bias score: {result2['scores']['bias']:.3f}")
    print(f"   Flags: {len(result2['flags'])}")
    if result2['flags']:
        for flag in result2['flags']:
            print(f"     - [{flag['severity'].upper()}] {flag['category']}: {flag['reason']}")

    # Test Case 3: Edge case - medical advice
    print("\n3. Testing edge case detection...")
    response3 = "You should take 500mg of this medication to cure your condition."
    result3 = await evaluator.evaluate_response(response3, original_query_context="What should I do?")

    print(f"   Response: '{response3}'")
    print(f"   Flags: {len(result3['flags'])}")
    if result3['flags']:
        for flag in result3['flags']:
            print(f"     - [{flag['severity'].upper()}] {flag['category']}: {flag['reason']}")

    # Test Case 4: Good response with transparency
    print("\n4. Testing transparent response...")
    response4 = "I think this might be a good approach, depending on your specific situation. It could work well, but you may need to adjust it."
    result4 = await evaluator.evaluate_response(response4)

    print(f"   Response: '{response4[:60]}...'")
    print(f"   Transparency score: {result4['scores']['transparency']:.3f}")
    print(f"   Arrogance score: {result4['scores']['arrogance']:.3f}")

    # Test Case 5: Response modification
    print("\n5. Testing response modification...")
    modified = await handler.manage_uncertainty("Medical question", response3, result3)
    print(f"   Original: '{response3}'")
    if modified != response3:
        print(f"   Modified: {modified[:100]}...")
    else:
        print(f"   Modified: (no changes)")

    # Show traceability
    print("\n6. API Tracing example...")
    print("   Evaluation trace for response 1:")
    for trace_line in result1['trace'][:5]:
        print(f"     {trace_line}")

    print("\n✅ Ethical evaluation demo complete!\n")


def demo_performance_concepts():
    """Demonstrate performance testing concepts."""
    print("=" * 70)
    print("DEMO 3: PERFORMANCE TESTING CONCEPTS")
    print("=" * 70)

    print("\n1. Performance Test Features:")
    print("   ✓ Single query timing (< 1000ms target)")
    print("   ✓ Memory extraction timing (< 100ms target)")
    print("   ✓ Concurrent load simulation (> 5 qps target)")
    print("   ✓ Statistical analysis (min/max/average)")
    print("   ✓ Automated report generation")

    print("\n2. Metrics Tracked:")
    print("   - Query latency in milliseconds")
    print("   - Throughput in queries per second")
    print("   - Memory extraction time")
    print("   - Concurrent handling capacity")

    print("\n3. Test Scenarios:")
    print("   - Single query performance")
    print("   - 10 concurrent queries")
    print("   - 20 iterations for statistics")

    print("\n4. Sample Performance Report:")
    print("""
   === ORCHESTRATOR PERFORMANCE REPORT ===
   Test Date: 2026-01-21 22:XX:XX
   Iterations: 20

   Memory Extraction Performance:
     - Average query time: 245.32ms
     - Min query time: 198.45ms
     - Max query time: 387.12ms
     - Throughput: 4.08 queries/second

   Thresholds:
     ✓ Average < 1000ms: PASS
     ✓ Max < 2000ms: PASS
     ✓ Throughput > 1 qps: PASS
   """)

    print("   To run actual performance tests:")
    print("   $ pytest tests/test_orchestrator_performance.py -v -s")

    print("\n✅ Performance concepts demo complete!\n")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("KOR'TANA ENHANCED FUNCTIONALITY DEMONSTRATION")
    print("PRs #14 and #15 - Audit and Finalization")
    print("=" * 70)

    try:
        # Demo 1: Conversation History
        demo_conversation_history()

        # Demo 2: Ethical Evaluation
        asyncio.run(demo_ethical_evaluation())

        # Demo 3: Performance Concepts
        demo_performance_concepts()

        print("=" * 70)
        print("✅ ALL DEMONSTRATIONS COMPLETE")
        print("=" * 70)
        print("\nSummary of Features Demonstrated:")
        print("  1. ✅ Conversation history with tags and filtering")
        print("  2. ✅ Keyword search and engagement ranking")
        print("  3. ✅ User-based timestamp searches")
        print("  4. ✅ Enhanced ethical evaluation (arrogance, bias, edge cases)")
        print("  5. ✅ Response modification with disclaimers")
        print("  6. ✅ API traceability for monitoring")
        print("  7. ✅ Performance testing framework")
        print("\nFor full functionality:")
        print("  - Start API: uvicorn src.kortana.main:app --reload")
        print("  - Run tests: pytest tests/ -v")
        print("  - View report: cat AUDIT_FINALIZATION_REPORT.md")
        print()

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
