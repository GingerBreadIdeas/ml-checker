import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  server: {
    watch: {
      usePolling: true,
      interval: 100, // Polling interval in ms (decrease for faster response)
    },
    host: true, // Listen on all addresses
    strictPort: true,
    port: parseInt(process.env.FRONTEND_PORT || '5173'),
    allowedHosts: process.env.FRONTEND_HOST ? [process.env.FRONTEND_HOST] : undefined,
    hmr: {
      clientPort: parseInt(process.env.FRONTEND_PORT || '5173'), // Force the HMR websocket to use this port
      overlay: true,     // Show error overlay
    },
    proxy: {
      '/api': {
        target: `http://localhost:${process.env.BACKEND_PORT || '8000'}`,
        changeOrigin: true,
      }
    }
  },
  // Define single entry point for SPA
  build: {
    sourcemap: true,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
      },
      output: {
        entryFileNames: `assets/[name].[hash].js`,
        chunkFileNames: `assets/[name].[hash].js`,
        assetFileNames: `assets/[name].[hash].[ext]`
      }
    }
  },
  // Optional: configure css
  css: {
    devSourcemap: true,
  }
})