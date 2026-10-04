import type { ErrorCode } from '../contracts';
import { messageFor } from '../quality';
import { h } from './dom';

/** The only error text the screens ever show is messageFor(code). */
export function bannerView(code: ErrorCode, a: { retry(): void; dismiss(): void }): HTMLElement {
  return h('div', { class: 'banner', role: 'alert', 'data-code': code },
    h('p', null, messageFor(code)),
    h('div', { class: 'row' },
      h('button', { type: 'button', class: 'btn primary', onclick: () => a.retry() }, 'Reprendre'),
      h('button', { type: 'button', class: 'btn', 'aria-label': 'Fermer le message', onclick: () => a.dismiss() }, 'Fermer')));
}

export function progressView(label: string): HTMLElement {
  return h('div', { class: 'progress', role: 'status' }, h('span', { class: 'spinner', 'aria-hidden': 'true' }), h('span', null, `${label}…`));
}
