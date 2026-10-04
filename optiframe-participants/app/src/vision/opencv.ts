import type * as OpenCv from '@techstark/opencv-js';
import { OptiError } from '../contracts';

// The installed build (@techstark/opencv-js 5.0.0-release.1, OpenCV 5.0.0, Apache-2.0) exposes ArUco at
// runtime but not in its .d.ts, and exposes no cornerSubPix. Only what we call is declared here.
interface ArucoApi {
  DICT_4X4_50: number;
  getPredefinedDictionary(id: number): { delete(): void };
  aruco_DetectorParameters: new () => { delete(): void };
  aruco_RefineParameters: new (minRepDistance: number, errorCorrectionRate: number, checkAllOrders: boolean) => { delete(): void };
  aruco_ArucoDetector: new (dict: unknown, params: unknown, refine: unknown) => {
    detectMarkers(img: OpenCv.Mat, corners: OpenCv.MatVector, ids: OpenCv.Mat, rejected: OpenCv.MatVector): void;
    delete(): void;
  };
  generateImageMarker(dict: unknown, id: number, sidePixels: number, img: OpenCv.Mat, borderBits: number): void;
}
export type Cv = typeof OpenCv & ArucoApi;

const VENDOR_PATH = 'vendor/opencv/opencv.js';
let url: string | undefined;
let pending: Promise<Cv> | undefined;

/** Override where opencv.js is fetched from (browser only). Call before the first loadOpenCv(). */
export function setOpenCvUrl(u: string): void {
  url = u;
  pending = undefined;
}

function defaultUrl(): string {
  const g = globalThis as { document?: { baseURI: string }; location?: { href: string } };
  const base = (import.meta as { env?: { BASE_URL?: string } }).env?.BASE_URL ?? './';
  // A bundled worker lives one folder below the app root (assets/), the page is at the root.
  const origin = g.document ? g.document.baseURI : new URL('../', g.location?.href ?? 'http://localhost/').href;
  return new URL(base + VENDOR_PATH, origin).href;
}

/** Runs the UMD build text without a script tag, so it works in the page and in a module Web Worker. */
export function evalOpenCv(source: string): unknown {
  const mod: { exports: unknown } = { exports: {} };
  new Function('module', 'exports', source)(mod, mod.exports);
  return mod.exports;
}

async function whenReady(raw: unknown): Promise<Cv> {
  let cv = raw as Record<string, unknown> & { then?: unknown };
  if (typeof cv.then === 'function') cv = (await cv) as typeof cv; // the build is a thenable
  if (!cv.Mat) {
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('OpenCV runtime did not initialise')), 60_000);
      (cv as { onRuntimeInitialized?: () => void }).onRuntimeInitialized = () => { clearTimeout(timer); resolve(); };
    });
  }
  return cv as unknown as Cv;
}

async function load(): Promise<Cv> {
  const g = globalThis as { process?: { versions?: { node?: string } }; document?: unknown };
  if (g.process?.versions?.node && !g.document) {
    // Node (Vitest, tools): load from node_modules. The module name is kept out of the bundler's sight.
    const name = 'node:module';
    const { createRequire } = (await import(/* @vite-ignore */ name)) as typeof import('node:module');
    return whenReady(createRequire(import.meta.url)('@techstark/opencv-js'));
  }
  const res = await fetch(url ?? defaultUrl());
  if (!res.ok) throw new Error('opencv.js HTTP ' + res.status);
  return whenReady(evalOpenCv(await res.text()));
}

/** Loads OpenCV.js once; every caller shares the same promise. */
export function loadOpenCv(): Promise<Cv> {
  pending ??= load().catch((e: unknown) => {
    pending = undefined; // allow a retry after a network failure
    throw new OptiError('LOAD_FAILED', 'opencv.js: ' + (e instanceof Error ? e.message : String(e)));
  });
  return pending;
}
