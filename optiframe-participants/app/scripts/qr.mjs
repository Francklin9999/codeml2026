// Usage: npm run qr -- https://user.github.io/repo/
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import QRCode from 'qrcode';

const url = process.argv[2];
if (!url || !/^https:\/\//.test(url)) {
  console.error('Usage: npm run qr -- https://your-public-url/');
  process.exit(1);
}
const svg = await QRCode.toString(url, { type: 'svg', margin: 2, errorCorrectionLevel: 'M' });
const out = fileURLToPath(new URL('../public/qr.svg', import.meta.url));
writeFileSync(out, svg);
console.log('QR code for ' + url + ' written to ' + out);
