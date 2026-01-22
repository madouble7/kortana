#!/usr/bin/env python3
"""
Memory and Learning Verification Script
Monitors Kor'tana's autonomous learning and memory formation
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Any

class LearningVerifier:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.start_time = datetime.now()
        self.initial_memory_count = 0
        self.belief_formation_count = 0

    def get_memories(self, memory_type: str = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get memories from the system"""
        try:
            params = {"limit": limit}
            if memory_type:
                params["type"] = memory_type

            response = requests.get(f"{self.base_url}/memories/", params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Error fetching memories: {e}")
            return []

    def analyze_core_beliefs(self) -> dict[str, Any]:
        """Analyze CORE_BELIEF memories for learning patterns"""
        beliefs = self.get_memories("CORE_BELIEF")

        analysis = {
            "total_beliefs": len(beliefs),
            "recent_beliefs": [],
            "learning_patterns": [],
            "confidence_scores": [],
            "knowledge_domains": set()
        }

        # Analyze recent beliefs (last hour)
        one_hour_ago = datetime.now() - timedelta(hours=1)

        for belief in beliefs:
            created_at = datetime.fromisoformat(belief.get('created_at', ''))
            content = belief.get('content', '')
            confidence = belief.get('confidence_score', 0.0)

            analysis['confidence_scores'].append(confidence)

            if created_at > one_hour_ago:
                analysis['recent_beliefs'].append(belief)

            # Identify knowledge domains
            if 'authentication' in content.lower():
                analysis['knowledge_domains'].add('Authentication')
            if 'database' in content.lower():
                analysis['knowledge_domains'].add('Database')
            if 'testing' in content.lower():
                analysis['knowledge_domains'].add('Testing')
            if 'planning' in content.lower():
                analysis['knowledge_domains'].add('Planning')
            if 'execution' in content.lower():
                analysis['knowledge_domains'].add('Execution')
            if 'pattern' in content.lower():
                analysis['knowledge_domains'].add('Pattern Recognition')

        return analysis

    def check_knowledge_graph(self) -> dict[str, Any]:
        """Check if knowledge graph is forming connections"""
        try:
            response = requests.get(f"{self.base_url}/memories/graph")
            if response.status_code == 200:
                graph_data = response.json()
                return {
                    "status": "available",
                    "nodes": len(graph_data.get('nodes', [])),
                    "edges": len(graph_data.get('edges', [])),
                    "connections": graph_data.get('edges', [])[:5]  # Sample connections
                }
            else:
                return {"status": "unavailable", "reason": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def verify_learning_progression(self) -> dict[str, Any]:
        """Verify that learning is progressing over time"""
        # Get memories from different time periods
        all_memories = self.get_memories()

        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)

        progression = {
            "total_memories": len(all_memories),
            "last_hour": 0,
            "last_day": 0,
            "learning_rate": 0.0,
            "memory_types": {}
        }

        for memory in all_memories:
            try:
                created_at = datetime.fromisoformat(memory.get('created_at', ''))
                memory_type = memory.get('memory_type', 'UNKNOWN')

                if created_at > last_hour:
                    progression['last_hour'] += 1
                if created_at > last_day:
                    progression['last_day'] += 1

                progression['memory_types'][memory_type] = progression['memory_types'].get(memory_type, 0) + 1

            except Exception:
                continue

        # Calculate learning rate (memories per hour)
        runtime_hours = (now - self.start_time).total_seconds() / 3600
        if runtime_hours > 0:
            progression['learning_rate'] = progression['last_hour'] / runtime_hours

        return progression

    def print_learning_analysis(self):
        """Print comprehensive learning analysis"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        runtime = datetime.now() - self.start_time

        print(f"\n{'='*60}")
        print(f"🧠 LEARNING & MEMORY ANALYSIS - {timestamp}")
        print(f"⏱️  Runtime: {runtime}")
        print(f"{'='*60}")

        # Analyze core beliefs
        belief_analysis = self.analyze_core_beliefs()

        print(f"\n📚 CORE BELIEF FORMATION:")
        print(f"   Total Beliefs: {belief_analysis['total_beliefs']}")
        print(f"   Recent Beliefs: {len(belief_analysis['recent_beliefs'])}")

        if belief_analysis['recent_beliefs']:
            print(f"\n🆕 RECENT LEARNING ACTIVITY:")
            for belief in belief_analysis['recent_beliefs']:
                content = belief.get('content', '')[:100] + "..."
                confidence = belief.get('confidence_score', 0.0)
                created = belief.get('created_at', 'Unknown')
                print(f"   💡 [{created}] Confidence: {confidence:.2f}")
                print(f"      {content}")
                print()

        # Knowledge domains
        if belief_analysis['knowledge_domains']:
            print(f"🎯 KNOWLEDGE DOMAINS ({len(belief_analysis['knowledge_domains'])}):")
            for domain in sorted(belief_analysis['knowledge_domains']):
                print(f"   🔍 {domain}")

        # Confidence analysis
        if belief_analysis['confidence_scores']:
            avg_confidence = sum(belief_analysis['confidence_scores']) / len(belief_analysis['confidence_scores'])
            print(f"\n📊 CONFIDENCE METRICS:")
            print(f"   Average Confidence: {avg_confidence:.2f}")
            print(f"   High Confidence (>0.8): {sum(1 for c in belief_analysis['confidence_scores'] if c > 0.8)}")
            print(f"   Low Confidence (<0.5): {sum(1 for c in belief_analysis['confidence_scores'] if c < 0.5)}")

        # Knowledge graph
        graph_info = self.check_knowledge_graph()
        print(f"\n🕸️  KNOWLEDGE GRAPH:")
        if graph_info['status'] == 'available':
            print(f"   Concepts: {graph_info['nodes']}")
            print(f"   Connections: {graph_info['edges']}")

            if graph_info['connections']:
                print("   Sample Connections:")
                for connection in graph_info['connections']:
                    print(f"      {connection.get('from', '?')} → {connection.get('to', '?')}")
        else:
            print(f"   Status: {graph_info['status']} ({graph_info.get('reason', 'Unknown')})")

        # Learning progression
        progression = self.verify_learning_progression()
        print(f"\n📈 LEARNING PROGRESSION:")
        print(f"   Total Memories: {progression['total_memories']}")
        print(f"   Last Hour: {progression['last_hour']}")
        print(f"   Last Day: {progression['last_day']}")
        print(f"   Learning Rate: {progression['learning_rate']:.2f} memories/hour")

        if progression['memory_types']:
            print("   Memory Types:")
            for mem_type, count in progression['memory_types'].items():
                print(f"      {mem_type}: {count}")

    def verify_autonomous_learning(self) -> bool:
        """Verify if autonomous learning is actually occurring"""
        print("🔍 VERIFYING AUTONOMOUS LEARNING...")

        # Check 1: Are new memories being formed?
        initial_memories = self.get_memories()
        self.initial_memory_count = len(initial_memories)

        print(f"📊 Baseline: {self.initial_memory_count} memories")

        # Wait and check again
        print("⏳ Waiting 30 seconds to observe memory formation...")
        time.sleep(30)

        current_memories = self.get_memories()
        current_count = len(current_memories)

        new_memories = current_count - self.initial_memory_count

        if new_memories > 0:
            print(f"✅ AUTONOMOUS LEARNING CONFIRMED: {new_memories} new memories formed!")
            return True
        else:
            print("❌ No new memories detected - may indicate lack of autonomous activity")
            return False

    def run_continuous_verification(self, interval: int = 30):
        """Run continuous learning verification"""
        print("🚀 Starting Learning & Memory Verification...")
        print(f"📡 Monitoring: {self.base_url}")
        print(f"⏰ Update interval: {interval} seconds")
        print("Press Ctrl+C to stop\n")

        # Initial verification
        learning_active = self.verify_autonomous_learning()

        try:
            while True:
                self.print_learning_analysis()

                # Check for signs of autonomous learning
                if learning_active:
                    print("\n💚 AUTONOMOUS LEARNING: ACTIVE")
                else:
                    print("\n🟡 AUTONOMOUS LEARNING: INACTIVE OR SLOW")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n🛑 Learning verification stopped by user")
            runtime = datetime.now() - self.start_time
            print(f"📊 Total monitoring time: {runtime}")

if __name__ == "__main__":
    verifier = LearningVerifier()

    # Check if server is running
    try:
        response = requests.get(f"{verifier.base_url}/health", timeout=5)
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("🔧 Please start the server first:")
        print("   python -m uvicorn src.kortana.main:app --reload --port 8000")
        exit(1)

    # Run verification
    verifier.run_continuous_verification()
