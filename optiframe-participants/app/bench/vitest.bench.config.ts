import { defineConfig } from 'vitest/config';
import base from '../vite.config.ts';

// Only the benchmark: `npm test` never picks it up (its include is src/ and tests/). The include is replaced,
// not merged (mergeConfig would concatenate it with the app suite).
export default defineConfig({ ...base, test: { ...base.test, include: ['bench/**/*.test.ts'] } });
