import { describe, expect, it } from 'vitest';

describe('ImageData polyfill', () => {
  it('creates new ImageData(2, 2) in the default environment', () => {
    const img = new ImageData(2, 2);
    expect(img.width).toBe(2);
    expect(img.height).toBe(2);
    expect(img.data).toBeInstanceOf(Uint8ClampedArray);
    expect(img.data.length).toBe(16);
    expect(img.colorSpace).toBe('srgb');
  });

  it('wraps existing data with (data, width, height)', () => {
    const data = new Uint8ClampedArray(3 * 2 * 4);
    const img = new ImageData(data, 3, 2);
    expect(img.data).toBe(data);
    expect([img.width, img.height]).toEqual([3, 2]);
  });
});
