// Node and jsdom have no ImageData: provide a minimal one for every test.
class ImageDataPolyfill {
  readonly data: Uint8ClampedArray;
  readonly width: number;
  readonly height: number;
  readonly colorSpace = 'srgb';

  constructor(width: number, height: number);
  constructor(data: Uint8ClampedArray, width: number, height?: number);
  constructor(a: number | Uint8ClampedArray, b: number, c?: number) {
    // Same failures as the real ImageData, so a test cannot pass here and break in a browser.
    const size = (n: number) => {
      if (!Number.isInteger(n) || n <= 0) throw new RangeError('ImageData: width and height must be positive integers');
      return n;
    };
    if (typeof a === 'number') {
      this.width = size(a);
      this.height = size(b);
      this.data = new Uint8ClampedArray(this.width * this.height * 4);
    } else {
      if (a.length === 0 || a.length % 4 !== 0) throw new RangeError('ImageData: data length must be a non-zero multiple of 4');
      this.width = size(b);
      this.height = size(c ?? a.length / 4 / b);
      if (a.length !== this.width * this.height * 4) throw new RangeError('ImageData: data length does not match width x height');
      this.data = a;
    }
  }
}

const g = globalThis as { ImageData?: unknown };
if (typeof g.ImageData === 'undefined') g.ImageData = ImageDataPolyfill;
