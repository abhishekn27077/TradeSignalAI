import { defineConfig, createLogger } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Intercept Vite's internal logger to suppress backend proxy noise
const customLogger = createLogger()
const originalError = customLogger.error
customLogger.error = (msg, options) => {
  if (msg.includes('ECONNREFUSED')) return;
  originalError(msg, options)
}

export default defineConfig({
  customLogger,
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
        configure: (proxy) => {
          // Suppress ECONNREFUSED noise when backend is offline
          proxy.on('error', (err: NodeJS.ErrnoException) => {
            if (err.code === 'ECONNREFUSED') return; // Backend simply offline — not an error
            console.warn('[proxy /api error]', err.message);
          });
        },
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
        configure: (proxy) => {
          proxy.on('error', (err: NodeJS.ErrnoException) => {
            if (err.code === 'ECONNREFUSED') return;
            console.warn('[proxy /ws error]', err.message);
          });
        },
      },
    },
  },
})

