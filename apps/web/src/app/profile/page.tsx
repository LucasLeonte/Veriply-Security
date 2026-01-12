"use client";

import Image from "next/image";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/DashboardLayout";
import { getAccessToken, clearAccessToken } from "@/lib/auth";

interface UserProfile {
    id: string;
    email: string;
    name?: string;
    avatar_url?: string;
    notification_frequency: "daily" | "weekly" | "never";
    role: string;
    last_active?: string;
    is_active: string;
}

export default function ProfilePage() {
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState<{
        name: string;
        notification_frequency: "daily" | "weekly" | "never";
    }>({
        name: "",
        notification_frequency: "weekly",
    });
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [deleting, setDeleting] = useState(false);
    const [exporting, setExporting] = useState(false);

    useEffect(() => {
        fetchProfile();
    }, []);

    const fetchProfile = async () => {
        try {
            setLoading(true);
            const token = getAccessToken();

            if (!token) {
                setError("Not authenticated. Please log in.");
                setLoading(false);
                setTimeout(() => {
                    window.location.href = "/login";
                }, 1000);
                return;
            }

            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

            const response = await fetch(`${apiUrl}/api/v1/profile/me`, {
                method: "GET",
                credentials: "include",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    setError(
                        "Your session is invalid. This usually happens when the server was restarted. Please log in again."
                    );
                    clearAccessToken();
                    return;
                }
                const errorData = await response.json();
                setError(errorData.detail || "Failed to load profile");
                setSuccessMessage(null);
                return;
            }

            const data = await response.json();
            setProfile(data);
            setFormData({
                name: data.name || "",
                notification_frequency: data.notification_frequency || "weekly",
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
            setSuccessMessage(null);
        } finally {
            setLoading(false);
        }
    };

    const handleInputChange = (
        e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
    ) => {
        const { name, value } = e.target;
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }));
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setError(null);
            setSuccessMessage(null);

            // Validate name
            if (
                formData.name &&
                (formData.name.length < 2 || formData.name.length > 100)
            ) {
                setError("Name must be between 2 and 100 characters");
                return;
            }

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                return;
            }

            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const response = await fetch(`${apiUrl}/api/v1/profile/me`, {
                method: "PUT",
                credentials: "include",
                headers: {
                    Authorization: `Bearer ${token}`,
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    name: formData.name || null,
                    notification_frequency: formData.notification_frequency,
                }),
            });

            if (!response.ok) {
                if (response.status === 401) {
                    setError("Session expired. Please log in again.");
                    clearAccessToken();
                    window.location.href = "/login";
                    return;
                }
                const errorData = await response.json();
                setError(errorData.detail || "Failed to update profile");
                return;
            }

            const updatedProfile = await response.json();
            setProfile(updatedProfile);
            setSuccessMessage("Profile updated successfully");
            setIsEditing(false);

            // Clear success message after 3 seconds
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        }
    };

    const handleAvatarUpload = async (
        e: React.ChangeEvent<HTMLInputElement>
    ) => {
        try {
            if (!e.target.files?.[0]) return;

            const file = e.target.files[0];

            // Validate file
            const maxSize = 5 * 1024 * 1024; // 5MB
            const allowedTypes = ["image/jpeg", "image/png", "image/webp"];

            if (file.size > maxSize) {
                setError("File size must be less than 5MB");
                return;
            }

            if (!allowedTypes.includes(file.type)) {
                setError("Only JPG, PNG, and WebP images are allowed");
                return;
            }

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                return;
            }

            // Use FormData for efficient multipart/form-data upload
            // This is the recommended approach for file uploads:
            // - Memory efficient: No base64 encoding overhead
            // - Standard: Uses HTTP multipart/form-data specification
            // - Scalable: Handles large files better than data URLs
            const formData = new FormData();
            formData.append("file", file);

            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const response = await fetch(`${apiUrl}/api/v1/profile/avatar`, {
                method: "POST",
                credentials: "include",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData, // FormData automatically sets Content-Type: multipart/form-data
            });

            if (!response.ok) {
                if (response.status === 401) {
                    setError("Session expired. Please log in again.");
                    clearAccessToken();
                    window.location.href = "/login";
                    return;
                }
                const errorData = await response.json();
                setError(errorData.detail || "Avatar upload failed");
                return;
            }

            const result = await response.json();

            // Update profile with new avatar URL from server
            if (profile && result.avatar_url) {
                setProfile({
                    ...profile,
                    avatar_url: result.avatar_url,
                });
            }
            setSuccessMessage("Avatar updated successfully");
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Avatar upload failed"
            );
        }
    };

    const handleDeleteAccount = async () => {
        if (deleting) return;
        const confirmed = window.confirm(
            "This will permanently delete your account and personal data. This cannot be undone. Continue?"
        );
        if (!confirmed) return;

        try {
            setDeleting(true);
            setError(null);
            setSuccessMessage(null);

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                return;
            }

            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const response = await fetch(`${apiUrl}/api/v1/profile/me`, {
                method: "DELETE",
                credentials: "include",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    setError("Session expired. Please log in again.");
                    clearAccessToken();
                    window.location.href = "/login";
                    return;
                }
                const errorData = await response.json();
                setError(
                    errorData.detail ||
                        "Failed to delete account. Please try again."
                );
                return;
            }

            setSuccessMessage(
                "Account deleted. Signing you out and clearing personal data..."
            );
            clearAccessToken();
            setTimeout(() => {
                window.location.href = "/login";
            }, 1200);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to delete account."
            );
        } finally {
            setDeleting(false);
        }
    };

    const handleExportData = async () => {
        if (exporting) return;
        try {
            setExporting(true);
            setError(null);
            setSuccessMessage(null);

            const token = getAccessToken();
            if (!token) {
                setError("Not authenticated. Please log in.");
                return;
            }

            const apiUrl =
                process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
            const response = await fetch(`${apiUrl}/api/v1/profile/me/export`, {
                method: "GET",
                credentials: "include",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!response.ok) {
                if (response.status === 401) {
                    setError("Session expired. Please log in again.");
                    clearAccessToken();
                    window.location.href = "/login";
                    return;
                }
                // Try to capture and display any validation or error payload (e.g., 422 details)
                const text = await response.text();
                let message = text;
                try {
                    const parsed = JSON.parse(text);
                    // If the backend returned a structured error, try to extract useful info
                    if (parsed.detail) {
                        message =
                            typeof parsed.detail === "string"
                                ? parsed.detail
                                : JSON.stringify(parsed.detail);
                    } else if (parsed.message) {
                        message = parsed.message;
                    } else {
                        message = JSON.stringify(parsed);
                    }
                } catch (_) {
                    // not JSON, keep raw text
                }
                console.error("Export failed", response.status, message);
                setError(
                    `Export failed (${response.status}): ${message}` ||
                        "Failed to export data"
                );
                return;
            }

            const blob = await response.blob();

            // Try to extract filename from Content-Disposition header
            let filename = "veriply_data_export.json";
            const cd =
                response.headers.get("Content-Disposition") ||
                response.headers.get("content-disposition");
            if (cd) {
                const match = cd.match(/filename\*?=([^;]+)/);
                if (match) {
                    filename = match[1].replace(/\"/g, "").trim();
                }
            }

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            setSuccessMessage(
                "Your data export has started. Check your downloads folder."
            );
            setTimeout(() => setSuccessMessage(null), 4000);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "Failed to export data"
            );
        } finally {
            setExporting(false);
        }
    };

    if (loading) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <p className="text-gray-600">Loading profile...</p>
                </div>
            </DashboardLayout>
        );
    }

    if (!profile) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <p className="text-red-600">Failed to load profile</p>
                </div>
            </DashboardLayout>
        );
    }

    return (
        <DashboardLayout>
            <div className="max-w-2xl mx-auto p-6">
                <h1 className="text-3xl font-bold mb-8 text-gray-900">
                    Profile Settings
                </h1>

                {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-red-800 font-medium mb-2">{error}</p>
                        <button
                            onClick={() => (window.location.href = "/login")}
                            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition text-sm"
                        >
                            Go to Login
                        </button>
                    </div>
                )}

                {successMessage && (
                    <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
                        {successMessage}
                    </div>
                )}

                {/* Avatar Section */}
                <div className="mb-8 p-6 bg-white rounded-lg border border-gray-200">
                    <h2 className="text-xl font-semibold mb-4 text-gray-800">
                        Avatar
                    </h2>
                    <div className="flex items-center gap-6">
                        <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden relative">
                            {profile.avatar_url ? (
                                <Image
                                    src={profile.avatar_url}
                                    alt={profile.name || "Avatar"}
                                    width={96}
                                    height={96}
                                    className="object-cover rounded-full"
                                />
                            ) : (
                                <span className="text-2xl text-gray-500">
                                    👤
                                </span>
                            )}
                        </div>
                        <div className="flex-1">
                            <label className="inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition">
                                Change Avatar
                                <input
                                    type="file"
                                    accept="image/jpeg,image/png,image/webp"
                                    onChange={handleAvatarUpload}
                                    className="hidden"
                                    disabled={loading}
                                />
                            </label>
                            <p className="mt-2 text-sm text-gray-600">
                                JPG, PNG, or WebP up to 5MB
                            </p>
                        </div>
                    </div>
                </div>

                {/* Profile Form */}
                <div className="p-6 bg-white rounded-lg border border-gray-200">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-semibold text-gray-800">
                            Account Information
                        </h2>
                        {!isEditing && (
                            <button
                                onClick={() => setIsEditing(true)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                            >
                                Edit
                            </button>
                        )}
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Email (Read-only) */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Email
                            </label>
                            <input
                                type="email"
                                value={profile.email}
                                readOnly
                                className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-600"
                            />
                        </div>

                        {/* Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Full Name
                            </label>
                            <input
                                type="text"
                                name="name"
                                value={formData.name}
                                onChange={handleInputChange}
                                readOnly={!isEditing}
                                placeholder="Enter your full name"
                                className={`w-full px-3 py-2 border rounded-lg ${
                                    isEditing
                                        ? "border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                        : "bg-gray-100 border-gray-300 text-gray-600"
                                }`}
                            />
                            <p className="mt-1 text-xs text-gray-500">
                                2-100 characters
                            </p>
                        </div>

                        {/* Role (Read-only) */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Role
                            </label>
                            <input
                                type="text"
                                value={
                                    profile.role
                                        ? profile.role.charAt(0).toUpperCase() +
                                          profile.role.slice(1)
                                        : ""
                                }
                                readOnly
                                className="w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-gray-600 capitalize"
                            />
                        </div>

                        {/* Notification Frequency */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Email Notifications
                            </label>
                            <select
                                name="notification_frequency"
                                value={formData.notification_frequency}
                                onChange={handleInputChange}
                                disabled={!isEditing}
                                className={`w-full px-3 py-2 border rounded-lg ${
                                    isEditing
                                        ? "border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                                        : "bg-gray-100 border-gray-300 text-gray-600"
                                }`}
                            >
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="never">Never</option>
                            </select>
                        </div>

                        {/* Action Buttons */}
                        {isEditing && (
                            <div className="flex gap-3 pt-4">
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
                                >
                                    Save Changes
                                </button>
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsEditing(false);
                                        setFormData({
                                            name: profile.name || "",
                                            notification_frequency:
                                                profile.notification_frequency,
                                        });
                                    }}
                                    className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
                                >
                                    Cancel
                                </button>
                            </div>
                        )}
                    </form>
                </div>

                {/* Export Data */}
                <div className="mt-8 p-6 bg-white border border-gray-200 rounded-lg">
                    <p className="text-sm text-gray-700 mb-4">
                        Export a copy of your personal data in JSON format. This
                        includes your profile, group memberships, integrations,
                        HITL activities, and recent audit logs.
                    </p>
                    <button
                        onClick={handleExportData}
                        disabled={exporting}
                        className={`px-4 py-2 rounded-lg text-white font-semibold transition ${
                            exporting
                                ? "bg-blue-300 cursor-not-allowed"
                                : "bg-blue-600 hover:bg-blue-700"
                        }`}
                    >
                        {exporting ? "Exporting..." : "Export my data"}
                    </button>
                </div>

                {/* Delete Account */}
                <div className="mt-8 p-6 bg-white border border-red-200 rounded-lg">
                    <p className="text-sm text-red-700 mb-4">
                        Delete your account and personal data. Requires another
                        tenant owner/admin before deletion. If permitted, your
                        integrations, memberships, audit logs, and personal
                        identifiers are removed or anonymized, and your bots and
                        documents are deleted rather than reassigned. This
                        action is permanent and cannot be undone.
                    </p>
                    <button
                        onClick={handleDeleteAccount}
                        disabled={deleting}
                        className={`px-4 py-2 rounded-lg text-white font-semibold transition ${
                            deleting
                                ? "bg-red-300 cursor-not-allowed"
                                : "bg-red-600 hover:bg-red-700"
                        }`}
                    >
                        {deleting ? "Deleting..." : "Delete my account"}
                    </button>
                </div>
            </div>
        </DashboardLayout>
    );
}
