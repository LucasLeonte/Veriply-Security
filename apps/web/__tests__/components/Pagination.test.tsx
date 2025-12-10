import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Pagination } from '@/components/kb/Pagination';

describe('Pagination', () => {
    const mockOnPageChange = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('does not render when totalPages is 1 or less', () => {
        const { container } = render(
            <Pagination
                currentPage={1}
                totalPages={1}
                onPageChange={mockOnPageChange}
            />
        );

        expect(container.firstChild).toBeNull();
    });

    it('renders pagination controls for multiple pages', () => {
        render(
            <Pagination
                currentPage={1}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        expect(screen.getByLabelText('Previous page')).toBeInTheDocument();
        expect(screen.getByLabelText('Next page')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument();
        expect(screen.getByText('5')).toBeInTheDocument();
    });

    it('displays item count when provided', () => {
        render(
            <Pagination
                currentPage={1}
                totalPages={5}
                onPageChange={mockOnPageChange}
                totalItems={100}
                itemsPerPage={20}
            />
        );

        expect(screen.getByText('Showing 1 - 20 of 100')).toBeInTheDocument();
    });

    it('calls onPageChange when clicking next', () => {
        render(
            <Pagination
                currentPage={1}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        const nextButton = screen.getByLabelText('Next page');
        fireEvent.click(nextButton);

        expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });

    it('calls onPageChange when clicking previous', () => {
        render(
            <Pagination
                currentPage={3}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        const prevButton = screen.getByLabelText('Previous page');
        fireEvent.click(prevButton);

        expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });

    it('calls onPageChange when clicking a page number', () => {
        render(
            <Pagination
                currentPage={1}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        const page3Button = screen.getByText('3');
        fireEvent.click(page3Button);

        expect(mockOnPageChange).toHaveBeenCalledWith(3);
    });

    it('disables previous button on first page', () => {
        render(
            <Pagination
                currentPage={1}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        const prevButton = screen.getByLabelText('Previous page');
        expect(prevButton).toBeDisabled();
    });

    it('disables next button on last page', () => {
        render(
            <Pagination
                currentPage={5}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        const nextButton = screen.getByLabelText('Next page');
        expect(nextButton).toBeDisabled();
    });

    it('highlights current page', () => {
        render(
            <Pagination
                currentPage={3}
                totalPages={5}
                onPageChange={mockOnPageChange}
            />
        );

        const currentPageButton = screen.getByLabelText('Page 3');
        expect(currentPageButton).toHaveClass('bg-emerald-600', 'text-white');
    });

    it('shows ellipsis for many pages', () => {
        render(
            <Pagination
                currentPage={5}
                totalPages={20}
                onPageChange={mockOnPageChange}
            />
        );

        const ellipses = screen.getAllByText('...');
        expect(ellipses.length).toBeGreaterThan(0);
    });

    it('calculates correct item range for middle page', () => {
        render(
            <Pagination
                currentPage={2}
                totalPages={5}
                onPageChange={mockOnPageChange}
                totalItems={100}
                itemsPerPage={20}
            />
        );

        expect(screen.getByText('Showing 21 - 40 of 100')).toBeInTheDocument();
    });

    it('calculates correct item range for last page with partial items', () => {
        render(
            <Pagination
                currentPage={5}
                totalPages={5}
                onPageChange={mockOnPageChange}
                totalItems={95}
                itemsPerPage={20}
            />
        );

        expect(screen.getByText('Showing 81 - 95 of 95')).toBeInTheDocument();
    });
});
