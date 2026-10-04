// IndexedDB store. Two object stores so listing never loads image bytes:
//   meta  (keyPath name): Meta + thumbnail
//   bytes (out-of-line key = name): the original file as an ArrayBuffer, untouched.
import type { Meta } from './manifest';

export interface StoredMeta extends Meta { thumb?: ArrayBuffer }

export class StorageError extends Error {
  constructor(public kind: 'quota' | 'exists' | 'unavailable' | 'other', message: string) { super(message); }
}

export interface PhotoStore {
  list(): Promise<StoredMeta[]>;
  getBytes(name: string): Promise<ArrayBuffer | undefined>;
  /** Fails with kind 'exists' unless `replace`. Names are compared case-insensitively (Windows). */
  put(meta: StoredMeta, bytes: ArrayBuffer, replace?: boolean): Promise<void>;
  delete(name: string): Promise<void>;
  markExported(names: string[], at: string): Promise<void>;
  /** Removes only photos marked exported; returns how many. */
  deleteExported(): Promise<number>;
}

const DB_NAME = 'optiframe-collect';
const META = 'meta';
const BYTES = 'bytes';

export const FRENCH_QUOTA = "Le téléphone n'a plus de place pour stocker les photos. Exportez puis videz les photos exportées.";

function toStorageError(e: unknown): StorageError {
  const name = (e as { name?: string } | null)?.name;
  if (name === 'QuotaExceededError') return new StorageError('quota', FRENCH_QUOTA);
  return new StorageError('other', "Le stockage des photos a échoué. Rechargez la page et réessayez.");
}

const req = <T>(r: IDBRequest<T>): Promise<T> =>
  new Promise((ok, ko) => {
    r.onsuccess = () => ok(r.result);
    r.onerror = () => ko(r.error);
  });

const done = (tx: IDBTransaction): Promise<void> =>
  new Promise((ok, ko) => {
    tx.oncomplete = () => ok();
    tx.onerror = () => ko(tx.error);
    tx.onabort = () => ko(tx.error ?? { name: 'AbortError' });
  });

export async function openStore(factory: IDBFactory | undefined = globalThis.indexedDB): Promise<PhotoStore> {
  if (!factory) throw new StorageError('unavailable', "Le stockage du navigateur n'est pas disponible (navigation privée ?).");
  const db = await new Promise<IDBDatabase>((ok, ko) => {
    const o = factory.open(DB_NAME, 1);
    o.onupgradeneeded = () => {
      o.result.createObjectStore(META, { keyPath: 'name' });
      o.result.createObjectStore(BYTES);
    };
    o.onsuccess = () => ok(o.result);
    o.onerror = () => ko(new StorageError('unavailable', "Le stockage du navigateur n'est pas disponible (navigation privée ?)."));
    o.onblocked = () => ko(new StorageError('unavailable', 'Le stockage est bloqué par un autre onglet.'));
  });

  const run = async <T>(stores: string[], mode: IDBTransactionMode, fn: (tx: IDBTransaction) => Promise<T>): Promise<T> => {
    try {
      const tx = db.transaction(stores, mode);
      const finished = done(tx);
      finished.catch(() => {}); // the awaited copy below reports it
      const out = await fn(tx);
      await finished;
      return out;
    } catch (e) {
      throw e instanceof StorageError ? e : toStorageError(e);
    }
  };

  const store: PhotoStore = {
    list: () => run([META], 'readonly', (tx) => req(tx.objectStore(META).getAll() as IDBRequest<StoredMeta[]>)),
    getBytes: (name) => run([BYTES], 'readonly', (tx) => req(tx.objectStore(BYTES).get(name) as IDBRequest<ArrayBuffer | undefined>)),
    put: (meta, bytes, replace = false) =>
      run([META, BYTES], 'readwrite', async (tx) => {
        if (!replace) {
          const all = (await req(tx.objectStore(META).getAllKeys())) as string[];
          const low = meta.name.toLowerCase();
          if (all.some((k) => String(k).toLowerCase() === low)) throw new StorageError('exists', `Le fichier ${meta.name} existe déjà.`);
        }
        tx.objectStore(META).put(meta);
        tx.objectStore(BYTES).put(bytes, meta.name);
      }),
    delete: (name) =>
      run([META, BYTES], 'readwrite', async (tx) => {
        tx.objectStore(META).delete(name);
        tx.objectStore(BYTES).delete(name);
      }),
    markExported: (names, at) =>
      run([META], 'readwrite', async (tx) => {
        const s = tx.objectStore(META);
        for (const n of names) {
          const m = (await req(s.get(n))) as StoredMeta | undefined;
          if (m) s.put({ ...m, exportedAt: at });
        }
      }),
    deleteExported: () =>
      run([META, BYTES], 'readwrite', async (tx) => {
        const all = (await req(tx.objectStore(META).getAll())) as StoredMeta[];
        const gone = all.filter((m) => !!m.exportedAt);
        for (const m of gone) {
          tx.objectStore(META).delete(m.name);
          tx.objectStore(BYTES).delete(m.name);
        }
        return gone.length;
      }),
  };
  return store;
}
