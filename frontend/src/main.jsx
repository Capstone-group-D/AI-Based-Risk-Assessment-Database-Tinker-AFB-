/**
 * main.jsx — Application Entry Point
 *
 * This is the very first file that runs when the app loads.
 * It mounts the root <App /> component into the #root div in index.html.
 *
 * - StrictMode enables extra development warnings for common React mistakes.
 * - index.css is imported here so global styles (fonts, colors, scrollbars)
 *   are applied before any component renders.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
