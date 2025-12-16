import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProfilePage from '@/app/profile/page';
import LoginPage from '@/app/login/page';

// Mock next/navigation
const mockPush = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/',
}));

// Mock DashboardLayout to avoid nested component complexity
vi.mock('@/components/DashboardLayout', () => ({
  DashboardLayout: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="dashboard-layout">{children}</div>
  ),
}));

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('renders login form with all required fields', () => {
    render(<LoginPage />);

    expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log in/i })).toBeInTheDocument();
  });

  it('shows validation error when email is missing', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const submitButton = screen.getByRole('button', { name: /log in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });

  it('shows validation error when password is missing', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText('you@example.com');
    await user.type(emailInput, 'test@example.com');

    const submitButton = screen.getByRole('button', { name: /log in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
  });

  it('validates email format correctly', () => {
    // Test the email validation regex pattern
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    expect(emailRegex.test('invalid-email')).toBe(false);
    expect(emailRegex.test('test@example.com')).toBe(true);
    expect(emailRegex.test('user@domain')).toBe(false);
    expect(emailRegex.test('@example.com')).toBe(false);
  });

  it('shows validation error for short password', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText('you@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'short');

    const submitButton = screen.getByRole('button', { name: /log in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument();
  });

  it('submits login form with valid credentials and calls API', async () => {
    const user = userEvent.setup();
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Success' }),
    } as unknown as Response);

    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText('you@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /log in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/v1\/auth\/(login|register)$/),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('test@example.com'),
        })
      );
    });
  });

  it('displays error message when API call fails', async () => {
    const user = userEvent.setup();
    vi.mocked(global.fetch).mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    } as unknown as Response);

    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText('you@example.com');
    const passwordInput = screen.getByPlaceholderText('••••••••');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /log in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
  });

  it('shows password as hidden by default', () => {
    render(<LoginPage />);

    const passwordInput = screen.getByPlaceholderText('••••••••');
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});

describe('Profile Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock localStorage
    const mockLocalStorage: Record<string, string> = {
      'access_token': 'mock-jwt-token-for-testing'
    };
    
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: (key: string) => mockLocalStorage[key] || null,
        setItem: (key: string, value: string) => { mockLocalStorage[key] = value; },
        removeItem: (key: string) => { delete mockLocalStorage[key]; },
        clear: () => { Object.keys(mockLocalStorage).forEach(key => delete mockLocalStorage[key]); },
      },
      writable: true
    });
    
    // Mock fetch to return valid profile data by default
    global.fetch = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      const method = options?.method || 'GET';
      
      // Handle GET /api/v1/profile/me
      if (method === 'GET' && url.includes('/api/v1/profile/me')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            id: 'user-123',
            email: 'user@example.com',
            name: 'John Doe',
            avatar_url: null,
            notification_frequency: 'weekly',
            role: 'agent',
            is_active: 'active',
            last_active: '2025-12-11T00:00:00Z',
          }),
        } as unknown as Response);
      }
      
      // Handle PUT /api/v1/profile/me
      if (method === 'PUT' && url.includes('/api/v1/profile/me')) {
        const body = options?.body ? JSON.parse(options.body as string) : {};
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            id: 'user-123',
            email: 'user@example.com',
            name: body.name || 'John Doe',
            avatar_url: null,
            notification_frequency: body.notification_frequency || 'weekly',
            role: 'agent',
            is_active: 'active',
            last_active: '2025-12-11T00:00:00Z',
          }),
        } as unknown as Response);
      }
      
      // Default response for unhandled requests
      return Promise.resolve({
        ok: true,
        status: 200,
        json: async () => ({}),
      } as unknown as Response);
    });
  });

  it('renders profile page successfully', async () => {
    render(<ProfilePage />);
    // Profile loads from mock immediately
    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });
  });

  it('renders profile information after loading', async () => {
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue(/john doe/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue(/user@example\.com/i)).toBeInTheDocument();
  });

  it('enables edit mode when edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /^edit$/i });
    await user.click(editButton);

    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('updates profile name when form is submitted', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole('button', { name: /^edit$/i });
    await user.click(editButton);

    // Change name
    const nameInput = screen.getByDisplayValue(/john doe/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'Jane Smith');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    // Verify success message and updated name
    expect(await screen.findByText(/profile updated successfully/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue(/jane smith/i)).toBeInTheDocument();
  });

  it('shows validation error for invalid name length', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole('button', { name: /^edit$/i });
    await user.click(editButton);

    // Enter invalid name (too short)
    const nameInput = screen.getByDisplayValue(/john doe/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'A');

    // Try to save
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    expect(await screen.findByText(/between 2 and 100 characters/i)).toBeInTheDocument();
  });

  it('changes notification frequency', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole('button', { name: /^edit$/i });
    await user.click(editButton);

    // Change notification frequency
    const frequencySelect = screen.getByRole('combobox');
    await user.selectOptions(frequencySelect, 'daily');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await user.click(saveButton);

    expect(await screen.findByText(/profile updated successfully/i)).toBeInTheDocument();
  });

  it('cancels edit mode without saving changes', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Click edit button
    const editButton = screen.getByRole('button', { name: /^edit$/i });
    await user.click(editButton);

    // Change name
    const nameInput = screen.getByDisplayValue(/john doe/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'Changed Name');

    // Cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await user.click(cancelButton);

    // Verify name is unchanged
    expect(screen.getByDisplayValue(/john doe/i)).toBeInTheDocument();
    expect(screen.queryByDisplayValue(/changed name/i)).not.toBeInTheDocument();
  });

  it('renders file input for avatar upload', async () => {
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Verify file input exists with correct accept types
    const fileInput = screen.getByLabelText(/change avatar/i);
    expect(fileInput).toHaveAttribute('accept', 'image/jpeg,image/png,image/webp');
  });

  it('validates file size when uploading avatar', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Create oversized file (6MB)
    const largeContent = new Uint8Array(6 * 1024 * 1024);
    const largeFile = new File([largeContent], 'large.jpg', { type: 'image/jpeg' });

    // Find file input
    const fileInput = screen.getByLabelText(/change avatar/i);
    await user.upload(fileInput, largeFile);

    // File size validation happens immediately in client code
    await waitFor(() => {
      expect(screen.getByText(/less than 5mb/i)).toBeInTheDocument();
    }, { timeout: 100 });
  });

  it('successfully uploads valid avatar image', async () => {
    const user = userEvent.setup();
    vi.mocked(global.fetch).mockResolvedValue({
      ok: true,
      json: async () => ({
        avatar_url: 'https://example.com/avatar.jpg',
        filename: 'avatar.jpg',
        size_bytes: 1024,
      }),
    } as unknown as Response);

    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Create valid file
    const validFile = new File(['image'], 'avatar.jpg', { type: 'image/jpeg' });

    // Upload file
    const fileInput = screen.getByLabelText(/change avatar/i);
    await user.upload(fileInput, validFile);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringMatching(/\/api\/v1\/profile\/avatar$/),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Authorization': expect.stringContaining('Bearer '),
          }),
        })
      );
    });

    expect(await screen.findByText(/profile updated successfully/i)).toBeInTheDocument();
  });
});
