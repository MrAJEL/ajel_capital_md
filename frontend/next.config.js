/** @type {import('next').NextConfig} */

// The browser calls the API on the same origin (/api/...) and Next.js forwards it to the
// backend. This way the app works from any device (localhost, the LAN IP from an iPhone)
// without CORS, and the auth cookies stay first-party.
const API_PROXY_TARGET = process.env.API_PROXY_TARGET || 'http://localhost:8000';

const nextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${API_PROXY_TARGET}/api/:path*` }];
  },
};

module.exports = nextConfig;
