# Migration for user_id Field - Manual Application

Due to branching complexity in the existing migrations, apply this change manually:

## SQL to apply directly:

```sql
-- Add user_id column to email_processing_queue
ALTER TABLE email_processing_queue 
ADD COLUMN user_id uuid NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';

-- Add foreign key constraint
ALTER TABLE email_processing_queue 
ADD CONSTRAINT fk_email_processing_queue_user_id 
FOREIGN KEY (user_id) REFERENCES users(id);

-- Update alembic version
INSERT INTO alembic_version (version_num) VALUES ('022_add_user_id_email_processing_queue');
```

## Or in psql:

```bash
psql -U [user] -d [database] -h [host] -c "
ALTER TABLE email_processing_queue 
ADD COLUMN user_id uuid NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000';

ALTER TABLE email_processing_queue 
ADD CONSTRAINT fk_email_processing_queue_user_id 
FOREIGN KEY (user_id) REFERENCES users(id);

INSERT INTO alembic_version (version_num) VALUES ('022_add_user_id_email_processing_queue');
"
```

## Note on Migration Strategy

The migration file at `alembic/versions/022_add_user_id_email_processing_queue.py` uses a temporary UUID default to populate existing rows.

For production deployment:
1. Apply the ALTER TABLE with temporary default
2. Update existing queue items with actual user_id values (if any exist)
3. Remove the server default
4. Make column NOT NULL (already done in code)

The migration file has been created but due to branching issues in the migration history, 
it should be applied manually or after resolving the existing migration branches.

Related issue: Multiple head revisions exist (015_update_group_roles, 012_add_verified_qa_table, 021_add_kb_emails)
