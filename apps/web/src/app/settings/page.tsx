'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardLayout } from '@/components';

interface TeamMember {
  id: string;
  email: string;
  name?: string;
  role: string;
  last_active?: string;
  is_active: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [currentUserRole, setCurrentUserRole] = useState<string>('');
  const [showRoleMenu, setShowRoleMenu] = useState<string | null>(null);

  useEffect(() => {
    fetchTeamMembers();
    getCurrentUserRole();
  }, []);

  const fetchTeamMembers = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch('/api/v1/profile/team/members', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          router.push('/login');
          return;
        }
        throw new Error('Failed to fetch team members');
      }

      const data = await response.json();
      setMembers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getCurrentUserRole = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('/api/v1/profile/me', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentUserRole(data.role);
      }
    } catch (err) {
      console.error('Failed to get current user role', err);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (
      !confirm(
        'Are you sure you want to remove this team member? They will lose access immediately.'
      )
    ) {
      return;
    }

    try {
      setError(null);
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(`/api/v1/profile/team/members/${memberId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to remove member');
      }

      setMembers((prev) =>
        prev.map((m) =>
          m.id === memberId ? { ...m, is_active: 'inactive' } : m
        )
      );
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleChangeRole = async (memberId: string, newRole: string) => {
    try {
      setError(null);
      const token = localStorage.getItem('access_token');
      if (!token) {
        router.push('/login');
        return;
      }

      const response = await fetch(
        `/api/v1/profile/team/members/${memberId}/role`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ role: newRole }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to change role');
      }

      const updatedMember = await response.json();
      setMembers((prev) =>
        prev.map((m) => (m.id === memberId ? updatedMember : m))
      );
      setShowRoleMenu(null);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const canManageTeam = currentUserRole === 'owner' || currentUserRole === 'admin';
  const roleOptions = ['owner', 'admin', 'manager', 'agent', 'viewer'];
  const ownerCount = members.filter(
    (m) => m.role === 'owner' && m.is_active === 'active'
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
        <h1 className="text-3xl font-bold mb-8 text-slate-900">Team Settings</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            Team member updated successfully
          </div>
        )}

        {!canManageTeam && (
          <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800">
            You do not have permission to manage team members. Only Owners and Admins can manage the team.
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
                      member.is_active === 'inactive' ? 'opacity-50' : ''
                    }`}
                  >
                    <td className="px-6 py-4 text-sm text-slate-800">
                      {member.name || 'N/A'}
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
                                showRoleMenu === member.id ? null : member.id
                              )
                            }
                            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm hover:bg-blue-200 transition"
                          >
                            {member.role}
                          </button>
                          {showRoleMenu === member.id && (
                            <div className="absolute z-10 mt-1 w-40 bg-white border border-slate-200 rounded-lg shadow-lg">
                              {roleOptions.map((role) => (
                                <button
                                  key={role}
                                  onClick={() =>
                                    handleChangeRole(member.id, role)
                                  }
                                  disabled={
                                    member.role === 'owner' &&
                                    role !== 'owner' &&
                                    ownerCount === 1
                                  }
                                  className={`w-full text-left px-4 py-2 text-sm hover:bg-slate-100 ${
                                    member.role === role
                                      ? 'bg-blue-50 font-semibold'
                                      : ''
                                  } ${
                                    member.role === 'owner' &&
                                    role !== 'owner' &&
                                    ownerCount === 1
                                      ? 'opacity-50 cursor-not-allowed'
                                      : ''
                                  }`}
                                >
                                  {role}
                                </button>
                              ))}
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
                        ? new Date(member.last_active).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {canManageTeam && (
                        <button
                          onClick={() => handleRemoveMember(member.id)}
                          disabled={member.role === 'owner' && ownerCount === 1}
                          className={`px-3 py-1 text-red-600 hover:bg-red-50 rounded transition ${
                            member.role === 'owner' && ownerCount === 1
                              ? 'opacity-50 cursor-not-allowed'
                              : ''
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
      </div>
    </DashboardLayout>
  );
}
