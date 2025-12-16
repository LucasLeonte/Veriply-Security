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

// Disable Next.js telemetry at config load time to avoid type-unsupported `telemetry` field
process.env.NEXT_TELEMETRY_DISABLED = "1";

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
        unoptimized: process.env.NODE_ENV === "development",
        remotePatterns: [
            {
                protocol: "http",
                hostname: "localhost",
                port: "8000",
                pathname: "/avatars/**",
            },
            {
                protocol: "http",
                hostname: "127.0.0.1",
                port: "8000",
                pathname: "/avatars/**",
            },
            {
                protocol: "https",
                hostname: "api.dicebear.com",
            },
        ],
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
};

export default nextConfig;
