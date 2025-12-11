"use client";

import { useGroup } from "@/contexts/GroupContext";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Users } from "lucide-react";

export function GroupSwitcher() {
    const { currentGroup, groups, isLoading, setCurrentGroup } = useGroup();

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
        <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-muted-foreground" />
            <Select
                value={currentGroup?.id}
                onValueChange={(groupId: string) => {
                    const group = groups.find((g) => g.id === groupId);
                    if (group) {
                        setCurrentGroup(group);
                    }
                }}
            >
                <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Select group" />
                </SelectTrigger>
                <SelectContent>
                    {groups.map((group) => (
                        <SelectItem key={group.id} value={group.id}>
                            {group.name}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
        </div>
    );
}
