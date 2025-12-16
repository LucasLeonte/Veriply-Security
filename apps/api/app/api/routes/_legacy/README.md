# Legacy Routes - Archived

This folder contains old tenant-scoped routes that have been replaced by group-scoped routes in `app/api/v1/`.

## Archived Files

### bots.py

-   **Old Path**: `/api/v1/bots`
-   **Replaced By**: `app/api/v1/bots.py` with `/api/v1/groups/{group_id}/bots`
-   **Reason**: Migration from tenant-scoped to group-scoped architecture
-   **Date Archived**: December 16, 2025

The bot endpoints were migrated to require group membership for better access control and organization.

## Active Routes Structure

**Group-scoped (app/api/v1/):**

-   `auth.py` - Authentication endpoints
-   `profile.py` - User profile management
-   `groups.py` - Group CRUD and membership
-   `bots.py` - Bot management within groups
-   `documents.py` - Document management within groups

**Legacy document operations (app/api/routes/):**

-   `query.py` - Query/search endpoints
-   `documents.py` - Document detail endpoints (`/api/v1/documents/{id}`) for operations like:
    -   Get document details
    -   Bulk delete
    -   Reprocess document
    -   Get document chunks

These document detail endpoints are kept for backward compatibility and will be migrated to group-scoped in a future iteration.
