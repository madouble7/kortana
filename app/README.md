# kor'tana Public App

Next.js web application for KOR'TANA using OpenAI's responses API.

This app runs inside the main kortana repo and deploys independently to Vercel.

## Quick Start

From this directory:

```bash
npm install
npm run dev
```

Visit <http://localhost:3000>

## Deployment to Vercel

1. Ensure this directory is committed to git:

   ```bash
   git add app/
   git commit -m "feat: kor'tana public app"
   git push
   ```

2. Deploy to Vercel:

   ```bash
   cd app
   npm install -g vercel
   vercel --prod
   ```

3. Add environment variables in Vercel dashboard or via CLI:

   ```bash
   vercel env add OPENAI_API_KEY
   vercel env add OPENAI_MODEL
   vercel --prod
   ```

## Environment Variables

| Variable | Value | Source |
|----------|-------|--------|
| `OPENAI_API_KEY` | Your OpenAI key | From ../\.env |
| `OPENAI_MODEL` | `gpt-5.4` | Default |

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Runtime**: Node.js
- **Hosting**: Vercel (free tier)
- **AI**: OpenAI responses API
