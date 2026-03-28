# Icon Files for Kor'tana PWA

## Current Status
The `icon-192.svg` and `icon-512.svg` files are **placeholder SVG templates**.

## What You Need To Do

### Option 1: Use a Design Tool
1. Create a 512x512 PNG icon in:
   - Figma
   - Canva
   - Adobe Illustrator
   - Any graphic design tool

2. Export as PNG:
   - `icon-192.png` (192x192 pixels)
   - `icon-512.png` (512x512 pixels)

3. Place both files in `kortana/frontend/public/`

### Option 2: Use an AI Generator
1. Go to an AI image generator:
   - DALL-E 3 (ChatGPT Plus)
   - Midjourney
   - Stable Diffusion

2. Prompt example:
   ```
   "App icon for an AI constellation system called Kor'tana. 
   Modern, minimalist design with purple gradient background. 
   Letter 'K' in white with small star above it. 
   Rounded square shape. Professional tech aesthetic."
   ```

3. Generate, download, and resize to 192x192 and 512x512
4. Save as PNG files in `kortana/frontend/public/`

### Option 3: Use the SVG Placeholders (Temporary)
The current SVG files will work but won't look as professional. Browser support for SVG icons in PWAs is limited.

**Recommendation:** Replace with PNG files before deploying to production.

## Icon Requirements for PWA

- **Formats:** PNG (recommended), SVG (limited support)
- **Sizes:** 192x192 (required), 512x512 (required)
- **Purpose:** `any maskable` (works on both regular and adaptive icons)
- **Background:** Should look good on any color background
- **Content:** Should be recognizable at small sizes

## Testing Your Icons

After adding your PNG icons:
1. Build the frontend: `npm run build`
2. Deploy or preview: `npm run preview`
3. Open DevTools → Application → Manifest
4. Verify icons load correctly
5. Test "Add to Home Screen" on mobile

## Color Scheme (Current)
- **Primary:** `#6366f1` (Indigo)
- **Secondary:** `#8b5cf6` (Purple)
- **Accent:** `#fbbf24` (Amber/Gold)
- **Background:** `#0a0a0a` (Near Black)

Match your icon design to these colors for consistency.
