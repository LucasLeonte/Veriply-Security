import { NextRequest, NextResponse } from "next/server";

export async function POST(
    request: NextRequest,
    { params }: { params: Promise<{ id: string }> }
) {
    try {
        // In production, add authentication check here

        const { reason } = await request.json();
        const { id: itemId } = await params;

        // In production, update the database and log rejection reason
        console.log(`Rejecting item ${itemId}`, { reason });

        return NextResponse.json({
            success: true,
            itemId,
            action: "rejected",
            reason: reason || "No reason provided",
        });
    } catch (error) {
        console.error("Error rejecting item:", error);
        return NextResponse.json(
            { error: "Failed to reject item" },
            { status: 500 }
        );
    }
}
