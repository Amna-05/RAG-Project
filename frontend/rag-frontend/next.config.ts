import type { NextConfig } from "next";


/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Output mode for Docker deployment
  output: 'standalone',

  // Enable optimized package imports
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },

  // Image optimization (if you'll use next/image)
  images: {
    remotePatterns: [],
  },

  // Disable x-powered-by header for security
  poweredByHeader: false,
};

export default nextConfig;