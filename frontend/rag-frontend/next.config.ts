import type { NextConfig } from "next";


/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
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