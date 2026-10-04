/// <reference types="vite/client" />
import './ui/styles.css';
import { messageFor } from './quality';
import { registerServiceWorker } from './swRegister';
import { startApp } from './ui/app';

const app = document.getElementById('app')!;
try {
  startApp(app, location.search);
} catch {
  app.textContent = messageFor('LOAD_FAILED');
}

if (import.meta.env.PROD) void registerServiceWorker();
