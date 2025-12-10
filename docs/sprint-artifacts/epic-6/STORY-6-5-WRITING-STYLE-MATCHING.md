# Story 6.5: Writing Style Matching

Status: drafted

## Story

As a User,
I want email drafts to match my writing style and tone,
so that responses sound authentic and consistent with how I naturally communicate.

## Acceptance Criteria

1. **Given** I have sent emails previously  
   **When** the system generates a draft  
   **Then** it analyzes my historical emails for:
   - Tone (formal, casual, friendly)
   - Greeting style ("Hi [Name]," vs "Hello," vs "Dear [Name],")
   - Closing style ("Best regards," vs "Thanks," vs "Cheers,")
   - Sentence structure (short vs long, simple vs complex)
   - Average email length
   - Use of emojis, exclamation points, or casual language

2. **Given** I have insufficient email history (< 10 emails)  
   **Then** system uses a default professional style  
   **And** displays a banner: "We're learning your writing style. Send more emails to improve personalization."

3. **Given** system has analyzed my style  
   **Then** LLM prompt includes style guidelines:
   - Example tone: "Match the sender's casual, friendly tone with short sentences"
   - Example greeting: "Use 'Hi [Name],' as greeting"
   - Example closing: "End with 'Thanks,' or 'Best,'"
   - Vocabulary preferences (technical jargon vs plain language)

4. **Given** I want to review my detected style  
   **Then** I can view "My Writing Style" page showing:
   - Detected tone (with examples from my emails)
   - Common phrases I use
   - Average email length
   - Greeting/closing patterns
   - Option to manually adjust preferences

5. **Given** I manually adjust my style preferences  
   **Then** those preferences override auto-detected style  
   **And** future drafts use my manual preferences  
   **And** I can reset to auto-detected style anytime

6. **Given** I have multiple email accounts connected  
   **Then** system tracks style per email account separately  
   **And** uses appropriate style based on which account triggered the draft

## Tasks / Subtasks

- [ ] Task 1: Email history collection (AC: #1, #2, #6)
  - [ ] Create database table: `user_email_history`
  - [ ] Columns: `id`, `tenant_id`, `user_id`, `integration_id`, `email_id`, `subject`, `body`, `sent_at`, `analyzed` (boolean), `created_at`
  - [ ] Add RLS policy filtered by `tenant_id`
  - [ ] Fetch sent emails from Gmail (using `me/sent` endpoint)
  - [ ] Fetch sent emails from Outlook (using Graph API `/me/mailFolders/sentitems/messages`)
  - [ ] Store last 50 sent emails per integration
  - [ ] Schedule periodic sync (weekly) to refresh email history

- [ ] Task 2: Style analysis engine (AC: #1, #3)
  - [ ] Create module: `apps/api/app/email_automation/style_analyzer.py`
  - [ ] Implement tone detection:
    - Use sentiment analysis (e.g., TextBlob or transformer model)
    - Classify as: formal, semi-formal, casual, friendly
    - Detect formality markers: "Dear Sir", "regards", vs "hey", "thanks"
  - [ ] Implement pattern extraction:
    - Extract greeting patterns (first line of emails)
    - Extract closing patterns (last line before signature)
    - Calculate average sentence length
    - Calculate average email length (word count)
    - Detect emoji/punctuation usage frequency
  - [ ] Store analysis results in database

- [ ] Task 3: Style profile storage (AC: #1, #4, #5, #6)
  - [ ] Create database table: `user_writing_styles`
  - [ ] Columns: `id`, `tenant_id`, `user_id`, `integration_id`, `tone` (enum: formal/casual/friendly), `greeting_pattern`, `closing_pattern`, `avg_sentence_length`, `avg_email_length`, `uses_emojis` (boolean), `formality_score` (0-100), `custom_preferences` (jsonb), `is_manual_override` (boolean), `last_analyzed_at`, `sample_count`, `created_at`, `updated_at`
  - [ ] Add RLS policy filtered by `tenant_id`
  - [ ] Add constraint: one style profile per (user_id, integration_id)

- [ ] Task 4: Background worker for style analysis (AC: #1, #2)
  - [ ] Create worker: `apps/api/app/workers/style_analyzer_worker.py`
  - [ ] Trigger analysis when:
    - User connects new email account (analyze existing sent emails)
    - Periodic refresh (weekly, to capture new emails)
    - Manual trigger from UI ("Refresh My Style")
  - [ ] Skip analysis if < 10 emails available
  - [ ] Update `user_writing_styles` table with results
  - [ ] Set `sample_count` to track email history size

- [ ] Task 5: Style-aware prompt enhancement (AC: #3)
  - [ ] Extend email draft prompt template from Story 6.4
  - [ ] Load user's writing style profile
  - [ ] Inject style guidelines into prompt:
    ```
    Writing Style Guidelines:
    - Tone: {tone} (e.g., "casual and friendly")
    - Greeting: Use "{greeting_pattern}" (e.g., "Hi [Name],")
    - Closing: Use "{closing_pattern}" (e.g., "Thanks,")
    - Sentence style: {avg_sentence_length} (e.g., "Keep sentences short and concise")
    - Emojis: {uses_emojis ? "Feel free to use emojis where appropriate" : "Avoid emojis"}
    - Length: Aim for {avg_email_length} words
    ```
  - [ ] If no style profile exists (< 10 emails), use default professional template
  - [ ] Apply style based on `integration_id` that triggered draft

- [ ] Task 6: Frontend - Writing Style page (AC: #4, #5)
  - [ ] Create page: `apps/web/src/app/dashboard/settings/writing-style/page.tsx`
  - [ ] Display detected style for each connected email account:
    - Tone badge (Formal/Casual/Friendly)
    - Example greeting and closing
    - Average email length chart
    - Sample phrases extracted from user's emails
  - [ ] Show "Insufficient Data" state if < 10 emails
  - [ ] Add "Refresh Style" button to trigger re-analysis
  - [ ] Implement manual preferences editor:
    - Tone selector (Formal/Casual/Friendly)
    - Custom greeting input
    - Custom closing input
    - Toggle: "Use emojis"
    - Slider: Formality level (0-100)
  - [ ] Save manual preferences with "Save Preferences" button
  - [ ] Add "Reset to Auto-Detected" button

- [ ] Task 7: API endpoints for style management (AC: #4, #5)
  - [ ] GET `/api/v1/writing-style` - Get all style profiles for user
  - [ ] GET `/api/v1/writing-style/:integration_id` - Get specific style profile
  - [ ] PUT `/api/v1/writing-style/:integration_id` - Update manual preferences
  - [ ] POST `/api/v1/writing-style/:integration_id/refresh` - Trigger re-analysis
  - [ ] DELETE `/api/v1/writing-style/:integration_id/override` - Reset to auto-detected

- [ ] Task 8: Default professional style template (AC: #2)
  - [ ] Create default style profile:
    - Tone: "semi-formal"
    - Greeting: "Hi [Name],"
    - Closing: "Best regards,"
    - Moderate sentence length
    - No emojis
    - ~150 words average
  - [ ] Use default when no style profile exists
  - [ ] Display banner in draft generation UI: "Learning your style..."

- [ ] Task 9: Testing (All ACs)
  - [ ] Unit test tone detection algorithm
  - [ ] Unit test pattern extraction (greeting, closing)
  - [ ] Unit test style profile creation and storage
  - [ ] Integration test style analysis worker
  - [ ] Integration test prompt enhancement with style injection
  - [ ] Test default style when < 10 emails
  - [ ] Test manual preference override
  - [ ] Test multi-account style tracking
  - [ ] E2E test: analyze style → generate draft with matching tone

## Dev Notes

### Technical Constraints

- **Privacy & Data Minimization:**
  - Only store email metadata needed for style analysis (subject, body)
  - Do not store full emails permanently (analyze and discard or retain for limited time)
  - Allow user to delete email history: "Clear My Email History" button
  - Comply with GDPR Right to be Forgotten

- **Analysis Accuracy:**
  - Minimum sample size: 10 emails for reliable analysis
  - Re-analyze every 50 new emails or weekly (whichever comes first)
  - Use statistical confidence metrics (e.g., if < 20 emails, show "Preliminary analysis")

- **Style Application:**
  - Style guidelines are prompts, not hard rules (LLM interprets)
  - Include example sentences from user's emails in prompt for better matching
  - Balance style matching with professional appropriateness (avoid copying unprofessional language)

- **Performance:**
  - Style analysis is async (background worker)
  - Cache style profiles in Redis for fast access during draft generation
  - Analysis should complete within 2 minutes for 50 emails

### Learnings from Previous Story

**From Story 6-4: Email Draft Generation**

- **Reuse Components:**
  - Email draft generation prompt template (extend with style injection)
  - Gmail and Outlook API wrappers for fetching sent emails
  - LLM integration for generating drafts

- **Integration Points:**
  - Draft generator loads style profile before generating
  - Style profile selected based on `integration_id` from email rule
  - Default style used as fallback

**From Stories 6-1, 6-2: OAuth Integrations**

- **Reuse Components:**
  - `email_integrations` table has connection details
  - Gmail API wrapper can fetch sent emails
  - Outlook Graph API wrapper can fetch sent items

- **Permissions:**
  - Gmail scope `gmail.readonly` allows reading sent emails
  - Outlook scope `Mail.Read` allows reading sent items

### Project Structure Notes

- **Backend:**
  - Create module: `apps/api/app/email_automation/style_analyzer.py` - Core analysis logic
  - Create worker: `apps/api/app/workers/style_analyzer_worker.py` - Background processing
  - Database models:
    - `apps/api/app/models/user_email_history.py`
    - `apps/api/app/models/user_writing_styles.py`
  - API routes: `apps/api/app/routes/writing_style.py`
  - Migrations:
    - `apps/api/alembic/versions/xxx_add_user_email_history.py`
    - `apps/api/alembic/versions/xxx_add_user_writing_styles.py`

- **Frontend:**
  - Create page: `apps/web/src/app/dashboard/settings/writing-style/page.tsx`
  - Components:
    - `apps/web/src/components/writing-style/StyleProfile.tsx`
    - `apps/web/src/components/writing-style/StyleEditor.tsx`
    - `apps/web/src/components/writing-style/EmailSamplePreview.tsx`
  - Reuse shadcn/ui: Card, Badge, Slider, Select, Switch

- **ML/NLP:**
  - Consider using lightweight libraries:
    - `textblob` for sentiment analysis
    - `nltk` for sentence tokenization
    - Or use LLM for style analysis (cost vs accuracy tradeoff)

### Architecture Alignment

- Extends email draft generation from Story 6.4 with style personalization
- Uses background workers consistent with async processing pattern (Epic 2, Epic 6)
- Multi-tenancy enforced via RLS (Epic 1 foundation)
- Privacy-conscious data handling (GDPR compliance)
- User preferences override AI detection (human-in-the-loop principle)

### Alternative Approaches Considered

1. **LLM-based style analysis:**
   - Pro: More accurate, understands nuance
   - Con: Higher cost, slower processing
   - Decision: Use rule-based + sentiment analysis for MVP, consider LLM for v2

2. **Real-time style learning:**
   - Pro: Always up-to-date
   - Con: Complex state management, higher latency
   - Decision: Use periodic batch analysis (weekly refresh)

3. **Style voting by recipients:**
   - Pro: Feedback loop improves accuracy
   - Con: Requires recipient interaction, slow feedback
   - Decision: Defer to post-MVP

### References

- [Source: docs/epics.md - Epic 6: Email Automation, Story 6.5]
- [Source: docs/prd.md - FR48: Writing style matching]
- [Source: docs/architecture.md - Background processing section]
- [Gmail API - Users.messages: list](https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list)
- [Microsoft Graph - List messages](https://docs.microsoft.com/en-us/graph/api/user-list-messages)
- [TextBlob Documentation](https://textblob.readthedocs.io/)

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

_To be filled by dev agent_

### Debug Log References

_To be filled by dev agent_

### Completion Notes List

_To be filled by dev agent_

### File List

_To be filled by dev agent_
