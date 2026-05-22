import React from 'react';
import ReactDOM from 'react-dom/client';
import { ThemeProvider } from '@kk-ai/ui';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
