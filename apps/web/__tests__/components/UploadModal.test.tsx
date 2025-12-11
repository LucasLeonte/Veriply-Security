import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { UploadModal } from '@/components/kb/UploadModal';

describe('UploadModal', () => {
    const mockOnClose = vi.fn();
    const mockOnUpload = vi.fn();
    const botId = 'bot-123';

    const getFileInput = () => {
        const browseButton = screen.getByRole('button', { name: /Browse Files/i });
        return browseButton.parentElement?.querySelector('input[type="file"]') as HTMLInputElement;
    };

    beforeEach(() => {
        vi.clearAllMocks();
        mockOnUpload.mockResolvedValue(undefined);
    });

    it('does not render when closed', () => {
        const { container } = render(
            <UploadModal
                isOpen={false}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        expect(container.firstChild).toBeNull();
    });

    it('renders when open', () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        expect(screen.getByText('Upload Documents')).toBeInTheDocument();
        expect(screen.getByText('Drag & drop files here')).toBeInTheDocument();
    });

    it('calls onClose when clicking cancel', () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const cancelButton = screen.getByText('Cancel');
        fireEvent.click(cancelButton);

        expect(mockOnClose).toHaveBeenCalled();
    });

    it('shows file validation error for unsupported file type', async () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.exe', { type: 'application/x-executable' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);

        await waitFor(() => {
            expect(screen.getByText(/Unsupported file type/)).toBeInTheDocument();
        });
    });

    it('shows file validation error for large file', async () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        // Create a file larger than 10MB
        const largeContent = 'x'.repeat(11 * 1024 * 1024);
        const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);

        await waitFor(() => {
            expect(screen.getByText(/File too large/)).toBeInTheDocument();
        });
    });

    it('accepts valid files', async () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);

        await waitFor(() => {
            expect(screen.getByText('test.pdf')).toBeInTheDocument();
        });
    });

    it('removes file when clicking remove button', async () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);

        await waitFor(() => {
            expect(screen.getByText('test.pdf')).toBeInTheDocument();
        });

        const removeButton = screen.getByLabelText(/Remove file/);
        fireEvent.click(removeButton);

        await waitFor(() => {
            expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
        });
    });

    it('calls onUpload with files when clicking upload', async () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);

        await waitFor(() => {
            expect(screen.getByText('test.pdf')).toBeInTheDocument();
        });

        const uploadButton = screen.getByRole('button', { name: /Upload 1 file/ });
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(mockOnUpload).toHaveBeenCalledWith([file]);
        });
    });

    it('closes modal after successful upload', async () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);
        const uploadButton = screen.getByRole('button', { name: /Upload 1 file/ });
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(mockOnClose).toHaveBeenCalled();
        });
    });

    it('shows upload error when onUpload fails', async () => {
        mockOnUpload.mockRejectedValue(new Error('Upload failed'));

        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);
        const uploadButton = screen.getByRole('button', { name: /Upload 1 file/ });
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(screen.getByText(/Upload failed/)).toBeInTheDocument();
        });
    });

    it('disables upload button when no files selected', () => {
        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const uploadButton = screen.getByRole('button', { name: /Upload/ });
        expect(uploadButton).toBeDisabled();
    });

    it('shows uploading state during upload', async () => {
        let resolveUpload: () => void;
        const uploadPromise = new Promise<void>((resolve) => {
            resolveUpload = resolve;
        });
        mockOnUpload.mockReturnValue(uploadPromise);

        render(
            <UploadModal
                isOpen={true}
                onClose={mockOnClose}
                onUpload={mockOnUpload}
                botId={botId}
            />
        );

        const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });
        const input = getFileInput();

        Object.defineProperty(input, 'files', {
            value: [file],
            writable: false,
        });

        fireEvent.change(input);
        const uploadButton = screen.getByRole('button', { name: /Upload 1 file/ });
        fireEvent.click(uploadButton);

        await waitFor(() => {
            expect(screen.getByText('Uploading...')).toBeInTheDocument();
        });

        resolveUpload!();
    });
});
