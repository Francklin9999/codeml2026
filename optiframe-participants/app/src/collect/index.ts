/// <reference types="vite/client" />
import './styles.css';
import pkg from '../../package.json';
import { chooseOriginalFile, decodeFile } from '../capture';
import { saveBlob } from '../export/download';
import { registerServiceWorker } from '../swRegister';
import { checkSheet, measure } from './measureAdapter';
import { openStore } from './storage';
import { mountCollect, type Deps } from './ui';

const THUMB_PX = 160;

/** 160 px JPEG thumbnail; the original file is never touched. */
async function makeThumb(file: File): Promise<ArrayBuffer | undefined> {
  let bmp: ImageBitmap;
  try { bmp = await createImageBitmap(file, { resizeWidth: THUMB_PX, resizeQuality: 'low' }); }
  catch { bmp = await createImageBitmap(file); }
  const w = Math.min(THUMB_PX, bmp.width), h = Math.max(1, Math.round((bmp.height * w) / bmp.width));
  const c = document.createElement('canvas');
  c.width = w;
  c.height = h;
  c.getContext('2d')?.drawImage(bmp, 0, 0, w, h);
  bmp.close();
  const blob = await new Promise<Blob | null>((ok) => c.toBlob(ok, 'image/jpeg', 0.7));
  return blob ? blob.arrayBuffer() : undefined;
}

async function save(data: Uint8Array, fileName: string): Promise<'shared' | 'saved' | 'cancelled'> {
  const file = new File([data as BlobPart], fileName, { type: 'application/zip' });
  if (navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: fileName });
      return 'shared';
    } catch (e) {
      if ((e as DOMException)?.name === 'AbortError') return 'cancelled';
      // any other failure: fall back to a download
    }
  }
  saveBlob(data as BlobPart, fileName, 'application/zip');
  return 'saved';
}

async function main() {
  const root = document.getElementById('app')!;
  let store;
  try {
    store = await openStore();
  } catch (e) {
    root.textContent = e instanceof Error ? e.message : 'Stockage indisponible.';
    return;
  }
  const deps: Deps = {
    store,
    chooseFile: (camera) => chooseOriginalFile(camera),
    decode: (file) => decodeFile(file, 'camera'),
    measure,
    checkSheet,
    makeThumb,
    save,
    confirm: (m) => window.confirm(m),
    storage: navigator.storage,
    local: window.localStorage,
    url: { create: (b) => URL.createObjectURL(b), revoke: (u) => URL.revokeObjectURL(u) },
    userAgent: navigator.userAgent,
    appVersion: pkg.version,
    now: () => new Date(),
  };
  mountCollect(root, deps);
}

void main();
if (import.meta.env.PROD) void registerServiceWorker();
