import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { HelmetProvider } from 'react-helmet-async'
import './index.css'
import 'react-toastify/dist/ReactToastify.css'
import '@fortawesome/fontawesome-free/css/all.min.css'
import App from './App.jsx'
import axios from 'axios'
import { AuthProvider } from './context/AuthContext'

// Initialize Sentry error tracking
import { initSentry } from './utils/sentry.js'
initSentry()

// Initialize Google Analytics
import { initAnalytics } from './utils/analytics.js'
initAnalytics()

// Configure axios with the appropriate backend URL based on environment
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
const backendURL = isDevelopment
  ? 'http://localhost:8001'
  : 'https://web-production-af8b.up.railway.app'

console.log('Environment detection:', {
  hostname: window.location.hostname,
  isDevelopment,
  backendURL
})

axios.defaults.baseURL = backendURL
axios.defaults.withCredentials = false // Disable sending cookies for cross-origin requests

// Add request interceptor for handling CORS and auth
axios.interceptors.request.use(
  config => {
    // Add CORS headers if needed
    config.headers = {
      ...config.headers,
      'Accept': 'application/json',
    }

    // Add auth token if available
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    return config
  },
  error => Promise.reject(error)
)

// Add response interceptor for error handling
axios.interceptors.response.use(
  response => response,
  error => {
    // Log authentication errors for debugging
    if (error.response?.status === 401) {
      console.error('🔒 Authentication Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data,
        hasToken: !!localStorage.getItem('access_token')
      })
    } else if (error.response?.status >= 400) {
      console.error('🚨 API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        status: error.response?.status,
        data: error.response?.data
      })
    }
    return Promise.reject(error)
  }
)

// Log authentication status on load for debugging
const token = localStorage.getItem('access_token')
const user = localStorage.getItem('user')
console.log('🔧 Initial auth state:', {
  hasToken: !!token,
  hasUser: !!user,
  tokenStart: token ? token.substring(0, 20) + '...' : 'None',
  userInfo: user ? JSON.parse(user).username : 'None'
})

// Validate token format if it exists
if (token && token !== 'null' && token !== 'undefined') {
  try {
    // Basic JWT token validation (should have 3 parts separated by dots)
    const parts = token.split('.')
    if (parts.length === 3) {
      console.log('✅ Token format appears valid')
    } else {
      console.warn('⚠️ Token format appears invalid:', parts.length, 'parts')
    }
  } catch (e) {
    console.warn('⚠️ Token validation error:', e)
  }
} else {
  console.log('ℹ️ No token found in localStorage')
}

// Render app
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  </React.StrictMode>
)
