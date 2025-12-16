"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useGroup } from "@/contexts/GroupContext";
import { groupsApi } from "@/lib/api/groups";
import { Users, Plus, ArrowRight, LogOut } from "lucide-react";
import { getAccessToken, clearAccessToken } from "@/lib/auth";

export default function GroupSelectionPage() {
    const router = useRouter();
    const { groups, setCurrentGroup, refreshGroups } = useGroup();
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [newGroupName, setNewGroupName] = useState("");
    const [newGroupDescription, setNewGroupDescription] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Check if user is authenticated
        const token = getAccessToken();
        if (!token) {
            router.push("/login");
            return;
        }

        // Fetch groups with error handling
        refreshGroups().catch((err) => {
            console.error("Failed to load groups:", err);
            setError("Failed to load groups. Please try again.");
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleCreateGroup = async () => {
        if (!newGroupName.trim()) {
            setError("Group name is required");
            return;
        }

        setLoading(true);
        setError(null);

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
            // Redirect to dashboard with selected group
            router.push("/dashboard");
        } catch (err) {
            console.error("Failed to create group:", err);
            setError(
                err instanceof Error ? err.message : "Failed to create group"
            );
        } finally {
            setLoading(false);
        }
    };

    const handleSelectGroup = (group: any) => {
        setCurrentGroup(group);
        router.push("/dashboard");
    };

    const handleLogout = () => {
        clearAccessToken();
        router.push("/login");
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute -top-40 -right-40 w-80 h-80 bg-sky-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
                <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
                <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-slate-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
            </div>

            {/* Main Card */}
            <div className="relative w-full max-w-2xl">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center gap-2 mb-4">
                        <div className="w-10 h-10 rounded-lg bg-sky-500 flex items-center justify-center shadow-lg">
                            <span className="text-white text-lg font-bold">
                                V
                            </span>
                        </div>
                        <h1 className="text-3xl font-bold text-slate-900">
                            Veriply
                        </h1>
                    </div>
                    <p className="text-slate-600">
                        Select or create a group to continue
                    </p>
                </div>

                {/* Groups Card */}
                <div className="bg-white rounded-lg shadow-lg border border-slate-200 overflow-hidden backdrop-blur-sm bg-white/90">
                    {/* Card Header */}
                    <div className="p-6 border-b border-slate-200 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Users className="h-5 w-5 text-slate-600" />
                            <h2 className="text-lg font-semibold text-slate-900">
                                Your Groups
                            </h2>
                        </div>
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="flex items-center gap-2 px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition text-sm font-medium shadow-sm"
                        >
                            <Plus className="h-4 w-4" />
                            Create Group
                        </button>
                    </div>

                    {/* Groups List */}
                    <div className="divide-y divide-slate-200">
                        {groups.length === 0 ? (
                            <div className="p-12 text-center">
                                <Users className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                                <p className="text-slate-600 mb-4">
                                    No groups yet
                                </p>
                                <button
                                    onClick={() => setShowCreateModal(true)}
                                    className="text-sky-600 hover:text-sky-700 font-medium text-sm"
                                >
                                    Create your first group to get started
                                </button>
                            </div>
                        ) : (
                            groups.map((group) => (
                                <div
                                    key={group.id}
                                    onClick={() => handleSelectGroup(group)}
                                    className="p-6 hover:bg-slate-50 cursor-pointer transition group"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <h3 className="font-semibold text-slate-900 mb-1">
                                                {group.name}
                                            </h3>
                                            {group.description && (
                                                <p className="text-sm text-slate-600">
                                                    {group.description}
                                                </p>
                                            )}
                                        </div>
                                        <ArrowRight className="h-5 w-5 text-slate-400 group-hover:text-sky-500 group-hover:translate-x-1 transition" />
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    {/* Footer */}
                    <div className="p-4 bg-slate-50 border-t border-slate-200">
                        <button
                            onClick={handleLogout}
                            className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition mx-auto"
                        >
                            <LogOut className="h-4 w-4" />
                            Sign out
                        </button>
                    </div>
                </div>
            </div>

            {/* Create Group Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
                        <h3 className="text-xl font-semibold text-slate-900 mb-4">
                            Create New Group
                        </h3>

                        {error && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
                                {error}
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Group Name
                                </label>
                                <input
                                    type="text"
                                    value={newGroupName}
                                    onChange={(e) =>
                                        setNewGroupName(e.target.value)
                                    }
                                    placeholder="Engineering Team"
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                                    disabled={loading}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Description (optional)
                                </label>
                                <textarea
                                    value={newGroupDescription}
                                    onChange={(e) =>
                                        setNewGroupDescription(e.target.value)
                                    }
                                    placeholder="What is this group for?"
                                    rows={3}
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none"
                                    disabled={loading}
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => {
                                    setShowCreateModal(false);
                                    setError(null);
                                    setNewGroupName("");
                                    setNewGroupDescription("");
                                }}
                                className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition"
                                disabled={loading}
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreateGroup}
                                className="flex-1 px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition disabled:opacity-50"
                                disabled={loading}
                            >
                                {loading ? "Creating..." : "Create Group"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <style jsx>{`
                @keyframes blob {
                    0%,
                    100% {
                        transform: translate(0, 0) scale(1);
                    }
                    33% {
                        transform: translate(30px, -50px) scale(1.1);
                    }
                    66% {
                        transform: translate(-20px, 20px) scale(0.9);
                    }
                }
                .animate-blob {
                    animation: blob 7s infinite;
                }
                .animation-delay-2000 {
                    animation-delay: 2s;
                }
                .animation-delay-4000 {
                    animation-delay: 4s;
                }
            `}</style>
        </div>
    );
}
