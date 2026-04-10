import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const appRoot = path.dirname(__filename);

export default defineConfig({
  plugins: [react()],
  root: appRoot,
  build: {
    outDir: path.resolve(appRoot, 'dist'),
    emptyOutDir: true,
  },
  server: {
    host: '127.0.0.1',
    port: 4173,
    strictPort: true,
  },
});
