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

export function proxy(request: NextRequest) {
    const { pathname } = request.nextUrl;

    // Get auth token from cookies
    const token = request.cookies.get("access_token")?.value;

    // NOTE: Proxy protection currently disabled because frontend/backed run on different origins.
    // Client-side auth remains active. Enable server-side redirects after same-origin deployment.
    return NextResponse.next();

    /* Server-side auth protection (enable when on same origin)
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

export const config = {
    matcher: [
        "/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
    ],
};
