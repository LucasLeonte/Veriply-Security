export type GroupRole = "owner" | "admin" | "manager" | "agent" | "viewer";

export interface Group {
    id: string;
    tenant_id: string;
    name: string;
    description?: string;
    created_by: string;
    created_at: string;
    updated_at: string;
    current_user_role?: GroupRole; // Role of the current user in this group
}

export interface GroupMember {
    id: string;
    group_id: string;
    user_id: string;
    role: GroupRole;
    invited_at: string;
    invited_by_id: string;
    name?: string;
    email?: string;
}

export interface CreateGroupInput {
    name: string;
    description?: string;
}

export interface UpdateGroupInput {
    name?: string;
    description?: string;
}

export interface InviteMemberInput {
    email: string;
    role: GroupRole;
}

export interface GroupMemberInviteResponse {
    message: string;
    user_id: string;
}

export interface GroupKBStats {
    doc_count: number;
    chunk_count: number;
    bot_count: number;
    total_size_bytes: number;
}
