import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
const path = (file: string) => fileURLToPath(new URL(file, import.meta.url));
export default defineConfig({
 root: path('./apps/demo'), base: './', plugins: [react()],
 resolve: { alias: { '@': path('./src') } },
 publicDir: path('./apps/demo/public'),
 server: { host: '127.0.0.1', port: 5173, strictPort: true, fs: { allow: [path('.')] } },
 build: { outDir: process.env.SIGHTLINE_BUILD_DIR || path('./dist'), emptyOutDir: false },
});
