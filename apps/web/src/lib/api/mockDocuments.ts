import { Document, DocumentChunk, PaginatedDocumentsResponse } from "@/types/document";

// Mock documents data
export const mockDocuments: Document[] = [
    {
        id: "doc-1",
        bot_id: "bot-123",
        filename: "product-specifications.pdf",
        file_size: 2457600, // 2.4 MB
        status: "processed",
        chunk_count: 45,
        created_at: "2025-12-08T10:30:00Z",
        updated_at: "2025-12-08T10:32:15Z",
        title: "Product Specifications",
        mime_type: "application/pdf",
    },
    {
        id: "doc-2",
        bot_id: "bot-123",
        filename: "company-policies.docx",
        file_size: 1536000, // 1.5 MB
        status: "processed",
        chunk_count: 32,
        created_at: "2025-12-07T14:20:00Z",
        updated_at: "2025-12-07T14:21:45Z",
        title: "Company Policies",
        mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    {
        id: "doc-3",
        bot_id: "bot-123",
        filename: "user-guide.md",
        file_size: 524288, // 512 KB
        status: "processed",
        chunk_count: 18,
        created_at: "2025-12-06T09:15:00Z",
        updated_at: "2025-12-06T09:16:30Z",
        title: "User Guide",
        mime_type: "text/markdown",
    },
    {
        id: "doc-4",
        bot_id: "bot-123",
        filename: "faq-document.txt",
        file_size: 307200, // 300 KB
        status: "processing",
        chunk_count: 0,
        created_at: "2025-12-11T12:00:00Z",
        updated_at: "2025-12-11T12:00:45Z",
        title: "FAQ Document",
        mime_type: "text/plain",
        processing_progress: 65,
    },
    {
        id: "doc-5",
        bot_id: "bot-123",
        filename: "training-materials.pdf",
        file_size: 5242880, // 5 MB
        status: "processed",
        chunk_count: 87,
        created_at: "2025-12-05T16:45:00Z",
        updated_at: "2025-12-05T16:48:20Z",
        title: "Training Materials",
        mime_type: "application/pdf",
    },
    {
        id: "doc-6",
        bot_id: "bot-123",
        filename: "api-documentation.pdf",
        file_size: 1843200, // 1.8 MB
        status: "failed",
        chunk_count: 0,
        created_at: "2025-12-04T11:30:00Z",
        updated_at: "2025-12-04T11:30:45Z",
        title: "API Documentation",
        mime_type: "application/pdf",
        error_message: "Failed to extract text from PDF",
    },
    {
        id: "doc-7",
        bot_id: "bot-123",
        filename: "release-notes-2024.txt",
        file_size: 153600, // 150 KB
        status: "processed",
        chunk_count: 12,
        created_at: "2025-12-03T08:20:00Z",
        updated_at: "2025-12-03T08:21:10Z",
        title: "Release Notes 2024",
        mime_type: "text/plain",
    },
    {
        id: "doc-8",
        bot_id: "bot-123",
        filename: "installation-guide.md",
        file_size: 409600, // 400 KB
        status: "processed",
        chunk_count: 22,
        created_at: "2025-12-02T13:45:00Z",
        updated_at: "2025-12-02T13:46:30Z",
        title: "Installation Guide",
        mime_type: "text/markdown",
    },
    {
        id: "doc-9",
        bot_id: "bot-123",
        filename: "troubleshooting.pdf",
        file_size: 2621440, // 2.5 MB
        status: "pending",
        chunk_count: 0,
        created_at: "2025-12-11T13:30:00Z",
        updated_at: "2025-12-11T13:30:00Z",
        title: "Troubleshooting Guide",
        mime_type: "application/pdf",
    },
    {
        id: "doc-10",
        bot_id: "bot-123",
        filename: "best-practices.docx",
        file_size: 1228800, // 1.2 MB
        status: "processed",
        chunk_count: 28,
        created_at: "2025-12-01T10:00:00Z",
        updated_at: "2025-12-01T10:01:40Z",
        title: "Best Practices",
        mime_type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    {
        id: "doc-11",
        bot_id: "bot-123",
        filename: "glossary.txt",
        file_size: 204800, // 200 KB
        status: "processed",
        chunk_count: 15,
        created_at: "2025-11-30T15:20:00Z",
        updated_at: "2025-11-30T15:21:00Z",
        title: "Technical Glossary",
        mime_type: "text/plain",
    },
    {
        id: "doc-12",
        bot_id: "bot-123",
        filename: "architecture-overview.pdf",
        file_size: 3145728, // 3 MB
        status: "processed",
        chunk_count: 56,
        created_at: "2025-11-29T09:30:00Z",
        updated_at: "2025-11-29T09:33:10Z",
        title: "Architecture Overview",
        mime_type: "application/pdf",
    },
];

// Mock chunks for a document
export const mockChunks: DocumentChunk[] = [
    {
        id: "chunk-1",
        document_id: "doc-1",
        content: "Product Specifications Overview: This document outlines the technical specifications for our flagship product. The system is designed to handle high-volume data processing with low latency.",
        chunk_index: 0,
        page_number: 1,
        created_at: "2025-12-08T10:32:00Z",
    },
    {
        id: "chunk-2",
        document_id: "doc-1",
        content: "Performance Requirements: The system must process at least 10,000 requests per second with an average response time under 100ms. Peak capacity should support 50,000 concurrent users.",
        chunk_index: 1,
        page_number: 2,
        created_at: "2025-12-08T10:32:05Z",
    },
    {
        id: "chunk-3",
        document_id: "doc-1",
        content: "Security Features: All data is encrypted at rest using AES-256 encryption. Transport layer security uses TLS 1.3. Role-based access control (RBAC) is implemented throughout the system.",
        chunk_index: 2,
        page_number: 3,
        created_at: "2025-12-08T10:32:10Z",
    },
    {
        id: "chunk-4",
        document_id: "doc-1",
        content: "Integration Capabilities: The system provides RESTful APIs and WebSocket support for real-time communication. SDKs are available for Python, JavaScript, Java, and Go.",
        chunk_index: 3,
        page_number: 4,
        created_at: "2025-12-08T10:32:15Z",
    },
];

// Helper function to simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock API functions
export const mockDocumentsApi = {
    async listDocuments(
        botId: string,
        page: number = 1,
        pageSize: number = 20,
        search?: string
    ): Promise<PaginatedDocumentsResponse> {
        await delay(300); // Simulate network delay

        let filteredDocs = mockDocuments.filter(doc => doc.bot_id === botId);

        if (search) {
            const searchLower = search.toLowerCase();
            filteredDocs = filteredDocs.filter(doc =>
                doc.filename.toLowerCase().includes(searchLower) ||
                doc.title?.toLowerCase().includes(searchLower)
            );
        }

        const total = filteredDocs.length;
        const totalPages = Math.ceil(total / pageSize);
        const startIndex = (page - 1) * pageSize;
        const endIndex = startIndex + pageSize;
        const paginatedDocs = filteredDocs.slice(startIndex, endIndex);

        return {
            documents: paginatedDocs,
            total,
            page,
            page_size: pageSize,
            total_pages: totalPages,
        };
    },

    async getDocument(documentId: string) {
        await delay(200);
        
        const doc = mockDocuments.find(d => d.id === documentId);
        if (!doc) {
            throw new Error("Document not found");
        }

        return {
            ...doc,
            chunks: mockChunks.filter(c => c.document_id === documentId),
        };
    },

    async uploadDocuments(botId: string, files: File[]) {
        await delay(500);
        
        // Simulate successful upload
        return {
            id: `doc-${Date.now()}`,
            document_id: `doc-${Date.now()}`,
            status: "pending",
            queued: true,
        };
    },

    async deleteDocument(documentId: string) {
        await delay(300);
        
        const index = mockDocuments.findIndex(d => d.id === documentId);
        if (index === -1) {
            throw new Error("Document not found");
        }
        
        // In a real implementation, this would delete from the array
        console.log(`Mock: Deleted document ${documentId}`);
    },

    async bulkDeleteDocuments(botId: string, documentIds: string[]) {
        await delay(500);
        
        // Validate documents belong to the bot
        const validDocs = mockDocuments.filter(
            d => d.bot_id === botId && documentIds.includes(d.id)
        );
        
        if (validDocs.length === 0) {
            throw new Error("No valid documents found");
        }

        console.log(`Mock: Bulk deleted ${validDocs.length} documents`);

        return {
            message: "Bulk deletion initiated",
            queued_count: validDocs.length,
            document_ids: validDocs.map(d => d.id),
        };
    },

    async reprocessDocument(documentId: string) {
        await delay(400);
        
        const doc = mockDocuments.find(d => d.id === documentId);
        if (!doc) {
            throw new Error("Document not found");
        }

        return {
            id: documentId,
            status: "processing",
            queued: true,
        };
    },

    async getDocumentChunks(documentId: string) {
        await delay(250);
        
        const chunks = mockChunks.filter(c => c.document_id === documentId);
        return {
            chunks,
            total: chunks.length,
        };
    },
};
