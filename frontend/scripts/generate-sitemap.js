import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Base URL for production
const BASE_URL = 'https://arbify.net';

// All public routes
const routes = [
    '/',
    '/login',
    '/register',
    '/forgot-password',
    '/reset-password',
    '/subscriptions',
    '/terms',
    '/privacy',
    '/refund-policy',
    '/support'
];

// Protected routes (optional to include but good for structure if some become public)
const protectedRoutes = [
    '/dashboard',
    '/profile',
    '/odds',
    '/arbitrage',
    '/calculator'
];

// Combine routes
const allRoutes = [...routes, ...protectedRoutes];

const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${allRoutes
        .map((route) => {
            return `
  <url>
    <loc>${BASE_URL}${route}</loc>
    <lastmod>${new Date().toISOString().split('T')[0]}</lastmod>
    <changefreq>${route === '/' ? 'daily' : 'weekly'}</changefreq>
    <priority>${route === '/' ? '1.0' : '0.8'}</priority>
  </url>`;
        })
        .join('')}
</urlset>
`;

// Path to public directory
const publicDir = path.resolve(__dirname, '../public');

// Ensure public directory exists
if (!fs.existsSync(publicDir)) {
    fs.mkdirSync(publicDir, { recursive: true });
}

// Write sitemap.xml
fs.writeFileSync(path.join(publicDir, 'sitemap.xml'), sitemap);

console.log('✅ Sitemap generated successfully at proper location!');
