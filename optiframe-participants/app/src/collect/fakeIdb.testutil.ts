// Small in-memory IndexedDB for tests (fake-indexeddb is not installed). Supports only what storage.ts uses:
// open/upgrade, createObjectStore (keyPath or out-of-line keys), transactions over several stores,
// get / getAll / getAllKeys / put / delete. Writes are buffered and applied when the transaction completes,
// so an aborted transaction leaves no trace.

type Handler<T = unknown> = ((ev: T) => void) | null;
type Err = { name: string } | null;

class FakeRequest<T> {
  result!: T;
  error: Err = null;
  onsuccess: Handler = null;
  onerror: Handler = null;
}

interface StoreState { keyPath?: string; data: Map<string, unknown> }

export interface FakeOptions { failPutWith?: string }

class FakeTx {
  error: Err = null;
  oncomplete: Handler = null;
  onerror: Handler = null;
  onabort: Handler = null;
  private pending = 0;
  private writes: (() => void)[] = [];
  private finished = false;
  constructor(private stores: Map<string, StoreState>, private names: string[], private opts: FakeOptions) {
    setTimeout(() => this.check(), 0);
  }
  objectStore(name: string): FakeStore {
    if (!this.names.includes(name)) throw new Error('NotFoundError: ' + name);
    return new FakeStore(this, this.stores.get(name)!, this.opts);
  }
  /** runs `op` in a later microtask, like a real request */
  request<T>(op: () => T, write?: () => void): FakeRequest<T> {
    const r = new FakeRequest<T>();
    this.pending++;
    queueMicrotask(() => {
      if (this.finished) return;
      try {
        if (write && this.opts.failPutWith) throw { name: this.opts.failPutWith };
        r.result = op();
        if (write) this.writes.push(write);
        (r.onsuccess as Handler)?.({});
      } catch (e) {
        r.error = e as Err;
        this.error = e as Err;
        (r.onerror as Handler)?.({});
        this.abort();
      }
      this.pending--;
      setTimeout(() => this.check(), 0);
    });
    return r;
  }
  private abort() {
    if (this.finished) return;
    this.finished = true;
    this.writes = [];
    queueMicrotask(() => (this.onabort as Handler)?.({}));
  }
  private check() {
    if (this.finished || this.pending > 0) return;
    this.finished = true;
    for (const w of this.writes) w();
    (this.oncomplete as Handler)?.({});
  }
}

class FakeStore {
  constructor(private tx: FakeTx, private st: StoreState, _o: FakeOptions) {}
  get(key: string) { return this.tx.request(() => structuredClone(this.st.data.get(key))); }
  getAll() { return this.tx.request(() => [...this.st.data.values()].map((v) => structuredClone(v))); }
  getAllKeys() { return this.tx.request(() => [...this.st.data.keys()]); }
  put(value: unknown, key?: string) {
    const k = key ?? String((value as Record<string, unknown>)[this.st.keyPath!]);
    const copy = structuredClone(value);
    return this.tx.request(() => k, () => { this.st.data.set(k, copy); });
  }
  delete(key: string) { return this.tx.request(() => undefined, () => { this.st.data.delete(key); }); }
}

class FakeDb {
  constructor(private stores: Map<string, StoreState>, private opts: FakeOptions) {}
  createObjectStore(name: string, o?: { keyPath?: string }) { this.stores.set(name, { keyPath: o?.keyPath, data: new Map() }); }
  transaction(names: string[] | string, _mode?: string) { return new FakeTx(this.stores, Array.isArray(names) ? names : [names], this.opts); }
}

export function fakeIndexedDB(opts: FakeOptions = {}): IDBFactory {
  const dbs = new Map<string, Map<string, StoreState>>();
  return {
    open(name: string) {
      const r = new FakeRequest<FakeDb>() as FakeRequest<FakeDb> & { onupgradeneeded: Handler; onblocked: Handler };
      r.onupgradeneeded = null;
      r.onblocked = null;
      setTimeout(() => {
        let stores = dbs.get(name);
        const db = (s: Map<string, StoreState>) => new FakeDb(s, opts);
        if (!stores) {
          stores = new Map();
          dbs.set(name, stores);
          r.result = db(stores);
          r.onupgradeneeded?.({});
        }
        r.result = db(stores);
        r.onsuccess?.({});
      }, 0);
      return r;
    },
  } as unknown as IDBFactory;
}
