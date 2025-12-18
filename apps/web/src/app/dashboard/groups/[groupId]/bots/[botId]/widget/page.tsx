"use client";
import { WidgetConfigClient } from "./widget-client";
import { DashboardLayout } from "@/components";
import { useParams } from "next/navigation";

export default function WidgetConfigPage() {
    const params = useParams();
    const groupId = params.groupId as string;
    const botId = params.botId as string;
    return (
        <DashboardLayout>
            <WidgetConfigClient groupId={groupId} botId={botId} />
        </DashboardLayout>
    );
}
