/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export', // Temporarily disabled to resolve dev server issues
  // trailingSlash: true, // Removed to simplify routing and resolve build errors
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;