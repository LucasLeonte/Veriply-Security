import { NextResponse } from "next/server";

export async function POST() {
    const response = NextResponse.json({ success: true });

    // Proactively clear common auth cookies if they exist
    const expired = new Date(0);
    response.cookies.set("access_token", "", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        expires: expired,
        path: "/",
        sameSite: "lax",
    });
    response.cookies.set("refresh_token", "", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        expires: expired,
        path: "/",
        sameSite: "lax",
    });

    return response;
}
