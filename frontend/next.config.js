/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export', // Removed for development server
  trailingSlash: false,
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
