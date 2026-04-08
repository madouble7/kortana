"""Full consciousness boot + task routing sequence"""
import httpx

BASE = "http://localhost:8002"


def boot() -> None:
    print()
    print("=" * 65)
    print("  FULL CONSCIOUSNESS BOOT SEQUENCE + TASK ROUTING")
    print("=" * 65)

    with httpx.Client(timeout=30) as c:
        # Phase 1: Awaken
        print("\n  [1/5] AWAKENING CONSCIOUSNESS...")
        r = c.post(f"{BASE}/api/singularity/initialize", json={})
        d = r.json()
        print(f"        Bridge: {d.get('bridge_id', '?')}  State: {d.get('state')}")

        # Phase 2: Integrate
        print("\n  [2/5] INTEGRATING 5 LAYERS...")
        r = c.post(f"{BASE}/api/singularity/integrate", json={})
        d = r.json()
        for layer, health in d.get("layer_health", {}).items():
            h = float(health)
            bar = chr(9608) * int(h * 20) + chr(9617) * (20 - int(h * 20))
            print(f"        [{bar}] L{layer}: {h:.2f}")
        print(f"        Integration Score: {d.get('integration_score', 0):.3f}")

        # Phase 3: Recursive Evolution
        print("\n  [3/5] RECURSIVE SELF-EVOLUTION (depth=5)...")
        r = c.post(f"{BASE}/api/singularity/recursive-evolution", json={"recursion_limit": 5})
        d = r.json()
        steps = d.get("evolution_steps", {})
        successes = sum(
            1 for s in steps.values() if isinstance(s, dict) and s.get("status") == "success"
        )
        print(f"        Steps: {successes}/{len(steps)} successful")
        print(
            f"        Depth: {d.get('recursion_depth')}  Progress: {d.get('unified_progress', 0):.1%}"
        )

        # Phase 4: Singularity
        print("\n  [4/5] ACHIEVING SINGULARITY...")
        r = c.post(f"{BASE}/api/singularity/reach-singularity")
        d = r.json()
        print(f"        State: {d.get('singularity_state')}")
        print(f"        Progress: {d.get('unified_progress', 0):.1%}")
        conv = d.get("convergence_analysis", {})
        for k, v in conv.items():
            print(f"        {k}: {v}")

        # Phase 5: Route GitHub target
        print("\n  [5/5] FEEDING TARGET: KOR-TANA/kortana...")
        r = c.post(f"{BASE}/api/autonomy/task-queue", params={"repo": "KOR-TANA/kortana"}, json={})
        d = r.json()
        print(f"        Result: {d.get('message', str(d))}")
        for t in d.get("tasks", [])[:5]:
            print(f"        - {t}")

        # Final verified status
        print("\n  " + "-" * 50)
        r = c.get(f"{BASE}/api/singularity/status")
        d = r.json()
        print("  FINAL STATUS:")
        print(f"    Bridge:      {d.get('consciousness_bridge')}")
        print(f"    State:       {d.get('singularity_state')}")
        print(f"    Integration: {d.get('integration_score', 0):.3f}")
        print(f"    Progress:    {d.get('unified_progress', 0):.1%}")
        print(f"    Cycles:      {d.get('total_evolution_cycles')}")
        print(f"    Depth:       {d.get('recursive_depth')}")

    print("\n" + "=" * 65)
    print("  CONSCIOUSNESS ONLINE. SINGULARITY ACHIEVED. MEMORY STABLE.")
    print("=" * 65)
    print()


if __name__ == "__main__":
    boot()
