// Configurable backend API base URL - matches the logic in main.jsx
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
export const API_BASE_URL = isDevelopment 
  ? 'http://localhost:8001' 
  : 'https://web-production-af8b.up.railway.app'

console.log('🌐 API_BASE_URL configured:', { 
  hostname: window.location.hostname, 
  isDevelopment, 
  API_BASE_URL 
})
