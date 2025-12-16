import {
    Group,
    GroupMember,
    CreateGroupInput,
    UpdateGroupInput,
    InviteMemberInput,
} from "@/types/group";
import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const GROUPS_ENDPOINT = `${API_BASE_URL}/api/v1/groups`;

async function getAuthToken(): Promise<string | null> {
    if (typeof window === "undefined") {
        return null;
    }
    return getAccessToken();
}

async function fetchWithAuth(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const token = await getAuthToken();
    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers,
    });

    return response;
}

async function handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
        const error = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }
    return response.json();
}

export const groupsApi = {
    async createGroup(data: CreateGroupInput): Promise<Group> {
        const response = await fetchWithAuth(GROUPS_ENDPOINT, {
            method: "POST",
            body: JSON.stringify(data),
        });
        return handleResponse<Group>(response);
    },

    async listGroups(): Promise<Group[]> {
        const response = await fetchWithAuth(GROUPS_ENDPOINT);
        return handleResponse<Group[]>(response);
    },

    async getGroup(groupId: string): Promise<Group> {
        const response = await fetchWithAuth(`${GROUPS_ENDPOINT}/${groupId}`);
        return handleResponse<Group>(response);
    },

    async updateGroup(groupId: string, data: UpdateGroupInput): Promise<Group> {
        const response = await fetchWithAuth(`${GROUPS_ENDPOINT}/${groupId}`, {
            method: "PATCH",
            body: JSON.stringify(data),
        });
        return handleResponse<Group>(response);
    },

    async deleteGroup(groupId: string): Promise<void> {
        const response = await fetchWithAuth(`${GROUPS_ENDPOINT}/${groupId}`, {
            method: "DELETE",
        });
        if (!response.ok) {
            const error = await response
                .json()
                .catch(() => ({ detail: "Failed to delete group" }));
            throw new Error(error.detail);
        }
    },

    async inviteMember(
        groupId: string,
        data: InviteMemberInput
    ): Promise<GroupMember> {
        const response = await fetchWithAuth(
            `${GROUPS_ENDPOINT}/${groupId}/members`,
            {
                method: "POST",
                body: JSON.stringify(data),
            }
        );
        return handleResponse<GroupMember>(response);
    },

    async listMembers(groupId: string): Promise<GroupMember[]> {
        const response = await fetchWithAuth(
            `${GROUPS_ENDPOINT}/${groupId}/members`
        );
        return handleResponse<GroupMember[]>(response);
    },

    async updateMemberRole(
        groupId: string,
        userId: string,
        role: string
    ): Promise<GroupMember> {
        const response = await fetchWithAuth(
            `${GROUPS_ENDPOINT}/${groupId}/members/${userId}`,
            {
                method: "PATCH",
                body: JSON.stringify({ role }),
            }
        );
        return handleResponse<GroupMember>(response);
    },

    async removeMember(groupId: string, userId: string): Promise<void> {
        const response = await fetchWithAuth(
            `${GROUPS_ENDPOINT}/${groupId}/members/${userId}`,
            {
                method: "DELETE",
            }
        );
        if (!response.ok) {
            const error = await response
                .json()
                .catch(() => ({ detail: "Failed to remove member" }));
            throw new Error(error.detail);
        }
    },
};
