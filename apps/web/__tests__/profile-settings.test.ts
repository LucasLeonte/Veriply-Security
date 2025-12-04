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

    expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows validation error when email is missing', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
  });

  it('shows validation error when password is missing', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText(/email/i);
    await user.type(emailInput, 'test@example.com');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
  });

  it('shows validation error for invalid email format', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    await user.type(emailInput, 'invalid-email');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/valid email address/i)).toBeInTheDocument();
  });

  it('shows validation error for short password', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'short');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument();
  });

  it('submits login form with valid credentials and calls API', async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({ message: 'Success' }),
    });

    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/v1/auth/register',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('test@example.com'),
        })
      );
    });
  });

  it('displays error message when API call fails', async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Invalid credentials' }),
    });

    render(<LoginPage />);

    const emailInput = screen.getByPlaceholderText(/email/i);
    const passwordInput = screen.getByPlaceholderText(/password/i);

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    await user.click(submitButton);

    expect(await screen.findByText(/invalid credentials/i)).toBeInTheDocument();
  });

  it('toggles password visibility when eye icon is clicked', async () => {
    const user = userEvent.setup();
    render(<LoginPage />);

    const passwordInput = screen.getByPlaceholderText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');

    // Find and click the toggle button (look for Eye icon button)
    const toggleButtons = screen.getAllByRole('button');
    const toggleButton = toggleButtons.find(btn => btn !== screen.getByRole('button', { name: /sign in/i }));
    
    if (toggleButton) {
      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'text');

      await user.click(toggleButton);
      expect(passwordInput).toHaveAttribute('type', 'password');
    }
  });
});

describe('Profile Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  it('displays loading state initially', () => {
    render(<ProfilePage />);
    expect(screen.getByText(/loading profile/i)).toBeInTheDocument();
  });

  it('renders profile information after loading', async () => {
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
      expect(screen.getByDisplayValue(/john doe/i)).toBeInTheDocument();
      expect(screen.getByText(/user@example\.com/i)).toBeInTheDocument();
    });
  });

  it('enables edit mode when edit button is clicked', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /edit profile/i });
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
    const editButton = screen.getByRole('button', { name: /edit profile/i });
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
    const editButton = screen.getByRole('button', { name: /edit profile/i });
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
    const editButton = screen.getByRole('button', { name: /edit profile/i });
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
    const editButton = screen.getByRole('button', { name: /edit profile/i });
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

  it('validates file type when uploading avatar', async () => {
    const user = userEvent.setup();
    render(<ProfilePage />);

    await waitFor(() => {
      expect(screen.getByText(/profile settings/i)).toBeInTheDocument();
    });

    // Create invalid file (PDF)
    const invalidFile = new File(['test'], 'test.pdf', { type: 'application/pdf' });

    // Find file input
    const fileInput = screen.getByLabelText(/change avatar/i);
    await user.upload(fileInput, invalidFile);

    expect(await screen.findByText(/only jpg, png, and webp/i)).toBeInTheDocument();
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

    expect(await screen.findByText(/less than 5mb/i)).toBeInTheDocument();
  });

  it('successfully uploads valid avatar image', async () => {
    const user = userEvent.setup();
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => ({
        avatar_url: 'https://example.com/avatar.jpg',
        filename: 'avatar.jpg',
        size_bytes: 1024,
      }),
    });

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
        '/api/v1/profile/avatar',
        expect.objectContaining({
          method: 'POST',
          credentials: 'include',
        })
      );
    });

    expect(await screen.findByText(/profile updated successfully/i)).toBeInTheDocument();
  });
});
