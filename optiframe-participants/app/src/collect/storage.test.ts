import { describe, expect, it } from 'vitest';
import { fakeIndexedDB } from './fakeIdb.testutil';
import type { Meta } from './manifest';
import { FRENCH_QUOTA, openStore, StorageError } from './storage';

const meta = (name: string, o: Partial<Meta> = {}): Meta => ({
  name, mode: 'validation', lensId: 'L01', phone: 'p', rep: 1, takenAt: '2026-01-01T00:00:00Z', bytes: 4, mime: 'image/jpeg', userAgent: 'UA', appVersion: '0.1.0', ok: true, ...o,
});
const buf = (...n: number[]) => Uint8Array.from(n).buffer as ArrayBuffer;

describe('photo store (fake IndexedDB)', () => {
  it('adds, lists without bytes, reads bytes back untouched', async () => {
    const s = await openStore(fakeIndexedDB());
    await s.put(meta('a.jpg'), buf(1, 2, 3, 4));
    await s.put(meta('b.jpg'), buf(9));
    const list = await s.list();
    expect(list.map((m) => m.name).sort()).toEqual(['a.jpg', 'b.jpg']);
    expect('bytes' in list[0] && (list[0] as unknown as { data?: unknown }).data).toBeFalsy();
    expect(new Uint8Array((await s.getBytes('a.jpg'))!)).toEqual(Uint8Array.from([1, 2, 3, 4]));
    expect(await s.getBytes('zzz')).toBeUndefined();
  });
  it('refuses a duplicate name (case-insensitive) unless replacing', async () => {
    const s = await openStore(fakeIndexedDB());
    await s.put(meta('a.jpg'), buf(1));
    await expect(s.put(meta('A.JPG'), buf(2))).rejects.toMatchObject({ kind: 'exists' });
    await s.put(meta('a.jpg', { notes: 'new' }), buf(3), true);
    expect((await s.list())).toHaveLength(1);
    expect(new Uint8Array((await s.getBytes('a.jpg'))!)[0]).toBe(3);
  });
  it('deletes one photo (meta and bytes)', async () => {
    const s = await openStore(fakeIndexedDB());
    await s.put(meta('a.jpg'), buf(1));
    await s.put(meta('b.jpg'), buf(2));
    await s.delete('a.jpg');
    expect((await s.list()).map((m) => m.name)).toEqual(['b.jpg']);
    expect(await s.getBytes('a.jpg')).toBeUndefined();
  });
  it('marks exported, and deleteExported never touches a photo that was not exported', async () => {
    const s = await openStore(fakeIndexedDB());
    for (const n of ['a.jpg', 'b.jpg', 'c.jpg']) await s.put(meta(n), buf(1));
    await s.markExported(['a.jpg', 'c.jpg', 'ghost.jpg'], '2026-02-02T00:00:00Z');
    const list = await s.list();
    expect(list.find((m) => m.name === 'a.jpg')!.exportedAt).toBe('2026-02-02T00:00:00Z');
    expect(list.find((m) => m.name === 'b.jpg')!.exportedAt).toBeUndefined();
    expect(await s.deleteExported()).toBe(2);
    expect((await s.list()).map((m) => m.name)).toEqual(['b.jpg']);
    expect(await s.getBytes('b.jpg')).toBeDefined();
    expect(await s.getBytes('a.jpg')).toBeUndefined();
    expect(await s.deleteExported()).toBe(0);
  });
  it('turns a quota error into a French sentence and keeps what was stored before', async () => {
    const opts: { failPutWith?: string } = {};
    const s = await openStore(fakeIndexedDB(opts));
    await s.put(meta('a.jpg'), buf(1));
    opts.failPutWith = 'QuotaExceededError';
    const err = await s.put(meta('b.jpg'), buf(2)).catch((e) => e);
    expect(err).toBeInstanceOf(StorageError);
    expect(err.kind).toBe('quota');
    expect(err.message).toBe(FRENCH_QUOTA);
    opts.failPutWith = undefined;
    expect((await s.list()).map((m) => m.name)).toEqual(['a.jpg']);
  });
  it('says so when IndexedDB is missing', async () => {
    await expect(openStore(undefined)).rejects.toBeInstanceOf(StorageError);
  });
});
