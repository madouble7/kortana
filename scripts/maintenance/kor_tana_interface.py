#!/usr/bin/env python3
"""
Kor'tana Interactive Interface
Communicate with the autonomous development system
"""

import requests
import json
import sys
from typing import Optional, Dict, Any

BASE_URL = "http://localhost:8000/api"

class KorTanaInterface:
    """Interface for communicating with Kor'tana"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check system health"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_always_on_status(self) -> Dict[str, Any]:
        """Get always-on monitoring status"""
        response = self.session.get(f"{self.base_url}/always-on/status")
        return response.json()
    
    def start_always_on(self) -> Dict[str, Any]:
        """Start always-on monitoring"""
        response = self.session.post(f"{self.base_url}/always-on/start")
        return response.json()
    
    def stop_always_on(self) -> Dict[str, Any]:
        """Stop always-on monitoring"""
        response = self.session.post(f"{self.base_url}/always-on/stop")
        return response.json()
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive dashboard"""
        response = self.session.get(f"{self.base_url}/always-on/dashboard")
        return response.json()
    
    def get_tasks(self, limit: int = 10) -> list:
        """Get recent tasks"""
        response = self.session.get(f"{self.base_url}/always-on/tasks?limit={limit}")
        return response.json()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get monitoring metrics"""
        response = self.session.get(f"{self.base_url}/always-on/metrics")
        return response.json()
    
    def force_check(self) -> Dict[str, Any]:
        """Force immediate monitoring cycle"""
        response = self.session.post(f"{self.base_url}/always-on/force-check")
        return response.json()
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get task status breakdown"""
        response = self.session.get(f"{self.base_url}/always-on/tasks/status")
        return response.json()
    
    def approve_task(self, task_id: str, approved: bool, notes: str = "") -> Dict[str, Any]:
        """Approve or reject a task"""
        response = self.session.post(
            f"{self.base_url}/always-on/tasks/{task_id}/approve",
            json={"approved": approved, "notes": notes}
        )
        return response.json()
    
    def retry_task(self, task_id: str) -> Dict[str, Any]:
        """Retry a failed task"""
        response = self.session.post(f"{self.base_url}/always-on/tasks/{task_id}/retry")
        return response.json()
    
    def get_actions(self, limit: int = 20) -> list:
        """Get recent actions"""
        response = self.session.get(f"{self.base_url}/always-on/actions?limit={limit}")
        return response.json()


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_section(text: str):
    """Print section title"""
    print(f"\n▶ {text}")
    print(f"{'─'*60}")


def print_json(data: Any, indent: int = 2):
    """Pretty print JSON"""
    print(json.dumps(data, indent=indent, default=str))


def interactive_menu():
    """Interactive menu for Kor'tana interface"""
    kor = KorTanaInterface()
    
    print_header("🤖 KOR'TANA AUTONOMOUS SYSTEM INTERFACE")
    print("Connected to: http://localhost:8000/api\n")
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("""
1. System Status & Health
2. Always-On Monitoring
3. Task Management
4. Dashboard & Metrics
5. Autonomous Development Cycle
6. Task Actions
0. Exit
        """)
        
        choice = input("Select option (0-6): ").strip()
        
        try:
            if choice == "0":
                print("\n👋 Disconnecting from Kor'tana...\n")
                break
            
            elif choice == "1":
                print_header("SYSTEM STATUS")
                data = kor.health_check()
                print("🏥 Health Check:")
                print_json(data)
            
            elif choice == "2":
                print_header("ALWAYS-ON MONITORING")
                print("""
1. Check Status
2. Start Monitoring
3. Stop Monitoring
0. Back
                """)
                sub = input("Select (0-3): ").strip()
                
                if sub == "1":
                    data = kor.get_always_on_status()
                    print("\n📊 Monitor Status:")
                    print_json(data)
                elif sub == "2":
                    print("\n🚀 Starting always-on monitoring...")
                    data = kor.start_always_on()
                    print_json(data)
                elif sub == "3":
                    print("\n⏹️ Stopping always-on monitoring...")
                    data = kor.stop_always_on()
                    print_json(data)
            
            elif choice == "3":
                print_header("TASK MANAGEMENT")
                print("""
1. View Recent Tasks
2. Get Task Status Summary
3. Approve/Reject Task
4. Retry Failed Task
0. Back
                """)
                sub = input("Select (0-4): ").strip()
                
                if sub == "1":
                    limit = input("Number of tasks to show (default 10): ").strip() or "10"
                    data = kor.get_tasks(int(limit))
                    print("\n📋 Recent Tasks:")
                    print_json(data)
                
                elif sub == "2":
                    data = kor.get_task_status()
                    print("\n📊 Task Status Summary:")
                    print_json(data)
                
                elif sub == "3":
                    task_id = input("Task ID: ").strip()
                    approved = input("Approve? (y/n): ").strip().lower() == "y"
                    notes = input("Notes (optional): ").strip()
                    data = kor.approve_task(task_id, approved, notes)
                    print("\n✅ Result:")
                    print_json(data)
                
                elif sub == "4":
                    task_id = input("Task ID: ").strip()
                    data = kor.retry_task(task_id)
                    print("\n🔄 Result:")
                    print_json(data)
            
            elif choice == "4":
                print_header("DASHBOARD & METRICS")
                print("""
1. Full Dashboard
2. Metrics Only
3. Recent Actions
0. Back
                """)
                sub = input("Select (0-3): ").strip()
                
                if sub == "1":
                    data = kor.get_dashboard()
                    print("\n📈 Full Dashboard:")
                    print_json(data)
                elif sub == "2":
                    data = kor.get_metrics()
                    print("\n📊 Metrics:")
                    print_json(data)
                elif sub == "3":
                    limit = input("Number of actions (default 20): ").strip() or "20"
                    data = kor.get_actions(int(limit))
                    print("\n📝 Recent Actions:")
                    print_json(data)
            
            elif choice == "5":
                print_header("AUTONOMOUS DEVELOPMENT CYCLE")
                print("\n🤖 Forcing immediate monitoring cycle...\n")
                data = kor.force_check()
                print_json(data)
            
            elif choice == "6":
                print_header("TASK ACTIONS")
                print("""
1. Force Monitoring Check
2. View Dashboard
3. Export Task Report
0. Back
                """)
                sub = input("Select (0-3): ").strip()
                
                if sub == "1":
                    print("\n⚡ Forcing check...")
                    data = kor.force_check()
                    print_json(data)
                elif sub == "2":
                    data = kor.get_dashboard()
                    print("\n📊 Dashboard:")
                    print_json(data)
                elif sub == "3":
                    tasks = kor.get_tasks(50)
                    filename = "kor_tana_task_report.json"
                    with open(filename, "w") as f:
                        json.dump(tasks, f, indent=2, default=str)
                    print(f"\n📄 Report exported to: {filename}")
        
        except requests.exceptions.ConnectionError:
            print("\n❌ ERROR: Cannot connect to Kor'tana at http://localhost:8000")
            print("   Make sure the server is running: python -m uvicorn src.kortana.main:app --port 8000")
        except requests.exceptions.RequestException as e:
            print(f"\n❌ ERROR: {str(e)}")
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")


def quick_status():
    """Quick status check without interactive menu"""
    try:
        kor = KorTanaInterface()
        
        print_header("🤖 KOR'TANA QUICK STATUS")
        
        print_section("System Health")
        health = kor.health_check()
        status = health.get("status", "unknown")
        print(f"Status: {status}")
        
        print_section("Always-On Monitor")
        monitor = kor.get_always_on_status()
        print(f"Running: {monitor.get('is_running', False)}")
        print(f"Check Interval: {monitor.get('check_interval', 'N/A')}s")
        
        print_section("Task Summary")
        tasks = kor.get_task_status()
        total = tasks.get('total_tasks', 0)
        by_status = tasks.get('by_status', {})
        print(f"Total Tasks: {total}")
        print(f"  Pending: {by_status.get('pending', 0)}")
        print(f"  Completed: {by_status.get('completed', 0)}")
        print(f"  Failed: {by_status.get('failed', 0)}")
        
        print_section("Metrics")
        metrics = kor.get_metrics()
        stats = metrics.get('tasks', {})
        print(f"Processed: {stats.get('tasks_processed', 0)}")
        print(f"Completed: {stats.get('tasks_completed', 0)}")
        print(f"Failed: {stats.get('tasks_failed', 0)}")
        
        print("\n✅ Kor'tana is responsive and operational!\n")
        
    except Exception as e:
        print(f"\n❌ Error connecting to Kor'tana: {str(e)}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_status()
    else:
        interactive_menu()
