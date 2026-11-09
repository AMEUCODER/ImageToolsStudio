import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Where /api requests go while developing or previewing. In Docker, nginx does this instead.
const api = process.env.VITE_API_TARGET ?? 'http://127.0.0.1:8000'
const proxy = { '/api': { target: api, changeOrigin: true } }

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.svg', 'icons/apple-touch-icon.png'],
      manifest: {
        name: 'Image Tools Studio',
        short_name: 'Image Studio',
        description: 'Edit photos with AI-powered tools: blur, enhance, crop and more.',
        theme_color: '#1a1a1c',
        background_color: '#1a1a1c',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icons/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icons/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icons/maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^\/api\//],      // the API is never served from the cache
        globPatterns: ['**/*.{js,css,html,svg,png,woff2}'],
      },
    }),
  ],
  server: { port: 5173, proxy },
  preview: { port: 4173, proxy },
})
