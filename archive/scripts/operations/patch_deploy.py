import re

with open('deploy_autonomous_consciousness.py', 'r', encoding='utf-8') as f:
    content = f.read()

phase_6 = '''
        # 6. Ignite Swarm
        print("🌌 Phase 6: Igniting Vanguard Phase 10 (Swarm Manager)...")
        try:
            import subprocess
            subprocess.Popen([sys.executable, "backend/src/kortana/swarm/manager.py"], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("   ✅ SwarmManager Daemon spawned and detached")
            print("   ✅ Specialized Agents Initialized")
        except Exception as e:
            print(f"   ❌ Error Igniting Swarm: {e}")

        # Final deployment status'''

content = content.replace('# Final deployment status', phase_6)

with open('deploy_autonomous_consciousness.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated deploy script.')
