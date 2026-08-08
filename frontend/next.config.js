/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  output: 'export',
  // Explicitly pin the tracing root to this directory so Next.js does not
  // treat the parent repo (which contains another package-lock.json, the
  // backend venv, etc.) as the workspace root and hang while tracing files.
  outputFileTracingRoot: path.join(__dirname),
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;