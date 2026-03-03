import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    }
  },
  build: {
    target: 'esnext',
    minify: 'esbuild',
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        manualChunks(id: string | string[]) {
          if (id.includes('@fontsource') || id.includes('primeicons')) {
            return 'fonts';
          }
          if (id.includes('node_modules')) {
            if (id.includes('primevue')) {
              return 'vendor-ui';
            }
            if (id.includes('vue')) {
              return 'vendor-vue';
            }
            return 'vendor-core';
          }
        }
      }
    }
  },
  esbuild: {
    drop: ['console', 'debugger'],
  }
  ,
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})