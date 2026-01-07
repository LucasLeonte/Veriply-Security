"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components";
import { getAccessToken, clearAccessToken } from "@/lib/auth";

interface TeamMember {
    id: string;
    email: string;
    name?: string;
    role: string;
    last_active?: string;
    is_active: string;
}

export default function SettingsPage() {
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

    useEffect(() => {
        fetchInitialData();
    }, []);

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
                        You do not have permission to manage team members. Only
                        Owners and Admins can manage the team.
                    </div>
                )}

                {/* Invite Member Button */}
                {canManageTeam && (
                    <div className="mb-6">
                        <button
                            onClick={() => setShowInviteModal(true)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
                        >
                            + Invite Team Member
                        </button>
                    </div>
                )}

                {/* Team Members Table */}
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
                                        No team members found
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
            </div>
        </DashboardLayout>
    );
}
