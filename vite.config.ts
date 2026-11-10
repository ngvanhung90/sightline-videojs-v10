import { execFileSync } from 'node:child_process';
import { fileURLToPath, URL } from 'node:url';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
const path = (file: string) => fileURLToPath(new URL(file, import.meta.url));
const head = execFileSync('git', ['rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
const dirty = execFileSync('git', ['status', '--porcelain'], { encoding: 'utf8' }).trim().length > 0;
const buildSha = head + (dirty ? '-dirty' : '');
export default defineConfig({
 define: { 'import.meta.env.VITE_BUILD_SHA': JSON.stringify(buildSha) },
 root: path('./apps/demo'), base: './', plugins: [react(), { name: 'sightline-source-receipt', generateBundle() { this.emitFile({ type: 'asset', fileName: 'build.json', source: JSON.stringify({ commit: head, dirty }) }); } }],
 resolve: { alias: { '@': path('./src') } },
 publicDir: path('./apps/demo/public'),
 server: { host: '127.0.0.1', port: 5174, strictPort: true, fs: { allow: [path('.')] } },
 build: { outDir: process.env.SIGHTLINE_BUILD_DIR || path('./dist'), emptyOutDir: false },
});
