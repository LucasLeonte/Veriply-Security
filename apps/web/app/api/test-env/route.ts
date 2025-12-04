/**
 * Test API Route - Verify Environment Variables
 * 
 * This route tests that:
 * 1. Server-side environment variables are loaded from root .env
 * 2. API URL is accessible and can be called from Next.js
 * 3. Configuration is properly inherited from root .env via symlink
 * 
 * Access: http://localhost:3000/api/test-env
 */

import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Test environment variable loading
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const nextAuthUrl = process.env.NEXTAUTH_URL;
    const nextAuthSecret = process.env.NEXTAUTH_SECRET;
    const environment = process.env.ENVIRONMENT;

    // Try to call the API health endpoint
    let apiHealthy = false;
    let apiResponse = null;

    if (apiUrl) {
      try {
        const response = await fetch(`${apiUrl}/healthz`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
          },
          // Add timeout
          signal: AbortSignal.timeout(5000),
        });

        if (response.ok) {
          apiHealthy = true;
          apiResponse = await response.json();
        }
      } catch (error) {
        console.error('API health check failed:', error);
      }
    }

    return NextResponse.json({
      success: true,
      message: 'Environment variables loaded successfully',
      environment: {
        NEXT_PUBLIC_API_URL: apiUrl || '(not set)',
        NEXTAUTH_URL: nextAuthUrl || '(not set)',
        NEXTAUTH_SECRET: nextAuthSecret ? '***set***' : '(not set)',
        ENVIRONMENT: environment || 'development',
      },
      apiHealthCheck: {
        configured: !!apiUrl,
        reachable: apiHealthy,
        response: apiResponse,
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
