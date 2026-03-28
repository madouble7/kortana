# Experimental: Autonomy Loop

This directory contains the abstracted Autonomy Loop application exported from Google AI Studio.

**Role in the Kor'tana ecosystem:**
Currently, this is a **quarantined experimental surface**.
It is *not* wired into the canonical deployment pipeline (`docker-compose.yml`, `Dockerfile`, root `package.json`).
Do not use it as a candidate replacement surface until all logic is merged safely and passes root CI expectations.

**Current Validation Status:**

- `npm run build` ✅ Passes (Vite + tsc)
- `npm test` ✅ Passes (Jest is scoped to the real service suite and runs through Node ESM)

**Operating Considerations:**

- Requires Cloud Run specific paths (`/tmp/` routing for write operations).
- Has relaxed threshold states (`Complexity: 20`, `Safety Check: 2`).
- Build still emits chunk-size/code-splitting warnings; treat those as optimization work, not correctness failures.

To manually investigate this environment:

```bash
npm --prefix autonomy_loop run dev
```
