import { afterEach, describe, expect, it, vi } from 'vitest';
import { registerServiceWorker } from './swRegister';

afterEach(() => vi.unstubAllGlobals());

describe('registerServiceWorker', () => {
  it('is a no-op when navigator.serviceWorker is absent', async () => {
    vi.stubGlobal('navigator', {});
    await expect(registerServiceWorker()).resolves.toBeUndefined();
  });

  it('registers ./sw.js when supported', async () => {
    const register = vi.fn().mockResolvedValue({});
    vi.stubGlobal('navigator', { serviceWorker: { register } });
    vi.stubGlobal('location', { search: '' });
    vi.stubGlobal('document', { readyState: 'complete' });
    await registerServiceWorker();
    expect(register).toHaveBeenCalledWith('./sw.js');
  });

  it('?nosw=1 unregisters the worker and clears the caches', async () => {
    const unregister = vi.fn().mockResolvedValue(true);
    const register = vi.fn();
    const del = vi.fn().mockResolvedValue(true);
    vi.stubGlobal('navigator', { serviceWorker: { register, getRegistrations: async () => [{ unregister }] } });
    vi.stubGlobal('location', { search: '?nosw=1' });
    vi.stubGlobal('caches', { keys: async () => ['optiframe-v1'], delete: del });
    await registerServiceWorker();
    expect(unregister).toHaveBeenCalled();
    expect(del).toHaveBeenCalledWith('optiframe-v1');
    expect(register).not.toHaveBeenCalled();
  });
});
