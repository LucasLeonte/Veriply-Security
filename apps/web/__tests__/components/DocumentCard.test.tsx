import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DocumentCard } from '@/components/kb/DocumentCard';
import { Document } from '@/types/document';

describe('DocumentCard', () => {
    const mockDocument: Document = {
        id: '123',
        bot_id: 'bot-456',
        group_id: 'group-789',
        uploader_id: 'user-123',
        filename: 'test-document.pdf',
        mime: 'application/pdf',
        size: 1024000, // 1000 KB
        storage_path: '/docs/test-document.pdf',
        status: 'processed',
        chunk_count: 10,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        tenant_id: 'tenant-123',
    };

    const mockHandlers = {
        onView: vi.fn(),
        onDelete: vi.fn(),
        onReprocess: vi.fn(),
    };

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('renders document information correctly', () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
        expect(screen.getByText('Processed')).toBeInTheDocument();
        expect(screen.getByText('10 chunks')).toBeInTheDocument();
        expect(screen.getByText('1000.0 KB')).toBeInTheDocument();
    });

    it('displays correct status for pending document', () => {
        const pendingDoc = { ...mockDocument, status: 'pending' as const };
        render(<DocumentCard document={pendingDoc} {...mockHandlers} />);

        expect(screen.getByText('Pending')).toBeInTheDocument();
    });

    it('displays correct status for processing document', () => {
        const processingDoc = { 
            ...mockDocument, 
            status: 'processing' as const,
            processing_progress: 50 
        };
        render(<DocumentCard document={processingDoc} {...mockHandlers} />);

        expect(screen.getByText('Processing 50%')).toBeInTheDocument();
    });

    it('displays correct status for failed document', () => {
        const failedDoc = { 
            ...mockDocument, 
            status: 'failed' as const,
            error_message: 'Failed to process'
        };
        render(<DocumentCard document={failedDoc} {...mockHandlers} />);

        expect(screen.getByText('Failed')).toBeInTheDocument();
        expect(screen.getByText(/Error: Failed to process/)).toBeInTheDocument();
    });

    it('calls onView when filename is clicked', () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        const filename = screen.getByText('test-document.pdf');
        fireEvent.click(filename);

        expect(mockHandlers.onView).toHaveBeenCalledWith(mockDocument);
    });

    it('opens menu when clicking more actions button', async () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        const menuButton = screen.getByLabelText(/Actions for test-document.pdf/i);
        fireEvent.click(menuButton);

        await waitFor(() => {
            expect(screen.getByText('View Details')).toBeInTheDocument();
            expect(screen.getByText('Reprocess')).toBeInTheDocument();
            expect(screen.getByText('Delete')).toBeInTheDocument();
        });
    });

    it('calls onDelete when delete is clicked', async () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        const menuButton = screen.getByLabelText(/Actions for test-document.pdf/i);
        fireEvent.click(menuButton);

        const deleteButton = await screen.findByText('Delete');
        fireEvent.click(deleteButton);

        expect(mockHandlers.onDelete).toHaveBeenCalledWith(mockDocument);
    });

    it('calls onReprocess when reprocess is clicked', async () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        const menuButton = screen.getByLabelText(/Actions for test-document.pdf/i);
        fireEvent.click(menuButton);

        const reprocessButton = await screen.findByText('Reprocess');
        fireEvent.click(reprocessButton);

        expect(mockHandlers.onReprocess).toHaveBeenCalledWith(mockDocument);
    });

    it('does not show reprocess button for processing documents', async () => {
        const processingDoc = { ...mockDocument, status: 'processing' as const };
        render(<DocumentCard document={processingDoc} {...mockHandlers} />);

        const menuButton = screen.getByLabelText(/Actions for test-document.pdf/i);
        fireEvent.click(menuButton);

        await waitFor(() => {
            expect(screen.queryByText('Reprocess')).not.toBeInTheDocument();
        });
    });

    it('closes menu when clicking outside', async () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        const menuButton = screen.getByLabelText(/Actions for test-document.pdf/i);
        fireEvent.click(menuButton);

        const backdrop = document.querySelector('.fixed.inset-0');
        expect(backdrop).toBeInTheDocument();

        fireEvent.click(backdrop!);

        await waitFor(() => {
            expect(screen.queryByText('View Details')).not.toBeInTheDocument();
        });
    });

    it('formats upload date correctly', () => {
        render(<DocumentCard document={mockDocument} {...mockHandlers} />);

        expect(screen.getByText(/Uploaded Jan 1, 2025/)).toBeInTheDocument();
    });
});
