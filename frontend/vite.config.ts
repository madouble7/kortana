import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'
// import { VitePWA } from 'vite-plugin-pwa'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const vendorChunkPackages = ['react', 'react-dom', 'clsx', 'tailwind-merge']
  const apiTarget =
    process.env.VITE_API_TARGET ||
    env.VITE_API_TARGET ||
    process.env.VITE_API_URL ||
    env.VITE_API_URL ||
    'http://127.0.0.1:8000'

  return {
    plugins: [
      react(),
      // VitePWA temporarily disabled - causing module resolution issues during build
      // TODO: Re-enable after Vercel deployment is stable
      // VitePWA({...})
    ],
    server: {
      port: 5173,
      host: true,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path
        }
      }
    },
    preview: {
      port: 5173,
      host: true
    },
    build: {
      outDir: 'dist',
      sourcemap: mode === 'development',
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) {
              return undefined
            }

            return vendorChunkPackages.some((pkg) => id.includes(pkg))
              ? 'vendor'
              : undefined
          }
        }
      }
    }
  }
})
