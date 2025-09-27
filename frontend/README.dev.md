# Frontend development notes

This project provides a convenient `dev:all` script that starts the Vite dev server,
the local Node proxy, and (optionally) the local Python API. Use the npm scripts in
`package.json` from the `frontend/` folder.

Common commands (run from `frontend/`):

```powershell
npm run dev           # runs vite + proxy (via concurrently)
npm run dev:frontend  # vite only
npm run proxy         # starts the local proxy (node ../server/proxy.js)
npm run dev:all       # vite + proxy + local-api (uvicorn) — requires local-api-v2
```

Seed and secrets:

- A helper script `seed-kortana-vault.sh` exists at the repo root to bootstrap
  secrets into AWS Secrets Manager. It supports `--dry-run` and `--prefix` to
  control the secret name prefix:

```powershell
# Dry-run (no AWS calls)
bash ../seed-kortana-vault.sh --dry-run

# Live (will call AWS and require aws-cli configured)
bash ../seed-kortana-vault.sh --prefix kortana/ --region us-east-2
```

Notes:
- Ensure your `.env` is not committed; `.gitignore` already ignores it. Use
  `.env.example` as the redacted template.
- The frontend uses Vite dev proxy to forward /proxy to the local Node proxy.
