"use client";

import { useGroup } from "@/contexts/GroupContext";
import { useRouter } from "next/navigation";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Users, Plus } from "lucide-react";

export function GroupSwitcher() {
    const { currentGroup, groups, isLoading, setCurrentGroup } = useGroup();
    const router = useRouter();

    if (isLoading) {
        return (
            <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
                <Users className="h-4 w-4" />
                <span>Loading groups...</span>
            </div>
        );
    }

    if (groups.length === 0) {
        return (
            <div className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground">
                <Users className="h-4 w-4" />
                <span>No groups</span>
            </div>
        );
    }

    return (
        <Select
            value={currentGroup?.id}
            onValueChange={(groupId: string) => {
                if (groupId === "create-new") {
                    router.push("/groups");
                    return;
                }
                const group = groups.find((g) => g.id === groupId);
                if (group) {
                    setCurrentGroup(group);
                }
            }}
        >
            <SelectTrigger className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-slate-50 border-0 h-auto">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-emerald-400 flex items-center justify-center text-white text-xs font-bold">
                        {currentGroup?.name?.slice(0, 2).toUpperCase() || "GR"}
                    </div>
                    <div className="text-left">
                        <p className="text-sm font-semibold text-slate-900">
                            {currentGroup?.name || "Current Group"}
                        </p>
                        <p className="text-xs text-slate-500">Switch group</p>
                    </div>
                </div>
            </SelectTrigger>
            <SelectContent className="bg-white">
                {groups.map((group) => (
                    <SelectItem key={group.id} value={group.id}>
                        {group.name}
                    </SelectItem>
                ))}
                <div className="my-2 border-t border-slate-200" />
                <SelectItem value="create-new">
                    <span className="text-sky-600 font-medium flex items-center gap-2">
                        <Plus className="h-4 w-4" />
                        Create new group
                    </span>
                </SelectItem>
            </SelectContent>
        </Select>
    );
}
