'use client';

import Image from 'next/image';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/DashboardLayout';

interface UserProfile {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  notification_frequency: 'daily' | 'weekly' | 'never';
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
    notification_frequency: 'daily' | 'weekly' | 'never';
  }>({
    name: '',
    notification_frequency: 'weekly',
  });
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      // Mock profile for testing - in production, this would use actual API
      const mockProfile: UserProfile = {
        id: '123e4567-e89b-12d3-a456-426614174000',
        email: 'user@example.com',
        name: 'John Doe',
        avatar_url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=John',
        notification_frequency: 'weekly',
        role: 'owner',
        last_active: new Date().toISOString(),
        is_active: 'active',
      };

      setProfile(mockProfile);
      setFormData({
        name: mockProfile.name || '',
        notification_frequency: mockProfile.notification_frequency || 'weekly',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
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
      setSuccess(false);

      // Validate name
      if (formData.name && (formData.name.length < 2 || formData.name.length > 100)) {
        setError('Name must be between 2 and 100 characters');
        return;
      }

      // Mock API response for testing
      const updatedProfile: UserProfile = {
        ...profile!,
        ...formData,
      };
      setProfile(updatedProfile);
      setSuccess(true);
      setIsEditing(false);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    try {
      if (!e.target.files?.[0]) return;

      const file = e.target.files[0];

      // Validate file
      const maxSize = 5 * 1024 * 1024; // 5MB
      const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];

      if (file.size > maxSize) {
        setError('File size must be less than 5MB');
        return;
      }

      if (!allowedTypes.includes(file.type)) {
        setError('Only JPG, PNG, and WebP images are allowed');
        return;
      }

      // Use FormData for efficient multipart/form-data upload
      // This is the recommended approach for file uploads:
      // - Memory efficient: No base64 encoding overhead
      // - Standard: Uses HTTP multipart/form-data specification
      // - Scalable: Handles large files better than data URLs
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/v1/profile/avatar', {
        method: 'POST',
        credentials: 'include', // Include httpOnly cookies
        body: formData, // FormData automatically sets Content-Type: multipart/form-data
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.detail || 'Avatar upload failed');
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
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Avatar upload failed');
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
        <h1 className="text-3xl font-bold mb-8 text-gray-900">Profile Settings</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            Profile updated successfully
          </div>
        )}

        {/* Avatar Section */}
        <div className="mb-8 p-6 bg-white rounded-lg border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 text-gray-800">Avatar</h2>
          <div className="flex items-center gap-6">
            <div className="w-24 h-24 bg-gray-200 rounded-full flex items-center justify-center overflow-hidden">
              {profile.avatar_url ? (
                <Image
                  src={profile.avatar_url}
                  alt={profile.name || 'Avatar'}
                  fill
                  className="object-cover"
                  sizes="96px"
                />
              ) : (
                <span className="text-2xl text-gray-500">👤</span>
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
            <h2 className="text-xl font-semibold text-gray-800">Account Information</h2>
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
                className={`w-full px-3 py-2 border rounded-lg ${isEditing
                  ? 'border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
                  : 'bg-gray-100 border-gray-300 text-gray-600'
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
                value={profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
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
                className={`w-full px-3 py-2 border rounded-lg ${isEditing
                  ? 'border-gray-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500'
                  : 'bg-gray-100 border-gray-300 text-gray-600'
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
                      name: profile.name || '',
                      notification_frequency: profile.notification_frequency,
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
      </div>
    </DashboardLayout>
  );
}
