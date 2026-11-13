import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// In development the SPA and the API share an origin through this proxy, exactly like
// the Vercel rewrite in production (see docs/adr/0004-autenticacion-y-sesion.md).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000',
        changeOrigin: false,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    coverage: { include: ['src/**/*.{ts,tsx}'], exclude: ['src/main.tsx', 'src/test/**'] },
  },
});
