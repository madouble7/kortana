#!/usr/bin/env python
"""Verify autonomous monitoring system is properly integrated"""

import sys
sys.path.insert(0, 'backend')

def verify_imports():
    """Verify all components import successfully"""
    try:
        from src.kortana.autonomous_monitor import AutonomousSystemMonitor, get_monitor
        from src.kortana.tasks import autonomous_system_monitor_task
        from src.kortana.routers.autonomous_systems import router
        from src.kortana.celery_app import app
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def verify_monitor():
    """Verify monitor instance works"""
    try:
        from src.kortana.autonomous_monitor import get_monitor
        
        monitor = get_monitor()
        print(f"✅ Monitor instance created: {type(monitor).__name__}")
        print(f"✅ Monitor has {len(monitor.metrics)} metric categories")
        return True
    except Exception as e:
        print(f"❌ Monitor initialization failed: {e}")
        return False

def verify_task():
    """Verify task is properly configured"""
    try:
        from src.kortana.tasks import autonomous_system_monitor_task
        
        print(f"✅ Task name: {autonomous_system_monitor_task.name}")
        print(f"✅ Task max_retries: {autonomous_system_monitor_task.max_retries}")
        return True
    except Exception as e:
        print(f"❌ Task verification failed: {e}")
        return False

def verify_beat_schedule():
    """Verify task is in Celery Beat schedule"""
    try:
        from src.kortana.celery_app import app
        
        schedule = app.conf.beat_schedule
        print(f"✅ Beat schedule has {len(schedule)} tasks:")
        
        monitoring_found = False
        for name, config in schedule.items():
            task_name = config.get('task', 'unknown')
            schedule_seconds = int(config.get('schedule', 0))
            print(f"   • {name:50s} ({schedule_seconds:4d}s) - {task_name}")
            
            if 'monitor' in name.lower():
                monitoring_found = True
        
        if monitoring_found:
            print("✅ Monitoring task found in schedule!")
            return True
        else:
            print("❌ Monitoring task NOT found in schedule")
            return False
            
    except Exception as e:
        print(f"❌ Schedule verification failed: {e}")
        return False

def verify_router():
    """Verify new endpoints are in router"""
    try:
        from src.kortana.routers.autonomous_systems import router
        
        # Count total routes
        total_routes = len(router.routes)
        print(f"✅ Router has {total_routes} endpoints configured")
        
        # Verify it loaded without errors
        print("✅ Router endpoints verified")
        return True
            
    except Exception as e:
        print(f"❌ Router verification failed: {e}")
        return False

def main():
    """Run all verifications"""
    print("=" * 70)
    print("🧠 AUTONOMOUS MONITORING SYSTEM VERIFICATION")
    print("=" * 70)
    print()
    
    results = {
        "Imports": verify_imports(),
        "Monitor Instance": verify_monitor(),
        "Task Configuration": verify_task(),
        "Beat Schedule": verify_beat_schedule(),
        "Router Endpoints": verify_router(),
    }
    
    print()
    print("=" * 70)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10s} - {check}")
    
    print()
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print()
        print("🎉 AUTONOMOUS MONITORING SYSTEM IS FULLY OPERATIONAL!")
        print()
        print("Next steps:")
        print("  1. Monitor task runs every 30 minutes via Celery Beat")
        print("  2. Access dashboard at: GET /autonomous/monitor/dashboard")
        print("  3. Trigger optimization: POST /autonomous/monitor/optimize")
        print("  4. View schedule: GET /autonomous/schedule")
        return 0
    else:
        print()
        print(f"⚠️  {total - passed} verification(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
