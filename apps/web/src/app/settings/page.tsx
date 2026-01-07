"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components";
import { getAccessToken, clearAccessToken } from "@/lib/auth";
import { useGroup } from "@/contexts/GroupContext";
import { groupsApi } from "@/lib/api/groups";
import { Group, GroupMember, GroupRole } from "@/types/group";
import { Plus, Trash2, Mail, Users, Crown, Shield } from "lucide-react";

interface TeamMember {
    id: string;
    email: string;
    name?: string;
    role: string;
    last_active?: string;
    is_active: string;
}

export default function SettingsPage() {
    // Org/team state
    const [members, setMembers] = useState<TeamMember[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [currentUserRole, setCurrentUserRole] = useState<string>("");
    const [showRoleMenu, setShowRoleMenu] = useState<string | null>(null);
    const [showInviteModal, setShowInviteModal] = useState(false);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("manager");
    const [inviteLoading, setInviteLoading] = useState(false);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    // Group state
    const { groups, currentGroup, setCurrentGroup, refreshGroups } = useGroup();
    const [groupMembers, setGroupMembers] = useState<GroupMember[]>([]);
    const [loadingGroupMembers, setLoadingGroupMembers] = useState(false);
    const [showGroupCreateModal, setShowGroupCreateModal] = useState(false);
    const [showGroupInviteModal, setShowGroupInviteModal] = useState(false);
    const [newGroupName, setNewGroupName] = useState("");
    const [newGroupDescription, setNewGroupDescription] = useState("");
    const [groupInviteEmail, setGroupInviteEmail] = useState("");
    const [groupInviteRole, setGroupInviteRole] = useState<GroupRole>("viewer");

    useEffect(() => {
        fetchInitialData();
    }, []);

    // Load group members when selected group changes
    useEffect(() => {
        if (currentGroup) {
            setGroupMembers([]);
            loadGroupMembers(currentGroup.id);
        } else {
            setGroupMembers([]);
        }
    }, [currentGroup]);

    const fetchInitialData = async () => {
        try {
            setLoading(true);
            setError(null);

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
                return;
            }

            const authHeaders = {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            };

            const profileResponse = await fetch(`${apiUrl}/api/v1/profile/me`, {
                method: "GET",
                credentials: "include",
                headers: authHeaders,
            });

            if (profileResponse.status === 401) {
                setError("Session expired. Please log in again.");
                clearAccessToken();
                window.location.href = "/login";
                return;
            }

            if (!profileResponse.ok) {
                const errorData = await profileResponse.json();
                setError(errorData.detail || "Failed to load profile");
                return;
            }

            const profile = await profileResponse.json();
            setCurrentUserRole(profile.role || "");

            const membersResponse = await fetch(
                `${apiUrl}/api/v1/profile/team/members`,
                {
                    method: "GET",
                    credentials: "include",
                    headers: authHeaders,
                }
            );

            if (membersResponse.status === 401) {
                setError("Session expired. Please log in again.");
                clearAccessToken();
                window.location.href = "/login";
                return;
            }

            if (!membersResponse.ok) {
                const errorData = await membersResponse.json();
                setError(errorData.detail || "Failed to load team members");
                return;
            }

            const data: TeamMember[] = await membersResponse.json();
            setMembers(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setLoading(false);
        }
    };

    // Get available roles based on current user's role
    const getAvailableRoles = () => {
        const allRoles = [
            { value: "owner", label: "Owner" },
            { value: "admin", label: "Admin" },
            { value: "manager", label: "Manager" },
            { value: "agent", label: "Agent" },
            { value: "viewer", label: "Viewer" },
        ];

        // Only owners can create other owners
        if (currentUserRole === "owner") {
            return allRoles;
        }

        // Admins can create admins, managers, agents, and viewers (but not owners)
        if (currentUserRole === "admin") {
            return allRoles.filter((role) => role.value !== "owner");
        }

        // Managers and below cannot invite
        return [];
    };

    const loadGroupMembers = async (groupId: string) => {
        setLoadingGroupMembers(true);
        try {
            const result = await groupsApi.listMembers(groupId);
            setGroupMembers(result);
        } catch (err) {
            console.error("Failed to load group members:", err);
        } finally {
            setLoadingGroupMembers(false);
        }
    };

    const handleCreateGroup = async () => {
        if (!newGroupName.trim()) return;

        const token = typeof window !== "undefined" ? getAccessToken() : null;
        if (!token) {
            alert(
                "You must be logged in to create a group. Please sign in again."
            );
            window.location.href = "/login";
            return;
        }

        try {
            const newGroup = await groupsApi.createGroup({
                name: newGroupName,
                description: newGroupDescription || undefined,
            });
            await refreshGroups();
            setGroupMembers([]);
            setCurrentGroup(newGroup);
            await loadGroupMembers(newGroup.id);
            setShowGroupCreateModal(false);
            setNewGroupName("");
            setNewGroupDescription("");
        } catch (err) {
            console.error("Failed to create group:", err);
            const message =
                err instanceof Error ? err.message : "Failed to create group";
            alert(message);
        }
    };

    const handleInviteGroupMember = async () => {
        if (!currentGroup || !groupInviteEmail.trim()) return;

        try {
            await groupsApi.inviteMember(currentGroup.id, {
                email: groupInviteEmail,
                role: groupInviteRole,
            });
            await loadGroupMembers(currentGroup.id);
            setShowGroupInviteModal(false);
            setGroupInviteEmail("");
            setGroupInviteRole("viewer");
        } catch (err) {
            console.error("Failed to invite member:", err);
            alert("Failed to invite member");
        }
    };

    const handleRemoveGroupMember = async (userId: string) => {
        if (!currentGroup) return;
        if (!confirm("Are you sure you want to remove this member?")) return;

        try {
            await groupsApi.removeMember(currentGroup.id, userId);
            await loadGroupMembers(currentGroup.id);
        } catch (err) {
            console.error("Failed to remove member:", err);
            alert("Failed to remove member");
        }
    };

    const handleUpdateGroupRole = async (
        userId: string,
        newRole: GroupRole
    ) => {
        if (!currentGroup) return;

        try {
            await groupsApi.updateMemberRole(currentGroup.id, userId, newRole);
            await loadGroupMembers(currentGroup.id);
        } catch (err) {
            console.error("Failed to update role:", err);
            alert("Failed to update role");
        }
    };

    const getGroupRoleIcon = (role: GroupRole) => {
        switch (role) {
            case "owner":
                return <Crown className="h-4 w-4 text-amber-600" />;
            case "admin":
                return <Shield className="h-4 w-4 text-purple-600" />;
            case "manager":
                return <Shield className="h-4 w-4 text-blue-600" />;
            case "agent":
                return <Users className="h-4 w-4 text-green-600" />;
            case "viewer":
                return <Users className="h-4 w-4 text-slate-600" />;
        }
    };

    const handleRemoveMember = async (memberId: string) => {
        if (
            !confirm(
                "Are you sure you want to remove this team member? They will lose access immediately."
            )
        ) {
            return;
        }

        try {
            setError(null);

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
                return;
            }

            const response = await fetch(
                `${apiUrl}/api/v1/profile/team/members/${memberId}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (response.status === 401) {
                setError("Session expired. Please log in again.");
                clearAccessToken();
                window.location.href = "/login";
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                setError(errorData.detail || "Failed to remove team member");
                return;
            }

            setMembers((prev) => prev.filter((m) => m.id !== memberId));
            setSuccessMessage("Team member removed successfully");
            setSuccess(true);
            setTimeout(() => {
                setSuccess(false);
                setSuccessMessage(null);
            }, 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        }
    };

    const handleChangeRole = async (memberId: string, newRole: string) => {
        try {
            setError(null);

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
                return;
            }

            const response = await fetch(
                `${apiUrl}/api/v1/profile/team/members/${memberId}/role`,
                {
                    method: "PUT",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ role: newRole }),
                }
            );

            if (response.status === 401) {
                setError("Session expired. Please log in again.");
                clearAccessToken();
                window.location.href = "/login";
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                setError(errorData.detail || "Failed to update role");
                return;
            }

            const updatedMember: TeamMember = await response.json();
            setMembers((prev) =>
                prev.map((m) =>
                    m.id === memberId ? { ...m, ...updatedMember } : m
                )
            );
            setShowRoleMenu(null);
            setSuccessMessage("Team member updated successfully");
            setSuccess(true);
            setTimeout(() => {
                setSuccess(false);
                setSuccessMessage(null);
            }, 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        }
    };

    const handleInviteMember = async () => {
        if (!inviteEmail.trim()) {
            setError("Please enter an email address");
            return;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(inviteEmail)) {
            setError("Please enter a valid email address");
            return;
        }

        try {
            setError(null);
            setInviteLoading(true);

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
                return;
            }

            const response = await fetch(
                `${apiUrl}/api/v1/profile/team/invite`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        email: inviteEmail,
                        role: inviteRole,
                    }),
                }
            );

            if (response.status === 401) {
                setError("Session expired. Please log in again.");
                clearAccessToken();
                window.location.href = "/login";
                return;
            }

            if (!response.ok) {
                const errorData = await response.json();
                setError(errorData.detail || "Failed to send invitation");
                return;
            }

            setSuccessMessage("Invite sent successfully");
            setSuccess(true);

            // Refresh the member list to show any updates
            await fetchInitialData();

            setTimeout(() => {
                setSuccess(false);
                setSuccessMessage(null);
            }, 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        } finally {
            setInviteLoading(false);
            setShowInviteModal(false);
            setInviteEmail("");
            setInviteRole("manager");
        }
    };

    const canManageTeam =
        currentUserRole === "owner" || currentUserRole === "admin";
    const roleOptions = ["owner", "admin", "manager", "agent", "viewer"];
    const ownerCount = members.filter(
        (m) => m.role === "owner" && m.is_active === "active"
    ).length;

    const closeGroupModals = () => {
        setShowGroupCreateModal(false);
        setShowGroupInviteModal(false);
    };

    if (loading) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <p className="text-slate-600">Loading team...</p>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto p-6">
                <h1 className="text-3xl font-bold mb-8 text-slate-900">
                    Team Settings
                </h1>

                {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
                        {successMessage || "Operation successful"}
                    </div>
                )}

                {!canManageTeam && (
                    <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
                        You do not have permission to manage group members. Only
                        Owners and Admins can manage the group.
                    </div>
                )}

                {/* Invite Member Button */}
                {canManageTeam && (
                    <div className="mb-6">
                        <button
                            onClick={() => setShowInviteModal(true)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                        >
                            + Invite Group Member
                        </button>
                    </div>
                )}

                {/* Group Members Table */}
                <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-slate-50 border-b border-slate-200">
                                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-800">
                                    Name
                                </th>
                                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-800">
                                    Email
                                </th>
                                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-800">
                                    Role
                                </th>
                                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-800">
                                    Last Active
                                </th>
                                <th className="px-6 py-3 text-left text-sm font-semibold text-slate-800">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody>
                            {members.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan={5}
                                        className="px-6 py-4 text-center text-slate-500"
                                    >
                                        No group members found
                                    </td>
                                </tr>
                            ) : (
                                members.map((member) => (
                                    <tr
                                        key={member.id}
                                        className={`border-b border-slate-200 hover:bg-slate-50 ${
                                            member.is_active === "inactive"
                                                ? "opacity-50"
                                                : ""
                                        }`}
                                    >
                                        <td className="px-6 py-4 text-sm text-slate-800">
                                            {member.name || "N/A"}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600">
                                            {member.email}
                                        </td>
                                        <td className="px-6 py-4 text-sm">
                                            {canManageTeam ? (
                                                <div className="relative inline-block">
                                                    <button
                                                        onClick={() =>
                                                            setShowRoleMenu(
                                                                showRoleMenu ===
                                                                    member.id
                                                                    ? null
                                                                    : member.id
                                                            )
                                                        }
                                                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200 transition"
                                                    >
                                                        {member.role}
                                                    </button>
                                                    {showRoleMenu ===
                                                        member.id && (
                                                        <div className="absolute z-10 mt-1 w-40 bg-white border border-slate-200 rounded-lg shadow-lg">
                                                            {roleOptions.map(
                                                                (role) => (
                                                                    <button
                                                                        key={
                                                                            role
                                                                        }
                                                                        onClick={() =>
                                                                            handleChangeRole(
                                                                                member.id,
                                                                                role
                                                                            )
                                                                        }
                                                                        disabled={
                                                                            member.role ===
                                                                                "owner" &&
                                                                            role !==
                                                                                "owner" &&
                                                                            ownerCount ===
                                                                                1
                                                                        }
                                                                        className={`w-full text-left px-4 py-2 text-sm hover:bg-slate-100 ${
                                                                            member.role ===
                                                                            role
                                                                                ? "bg-blue-50 font-semibold"
                                                                                : ""
                                                                        } ${
                                                                            member.role ===
                                                                                "owner" &&
                                                                            role !==
                                                                                "owner" &&
                                                                            ownerCount ===
                                                                                1
                                                                                ? "opacity-50 cursor-not-allowed"
                                                                                : ""
                                                                        }`}
                                                                    >
                                                                        {role}
                                                                    </button>
                                                                )
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <span className="px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-sm capitalize">
                                                    {member.role}
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-slate-600">
                                            {member.last_active
                                                ? new Date(
                                                      member.last_active
                                                  ).toLocaleDateString()
                                                : "Never"}
                                        </td>
                                        <td className="px-6 py-4 text-sm">
                                            {canManageTeam && (
                                                <button
                                                    onClick={() =>
                                                        handleRemoveMember(
                                                            member.id
                                                        )
                                                    }
                                                    disabled={
                                                        member.role ===
                                                            "owner" &&
                                                        ownerCount === 1
                                                    }
                                                    className={`px-3 py-1 text-red-600 hover:bg-red-50 rounded transition ${
                                                        member.role ===
                                                            "owner" &&
                                                        ownerCount === 1
                                                            ? "opacity-50 cursor-not-allowed"
                                                            : ""
                                                    }`}
                                                >
                                                    Remove
                                                </button>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Groups Management */}
                <div className="mt-10 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-2xl font-semibold text-slate-900">
                            Groups
                        </h2>
                        <div className="flex gap-2">
                            {currentGroup && (
                                <button
                                    onClick={() =>
                                        setShowGroupInviteModal(true)
                                    }
                                    className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                                >
                                    <Mail className="h-4 w-4 inline-block mr-2" />
                                    Invite to Group
                                </button>
                            )}
                            <button
                                onClick={() => setShowGroupCreateModal(true)}
                                className="px-3 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition text-sm"
                            >
                                <Plus className="h-4 w-4 inline-block mr-2" />
                                Create Group
                            </button>
                        </div>
                    </div>

                    <div className="bg-white rounded-lg border border-slate-200 divide-y">
                        {groups.length === 0 ? (
                            <div className="p-4 text-slate-600">
                                No groups yet
                            </div>
                        ) : (
                            groups.map((group: Group) => (
                                <div
                                    key={group.id}
                                    className="p-4 flex items-center justify-between hover:bg-slate-50"
                                >
                                    <div>
                                        <p className="font-medium text-slate-900">
                                            {group.name}
                                        </p>
                                        {group.description && (
                                            <p className="text-sm text-slate-600">
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
                                        <button
                                            onClick={() =>
                                                setCurrentGroup(group)
                                            }
                                            className="px-3 py-1 text-sm border border-slate-300 rounded-lg hover:bg-slate-100"
                                        >
                                            Select
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {currentGroup && (
                        <div className="bg-white rounded-lg border border-slate-200">
                            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
                                <h3 className="text-lg font-semibold text-slate-900">
                                    Members of {currentGroup.name}
                                </h3>
                                <button
                                    onClick={() =>
                                        setShowGroupInviteModal(true)
                                    }
                                    className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm"
                                >
                                    <Mail className="h-4 w-4 inline-block mr-2" />
                                    Invite
                                </button>
                            </div>
                            <div className="divide-y">
                                {loadingGroupMembers ? (
                                    <div className="p-4 text-slate-600">
                                        Loading members...
                                    </div>
                                ) : groupMembers.length === 0 ? (
                                    <div className="p-4 text-slate-600">
                                        No members yet
                                    </div>
                                ) : (
                                    groupMembers.map((member) => (
                                        <div
                                            key={member.user_id}
                                            className="p-4 flex items-center justify-between"
                                        >
                                            <div className="flex items-center gap-3">
                                                {getGroupRoleIcon(member.role)}
                                                <div>
                                                    <p className="font-medium text-slate-900">
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
                                                        handleUpdateGroupRole(
                                                            member.user_id,
                                                            e.target
                                                                .value as GroupRole
                                                        )
                                                    }
                                                    className="text-sm border border-slate-300 rounded px-2 py-1"
                                                >
                                                    <option value="viewer">
                                                        Viewer
                                                    </option>
                                                    <option value="agent">
                                                        Agent
                                                    </option>
                                                    <option value="manager">
                                                        Manager
                                                    </option>
                                                    <option value="admin">
                                                        Admin
                                                    </option>
                                                    <option value="owner">
                                                        Owner
                                                    </option>
                                                </select>
                                                <button
                                                    onClick={() =>
                                                        handleRemoveGroupMember(
                                                            member.user_id
                                                        )
                                                    }
                                                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </button>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {members.length > 0 && (
                    <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-800 text-sm">
                        <p>
                            <strong>Total Members:</strong> {members.length}
                        </p>
                        <p>
                            <strong>Owners:</strong> {ownerCount}
                        </p>
                    </div>
                )}

                {/* Invite Member Modal */}
                {showInviteModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
                            <h2 className="text-xl font-semibold mb-4 text-slate-900">
                                Invite Team Member
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-slate-700">
                                        Email Address
                                    </label>
                                    <input
                                        type="email"
                                        value={inviteEmail}
                                        onChange={(e) =>
                                            setInviteEmail(e.target.value)
                                        }
                                        onKeyPress={(e) => {
                                            if (e.key === "Enter") {
                                                handleInviteMember();
                                            }
                                        }}
                                        placeholder="user@example.com"
                                        className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-1 text-slate-700">
                                        Role
                                    </label>
                                    <select
                                        value={inviteRole}
                                        onChange={(e) =>
                                            setInviteRole(e.target.value)
                                        }
                                        className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    >
                                        {getAvailableRoles().map((role) => (
                                            <option
                                                key={role.value}
                                                value={role.value}
                                            >
                                                {role.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                <p className="text-xs text-slate-500">
                                    An invitation email will be sent to this
                                    address with a signup link.
                                </p>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button
                                    onClick={handleInviteMember}
                                    disabled={inviteLoading}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {inviteLoading
                                        ? "Sending..."
                                        : "Send Invite"}
                                </button>
                                <button
                                    onClick={() => {
                                        setShowInviteModal(false);
                                        setInviteEmail("");
                                        setInviteRole("manager");
                                        setError(null);
                                    }}
                                    disabled={inviteLoading}
                                    className="flex-1 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition font-medium disabled:opacity-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Group Create Modal */}
                {showGroupCreateModal && (
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
                                <button
                                    onClick={handleCreateGroup}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                >
                                    Create
                                </button>
                                <button
                                    onClick={closeGroupModals}
                                    className="flex-1 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Group Invite Modal */}
                {showGroupInviteModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white rounded-lg p-6 w-full max-w-md">
                            <h2 className="text-xl font-semibold mb-4">
                                Invite Group Member
                            </h2>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">
                                        Email
                                    </label>
                                    <input
                                        type="email"
                                        value={groupInviteEmail}
                                        onChange={(e) =>
                                            setGroupInviteEmail(e.target.value)
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
                                        value={groupInviteRole}
                                        onChange={(e) =>
                                            setGroupInviteRole(
                                                e.target.value as GroupRole
                                            )
                                        }
                                        className="w-full border border-slate-300 rounded px-3 py-2"
                                    >
                                        <option value="viewer">Viewer</option>
                                        <option value="agent">Agent</option>
                                        <option value="manager">Manager</option>
                                        <option value="admin">Admin</option>
                                        <option value="owner">Owner</option>
                                    </select>
                                </div>
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button
                                    onClick={handleInviteGroupMember}
                                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                                >
                                    Send Invite
                                </button>
                                <button
                                    onClick={closeGroupModals}
                                    className="flex-1 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300 transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
