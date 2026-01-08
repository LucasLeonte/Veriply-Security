import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Protected routes that require authentication
const protectedRoutes = [
    "/dashboard",
    "/settings",
    "/inbox",
    "/knowledge-base",
    "/analytics",
    "/bots",
    "/documents",
    "/groups",
    "/agents",
    "/profile",
];

// Public routes that don't require authentication
const publicRoutes = [
    "/login",
    "/register",
    "/forgot-password",
    "/reset-password",
];

export function middleware(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Get auth token from cookies
    const token = request.cookies.get("access_token")?.value;

    // NOTE: Middleware protection is currently disabled because:
    // 1. Frontend and backend run on different ports (localhost:3000 vs 127.0.0.1:8000)
    // 2. Cross-origin cookies require additional configuration
    // 3. Client-side auth (localStorage) already provides protection on each page
    //
    // To enable server-side protection:
    // - Deploy frontend and backend on same domain, or
    // - Configure reverse proxy to handle both on same origin

    // For now, allow all requests through and let client-side handle auth
    return NextResponse.next();

    /* Server-side auth protection (disabled - enable when using same-origin deployment)
    const isProtectedRoute = protectedRoutes.some((route) =>
        pathname.startsWith(route)
    );
    const isPublicRoute = publicRoutes.some((route) =>
        pathname.startsWith(route)
    );

    if (isProtectedRoute && !token) {
        const loginUrl = new URL("/login", request.url);
        loginUrl.searchParams.set("redirect", pathname);
        return NextResponse.redirect(loginUrl);
    }

    if (isPublicRoute && token && pathname !== "/login") {
        return NextResponse.redirect(new URL("/dashboard", request.url));
    }

    return NextResponse.next();
    */
}

// Configure which routes use this middleware
export const config = {
    matcher: [
        /*
         * Match all request paths except:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         * - public files (public folder)
         */
        "/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
    ],
};
