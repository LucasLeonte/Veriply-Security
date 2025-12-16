"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/DashboardLayout";
import { useGroup } from "@/contexts/GroupContext";
import { Button } from "@/components/ui/button";
import { groupsApi } from "@/lib/api/groups";
import { Group, GroupMember, GroupRole } from "@/types/group";
import { getAccessToken } from "@/lib/auth";
import {
    Plus,
    Trash2,
    Mail,
    Users,
    Crown,
    Shield,
    ArrowRight,
} from "lucide-react";

export default function GroupsPage() {
    const router = useRouter();
    const { groups, currentGroup, setCurrentGroup, refreshGroups } = useGroup();
    const [members, setMembers] = useState<GroupMember[]>([]);
    const [loadingMembers, setLoadingMembers] = useState(false);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [newGroupName, setNewGroupName] = useState("");
    const [newGroupDescription, setNewGroupDescription] = useState("");
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState<GroupRole>("operator");

    // Load members when group changes
    React.useEffect(() => {
        if (currentGroup) {
            loadMembers(currentGroup.id);
        }
    }, [currentGroup]);

    const loadMembers = async (groupId: string) => {
        setLoadingMembers(true);
        try {
            const result = await groupsApi.listMembers(groupId);
            setMembers(result);
        } catch (err) {
            console.error("Failed to load members:", err);
        } finally {
            setLoadingMembers(false);
        }
    };

    const handleCreateGroup = async () => {
        if (!newGroupName.trim()) return;

        const token = typeof window !== "undefined" ? getAccessToken() : null;
        if (!token) {
            alert(
                "You must be logged in to create a group. Please sign in again."
            );
            router.push("/login");
            return;
        }

        try {
            const newGroup = await groupsApi.createGroup({
                name: newGroupName,
                description: newGroupDescription || undefined,
            });
            await refreshGroups();
            setCurrentGroup(newGroup);
            setShowCreateModal(false);
            setNewGroupName("");
            setNewGroupDescription("");
            // Redirect to dashboard after creating first group
            router.push("/");
        } catch (err) {
            console.error("Failed to create group:", err);
            const message =
                err instanceof Error ? err.message : "Failed to create group";
            alert(message);
        }
    };

    const handleDeleteGroup = async (groupId: string) => {
        if (!confirm("Are you sure you want to delete this group?")) return;

        try {
            await groupsApi.deleteGroup(groupId);
            await refreshGroups();
        } catch (err) {
            console.error("Failed to delete group:", err);
            alert("Failed to delete group");
        }
    };

    const handleInviteMember = async () => {
        if (!currentGroup || !inviteEmail.trim()) return;

        try {
            await groupsApi.inviteMember(currentGroup.id, {
                email: inviteEmail,
                role: inviteRole,
            });
            await loadMembers(currentGroup.id);
            setShowInviteModal(false);
            setInviteEmail("");
            setInviteRole("operator");
        } catch (err) {
            console.error("Failed to invite member:", err);
            alert("Failed to invite member");
        }
    };

    const handleRemoveMember = async (userId: string) => {
        if (!currentGroup) return;
        if (!confirm("Are you sure you want to remove this member?")) return;

        try {
            await groupsApi.removeMember(currentGroup.id, userId);
            await loadMembers(currentGroup.id);
        } catch (err) {
            console.error("Failed to remove member:", err);
            alert("Failed to remove member");
        }
    };

    const handleUpdateRole = async (userId: string, newRole: GroupRole) => {
        if (!currentGroup) return;

        try {
            await groupsApi.updateMemberRole(currentGroup.id, userId, newRole);
            await loadMembers(currentGroup.id);
        } catch (err) {
            console.error("Failed to update role:", err);
            alert("Failed to update role");
        }
    };

    const getRoleIcon = (role: GroupRole) => {
        switch (role) {
            case "group_admin":
                return <Crown className="h-4 w-4 text-amber-600" />;
            case "manager":
                return <Shield className="h-4 w-4 text-blue-600" />;
            case "operator":
                return <Users className="h-4 w-4 text-slate-600" />;
        }
    };

    return (
        <DashboardLayout>
            <div className="max-w-5xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <h1 className="text-2xl font-bold text-slate-950">
                        Groups
                    </h1>
                    <div className="flex gap-2">
                        {currentGroup && (
                            <Button
                                variant="outline"
                                onClick={() => router.push("/")}
                            >
                                <ArrowRight className="h-4 w-4 mr-2" />
                                Go to Dashboard
                            </Button>
                        )}
                        <Button onClick={() => setShowCreateModal(true)}>
                            <Plus className="h-4 w-4 mr-2" />
                            Create Group
                        </Button>
                    </div>
                </div>

                {/* Groups List */}
                <div className="bg-white rounded-lg border border-slate-300 shadow-sm">
                    <div className="p-4 border-b border-slate-300">
                        <h2 className="text-lg font-semibold text-slate-950">
                            Your Groups
                        </h2>
                    </div>
                    <div className="divide-y divide-slate-300">
                        {groups.map((group) => (
                            <div
                                key={group.id}
                                className="p-4 flex items-center justify-between hover:bg-slate-50"
                            >
                                <div className="flex-1">
                                    <h3 className="font-medium text-slate-950">
                                        {group.name}
                                    </h3>
                                    {group.description && (
                                        <p className="text-sm text-slate-600 mt-1">
                                            {group.description}
                                        </p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2">
                                    {currentGroup?.id === group.id && (
                                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                            Current
                                        </span>
                                    )}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={() =>
                                            handleDeleteGroup(group.id)
                                        }
                                    >
                                        <Trash2 className="h-4 w-4 text-red-600" />
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Members Section */}
                {currentGroup && (
                    <div className="bg-white rounded-lg border border-slate-300 shadow-sm">
                        <div className="p-4 border-b border-slate-300 flex items-center justify-between">
                            <h2 className="text-lg font-semibold text-slate-950">
                                Members of {currentGroup.name}
                            </h2>
                            <Button
                                onClick={() => setShowInviteModal(true)}
                                size="sm"
                            >
                                <Mail className="h-4 w-4 mr-2" />
                                Invite Member
                            </Button>
                        </div>
                        <div className="divide-y divide-slate-300">
                            {loadingMembers ? (
                                <div className="p-4 text-center text-slate-600">
                                    Loading...
                                </div>
                            ) : members.length === 0 ? (
                                <div className="p-4 text-center text-slate-600">
                                    No members yet
                                </div>
                            ) : (
                                members.map((member) => (
                                    <div
                                        key={member.user_id}
                                        className="p-4 flex items-center justify-between"
                                    >
                                        <div className="flex items-center gap-3">
                                            {getRoleIcon(member.role)}
                                            <div>
                                                <p className="font-medium text-slate-950">
                                                    User {member.user_id}
                                                </p>
                                                <p className="text-sm text-slate-600 capitalize">
                                                    {member.role.replace(
                                                        "_",
                                                        " "
                                                    )}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <select
                                                value={member.role}
                                                onChange={(e) =>
                                                    handleUpdateRole(
                                                        member.user_id,
                                                        e.target
                                                            .value as GroupRole
                                                    )
                                                }
                                                className="text-sm border border-slate-300 rounded px-2 py-1"
                                            >
                                                <option value="operator">
                                                    Operator
                                                </option>
                                                <option value="manager">
                                                    Manager
                                                </option>
                                                <option value="group_admin">
                                                    Group Admin
                                                </option>
                                            </select>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() =>
                                                    handleRemoveMember(
                                                        member.user_id
                                                    )
                                                }
                                            >
                                                <Trash2 className="h-4 w-4 text-red-600" />
                                            </Button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                {/* Create Group Modal */}
                {showCreateModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h2 className="text-xl font-semibold mb-4">
                                Create New Group
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        Name
                                    </label>
                                    <input
                                        type="text"
                                        value={newGroupName}
                                        onChange={(e) =>
                                            setNewGroupName(e.target.value)
                                        }
                                        className="w-full border border-slate-300 rounded px-3 py-2"
                                        placeholder="Enter group name"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        Description (optional)
                                    </label>
                                    <textarea
                                        value={newGroupDescription}
                                        onChange={(e) =>
                                            setNewGroupDescription(
                                                e.target.value
                                            )
                                        }
                                        className="w-full border border-slate-300 rounded px-3 py-2"
                                        placeholder="Enter description"
                                        rows={3}
                                    />
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <Button
                                    onClick={handleCreateGroup}
                                    className="flex-1"
                                >
                                    Create
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => setShowCreateModal(false)}
                                    className="flex-1"
                                >
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Invite Member Modal */}
                {showInviteModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h2 className="text-xl font-semibold mb-4">
                                Invite Member
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={inviteEmail}
                                        onChange={(e) =>
                                            setInviteEmail(e.target.value)
                                        }
                                        className="w-full border border-slate-300 rounded px-3 py-2"
                                        placeholder="user@example.com"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        Role
                                    </label>
                                    <select
                                        value={inviteRole}
                                        onChange={(e) =>
                                            setInviteRole(
                                                e.target.value as GroupRole
                                            )
                                        }
                                        className="w-full border border-slate-300 rounded px-3 py-2"
                                    >
                                        <option value="operator">
                                            Operator
                                        </option>
                                        <option value="manager">Manager</option>
                                        <option value="group_admin">
                                            Group Admin
                                        </option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <Button
                                    onClick={handleInviteMember}
                                    className="flex-1"
                                >
                                    Send Invite
                                </Button>
                                <Button
                                    variant="outline"
                                    onClick={() => setShowInviteModal(false)}
                                    className="flex-1"
                                >
                                    Cancel
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
