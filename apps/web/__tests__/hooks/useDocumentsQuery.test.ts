import { describe, it, expect, vi } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useDocumentsQuery, useUploadDocuments, useDeleteDocument } from '@/hooks/useDocumentsQuery';
import { documentsApi } from '@/lib/api/documents';

// Mock the API
vi.mock('@/lib/api/documents', () => ({
    documentsApi: {
        listDocuments: vi.fn(),
        uploadDocuments: vi.fn(),
        deleteDocument: vi.fn(),
        reprocessDocument: vi.fn(),
        getDocument: vi.fn(),
        getDocumentChunks: vi.fn(),
    },
}));

describe('useDocumentsQuery', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('fetches documents successfully', async () => {
        const mockResponse = {
            documents: [
                {
                    id: '1',
                    bot_id: 'bot-1',
                    filename: 'test.pdf',
                    file_size: 1000,
                    status: 'processed' as const,
                    chunk_count: 5,
                    created_at: '2025-01-01T00:00:00Z',
                    updated_at: '2025-01-01T00:00:00Z',
                },
            ],
            total: 1,
            page: 1,
            page_size: 20,
            total_pages: 1,
        };

        vi.mocked(documentsApi.listDocuments).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useDocumentsQuery('bot-1', 1, 20));

        // Wait for loading to complete
        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.data).toEqual(mockResponse);
        expect(result.current.error).toBeNull();
    });

    it('handles fetch error', async () => {
        const mockError = new Error('Failed to fetch');
        vi.mocked(documentsApi.listDocuments).mockRejectedValue(mockError);

        const { result } = renderHook(() => useDocumentsQuery('bot-1', 1, 20));

        await waitFor(() => {
            expect(result.current.isLoading).toBe(false);
        });

        expect(result.current.error).toBeTruthy();
        expect(result.current.data).toBeNull();
    });

    it('refetches data when parameters change', async () => {
        const mockResponse = {
            documents: [],
            total: 0,
            page: 1,
            page_size: 20,
            total_pages: 0,
        };

        vi.mocked(documentsApi.listDocuments).mockResolvedValue(mockResponse);

        const { rerender } = renderHook(
            ({ botId, page }) => useDocumentsQuery(botId, page, 20),
            { initialProps: { botId: 'bot-1', page: 1 } }
        );

        await waitFor(() => {
            expect(documentsApi.listDocuments).toHaveBeenCalledWith('bot-1', 1, 20, undefined);
        });

        rerender({ botId: 'bot-1', page: 2 });

        await waitFor(() => {
            expect(documentsApi.listDocuments).toHaveBeenCalledWith('bot-1', 2, 20, undefined);
        });
    });
});

describe('useUploadDocuments', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('uploads documents successfully', async () => {
        const mockResponse = {
            id: '123',
            document_id: '123',
            status: 'uploaded',
            queued: true,
        };

        vi.mocked(documentsApi.uploadDocuments).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useUploadDocuments());

        const files = [new File(['content'], 'test.pdf', { type: 'application/pdf' })];
        
        expect(result.current.isPending).toBe(false);

        const uploadPromise = result.current.mutate('bot-1', files);
        const response = await uploadPromise;

        await waitFor(() => {
            expect(result.current.isPending).toBe(false);
        });

        expect(response).toEqual(mockResponse);
        expect(result.current.error).toBeNull();
    });

    it('handles upload error', async () => {
        const mockError = new Error('Upload failed');
        vi.mocked(documentsApi.uploadDocuments).mockRejectedValue(mockError);

        const { result } = renderHook(() => useUploadDocuments());

        const files = [new File(['content'], 'test.pdf', { type: 'application/pdf' })];

        try {
            await result.current.mutate('bot-1', files);
        } catch (_error) {
            // Expected to throw
        }

        await waitFor(() => {
            expect(result.current.isPending).toBe(false);
        });

        expect(result.current.error).toBeTruthy();
    });
});

describe('useDeleteDocument', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('deletes document successfully', async () => {
        vi.mocked(documentsApi.deleteDocument).mockResolvedValue(undefined);

        const { result } = renderHook(() => useDeleteDocument());

        expect(result.current.isPending).toBe(false);

        const deletePromise = result.current.mutate('doc-123');
        await deletePromise;

        await waitFor(() => {
            expect(result.current.isPending).toBe(false);
        });

        expect(result.current.error).toBeNull();
    });

    it('handles delete error', async () => {
        const mockError = new Error('Delete failed');
        vi.mocked(documentsApi.deleteDocument).mockRejectedValue(mockError);

        const { result } = renderHook(() => useDeleteDocument());

        try {
            await result.current.mutate('doc-123');
        } catch (_error) {
            // Expected to throw
        }

        await waitFor(() => {
            expect(result.current.isPending).toBe(false);
        });

        expect(result.current.error).toBeTruthy();
    });
});
