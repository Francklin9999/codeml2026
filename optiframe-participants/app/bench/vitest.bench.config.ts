import { defineConfig } from 'vitest/config';
import base from '../vite.config.ts';

// Only the benchmark: `npm test` never picks it up (its projects include src/ and tests/). The app config splits the
// suite into projects, and a project's include wins over a top-level one, so the projects are dropped here.
const { projects: _projects, ...test } = base.test ?? {};
export default defineConfig({ ...base, test: { ...test, include: ['bench/**/*.test.ts'] } });
