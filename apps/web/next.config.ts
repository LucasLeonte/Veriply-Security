import type { NextConfig } from "next";

/**
 * Next.js Configuration
 * 
 * Environment Variables:
 * - Next.js automatically loads .env, .env.local, .env.production, etc.
 * - For this project, we use the root ../../.env file (loaded via Docker Compose)
 * - NEXT_PUBLIC_* variables are exposed to the browser
 * - Other variables are server-side only
 * 
 * See apps/web/.env.example for documentation of all variables.
 */

const nextConfig: NextConfig = {
  // Environment variable configuration
  env: {
    // These are loaded from .env automatically, but we can document them here
    // NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    // NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    // NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
  },

  // Compiler options
  compiler: {
    // Remove console.log in production
    removeConsole: process.env.NODE_ENV === "production",
  },

  // Image optimization
  images: {
    domains: ["localhost"],
  },

  // Experimental features
  experimental: {
    // Enable server actions
    serverActions: {
      bodySizeLimit: "50mb", // Match MAX_UPLOAD_SIZE_MB from .env
    },
  },

  // Output configuration
  output: "standalone", // For Docker deployment

  // Disable telemetry
  telemetry: false,
};

export default nextConfig;

