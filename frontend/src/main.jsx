import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './responsive-utilities.css'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext'
// import { registerServiceWorker } from './utils/registerServiceWorker'

// Optional: Register service worker for PWA capabilities
// Uncomment the line below to enable offline support and caching
// registerServiceWorker();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </StrictMode>,
)
