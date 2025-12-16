"use client";

import React, {
    createContext,
    useContext,
    useState,
    useEffect,
    ReactNode,
} from "react";
import { Group } from "@/types/group";
import { getAccessToken } from "@/lib/auth";
import { groupsApi } from "@/lib/api/groups";

interface GroupContextType {
    currentGroup: Group | null;
    groups: Group[];
    isLoading: boolean;
    error: Error | null;
    setCurrentGroup: (group: Group | null) => void;
    refreshGroups: () => Promise<void>;
}

const GroupContext = createContext<GroupContextType | undefined>(undefined);

export function GroupProvider({ children }: { children: ReactNode }) {
    const [currentGroup, setCurrentGroupState] = useState<Group | null>(null);
    const [groups, setGroups] = useState<Group[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const refreshGroups = async () => {
        // Check if user is logged in before fetching
        if (typeof window === "undefined") return;
        const token = getAccessToken();
        if (!token) {
            setIsLoading(false);
            return; // Don't fetch if not logged in
        }

        setIsLoading(true);
        setError(null);
        try {
            const fetchedGroups = await groupsApi.listGroups();
            setGroups(fetchedGroups);

            // Auto-select first group if none selected
            if (!currentGroup && fetchedGroups.length > 0) {
                const savedGroupId =
                    typeof window !== "undefined"
                        ? localStorage.getItem("currentGroupId")
                        : null;
                const groupToSelect = savedGroupId
                    ? fetchedGroups.find((g) => g.id === savedGroupId) ||
                      fetchedGroups[0]
                    : fetchedGroups[0];
                setCurrentGroupState(groupToSelect);
            }
        } catch (err) {
            setError(
                err instanceof Error ? err : new Error("Failed to fetch groups")
            );
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        refreshGroups();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const setCurrentGroup = (group: Group | null) => {
        setCurrentGroupState(group);
        if (typeof window !== "undefined" && group) {
            localStorage.setItem("currentGroupId", group.id);
        }
    };

    return (
        <GroupContext.Provider
            value={{
                currentGroup,
                groups,
                isLoading,
                error,
                setCurrentGroup,
                refreshGroups,
            }}
        >
            {children}
        </GroupContext.Provider>
    );
}

export function useGroup() {
    const context = useContext(GroupContext);
    if (context === undefined) {
        throw new Error("useGroup must be used within a GroupProvider");
    }
    return context;
}
