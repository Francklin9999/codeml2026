export const FILE_NAMES = { svgLeft: 'contour-gauche.svg', svgRight: 'contour-droit.svg', stl: 'monture.stl', json: 'mesures.json' } as const;

/** Call from a user gesture (iOS Safari). */
export function saveBlob(data: BlobPart, filename: string, mime: string): void {
  const url = URL.createObjectURL(new Blob([data], { type: mime }));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { a.remove(); URL.revokeObjectURL(url); }, 4000);
}
