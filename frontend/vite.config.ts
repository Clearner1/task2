import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@ui': path.resolve(__dirname, 'src/components/ui'),
      '@foundation': path.resolve(__dirname, 'src/foundation'),
      '@domains': path.resolve(__dirname, 'src/domains'),
      '@pages': path.resolve(__dirname, 'src/pages'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
