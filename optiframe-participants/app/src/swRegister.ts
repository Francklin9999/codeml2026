// Registers ./sw.js so the app works offline after the first load.
// `?nosw=1` unregisters it and clears its caches (escape hatch for a bad cache).
export async function registerServiceWorker(): Promise<void> {
  if (typeof navigator === 'undefined' || !('serviceWorker' in navigator)) return;
  try {
    if (new URLSearchParams(location.search).get('nosw') === '1') {
      for (const reg of await navigator.serviceWorker.getRegistrations()) await reg.unregister();
      if (typeof caches !== 'undefined') for (const key of await caches.keys()) await caches.delete(key);
      return;
    }
    if (document.readyState !== 'complete') {
      await new Promise<void>((done) => addEventListener('load', () => done(), { once: true }));
    }
    await navigator.serviceWorker.register('./sw.js');
  } catch {
    // Offline support is optional: never break the app because of it.
  }
}
