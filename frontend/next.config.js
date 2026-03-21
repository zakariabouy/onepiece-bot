/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
      { source: "/static/:path*", destination: "http://localhost:8000/static/:path*" },
    ];
  },
};

module.exports = nextConfig;
