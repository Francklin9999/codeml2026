import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { defaultClientConditions } from 'vite';
import { defineConfig } from 'vitest/config';

// Every top-level page is an entry: index.html (the app), eval.html (brief 14), collect.html (brief 17).
// lightbox.html lives in public/ and is copied as is.
const input: Record<string, string> = {};
for (const f of readdirSync(import.meta.dirname).filter((n) => n.endsWith('.html')).sort()) {
  input[f === 'index.html' ? 'main' : f.replace(/\.html$/, '')] = resolve(import.meta.dirname, f);
}

export default defineConfig({
  base: './', // works from a sub-path such as https://user.github.io/repo/
  // The ort WASM is self-hosted in public/vendor/ort: this condition stops Vite bundling a second 14 MB copy.
  resolve: { conditions: [...defaultClientConditions, 'onnxruntime-web-use-extern-wasm'] },
  build: { target: 'es2022', rollupOptions: { input } },
  worker: { format: 'es' },
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts', 'tests/**/*.test.ts'],
    setupFiles: ['src/test/setup.ts'],
  },
});
