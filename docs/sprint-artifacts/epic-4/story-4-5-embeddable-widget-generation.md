# Story 4.5: Embeddable Widget Generation

**Epic:** 4. Chat Experience  
**Status:** ready-for-dev  
**Assigned to:** Unassigned  
**Blocked by:** 4-1-web-chat-interface  
**Context:** docs/sprint-artifacts/epic-4/story-4-5.context.xml

## Story

As a User,  
I want to generate an embeddable widget for my bot,  
so that I can add the chat to my website.

## Acceptance Criteria

### Widget Code Generation

1. **Given** I am on a bot's Settings page  
   **When** I click "Get Widget Code"  
   **Then** I see a code snippet in a text area:
   ```html
   <script src="https://veriply.io/widget.js" 
           data-bot-id="550e8400-e29b-41d4-a716-446655440000" 
           data-position="bottom-right"
           data-primary-color="#3B82F6"
           data-welcome-message="Hi! How can I help?">
   </script>
   ```

2. **Given** I see the code snippet  
   **When** I look at the options  
   **Then** I see a "Copy to Clipboard" button  
   **And** clicking it copies the code and shows: "Copied!"

### Widget Customization

3. **Given** I want to customize the widget appearance  
   **When** I look at the settings  
   **Then** I see customization options:
   - **Position**: Dropdown (bottom-right, bottom-left, top-right, top-left)
   - **Primary Color**: Color picker input (default: #3B82F6)
   - **Welcome Message**: Text field (max 200 chars)
   - **Auto-open**: Toggle switch (on/off, default: off)

4. **Given** I change the position to "bottom-left"  
   **When** I update the setting  
   **Then** the code snippet updates immediately:
   ```html
   data-position="bottom-left"
   ```

5. **Given** I select a new primary color (e.g., #FF6B6B)  
   **When** the color is selected  
   **Then** the code snippet updates:
   ```html
   data-primary-color="#FF6B6B"
   ```

6. **Given** I enter a welcome message: "Welcome to Support!"  
   **When** I update the field  
   **Then** the code snippet updates:
   ```html
   data-welcome-message="Welcome to Support!"
   ```

7. **Given** I enable "Auto-open"  
   **When** the toggle is ON  
   **Then** the code snippet updates:
   ```html
   data-auto-open="true"
   ```

### Widget Preview

8. **Given** I customize the widget settings  
   **When** I look at the preview area  
   **Then** I see a live preview of the widget with:
   - Correct position on screen (bottom-right, etc.)
   - Primary color applied to buttons and accents
   - Welcome message displayed
   - Widget appears to expand/collapse based on auto-open setting

9. **Given** I click on the preview widget  
   **When** the widget opens in the preview  
   **Then** it shows the chat interface (not fully functional, just UI preview)

### Widget Implementation

10. **Given** a website owner embeds the widget code on their site  
    **When** the page loads  
    **Then** the widget script (widget.js) loads asynchronously  
    **And** the widget appears in the specified position  
    **And** the widget loads the chat interface in an iframe

11. **Given** the widget loads with `data-bot-id` parameter  
    **When** initialization completes  
    **Then** the widget fetches bot metadata (name, welcome message)  
    **And** displays the configured welcome message

### Security & Isolation

12. **Given** the widget loads on a website  
    **When** the iframe initializes  
    **Then** it loads from `https://veriply.io/chat/:bot_id`  
    **And** the iframe is sandboxed: `sandbox="allow-same-origin allow-forms allow-popups allow-scripts"`  
    **And** no access to parent window data (XSS protection)

13. **Given** a website embeds the widget  
    **When** the user interacts with the chat  
    **Then** the chat data is isolated to the iframe  
    **And** no bot data leaks to parent window

### Responsive Design

14. **Given** the widget is embedded on a desktop website  
    **When** I interact with the chat  
    **Then** the widget is responsive and works at all breakpoints

15. **Given** the widget is embedded on a mobile website  
    **When** I rotate the device  
    **Then** the widget adapts to the new screen size  
    **And** chat remains fully functional

### Error Handling

16. **Given** the widget code is embedded incorrectly (wrong script tag)  
    **When** the page loads  
    **Then** NO error is shown to end-user  
    **And** the widget silently fails to load (graceful degradation)

17. **Given** the bot is disabled or deleted  
    **When** someone visits the embedded widget  
    **Then** the widget shows: "This bot is no longer available"  
    **And** no error is exposed

## Tasks / Subtasks

### 1) Frontend - Widget Settings Panel

- [ ] Create widget customization UI in bot settings:
  - [ ] Component: `WidgetSettings.tsx` in bot settings page
  - [ ] Display current widget code snippet (read-only textarea)
  - [ ] Add "Copy to Clipboard" button (use shadcn/ui)
- [ ] Customization form:
  - [ ] Position dropdown: bottom-right, bottom-left, top-right, top-left
  - [ ] Color picker for primary color (use shadcn/ui Popover + color input)
  - [ ] Welcome message text field (max 200 chars, counter)
  - [ ] Auto-open toggle switch
- [ ] Real-time code generation:
  - [ ] Function: `generateWidgetCode(settings)` updates snippet
  - [ ] Subscribe to setting changes, re-generate on each change
  - [ ] Display in readonly textarea

### 2) Frontend - Widget Preview

- [ ] Create `WidgetPreview.tsx` component:
  - [ ] Render preview of widget in different positions (CSS positioning)
  - [ ] Show widget button with specified color
  - [ ] Embed live chat preview (non-functional, just UI)
  - [ ] Split-screen: customization form on left, preview on right
- [ ] Live preview updates:
  - [ ] On position change: move preview widget
  - [ ] On color change: update button color in preview
  - [ ] On message change: update welcome text in preview

### 3) Frontend - Copy to Clipboard

- [ ] Implement clipboard copy:
  - [ ] Use `navigator.clipboard.writeText(code)`
  - [ ] Show success toast: "Copied to clipboard!"
  - [ ] Fallback for older browsers (copy to input, user select/Ctrl+C)

### 4) Backend - Widget API Endpoint

- [ ] Create endpoint: `GET /api/v1/bots/:bot_id/widget/config`
  - [ ] Returns widget configuration: `{ bot_id, position, color, welcome_message, auto_open }`
  - [ ] Public endpoint (no auth required if bot is public)
  - [ ] Cache response (5 min TTL)
- [ ] Create endpoint: `GET /api/v1/bots/:bot_id/public` (already in Story 4.1)
  - [ ] Returns: `{ name, avatar, welcome_message, is_public }`

### 5) Frontend - Widget Bundle (widget.js)

- [ ] Create `widget.js` bundle:
  - [ ] Bundled with esbuild or webpack (minimal, <50KB gzipped)
  - [ ] Deployment location: `apps/web/public/widget.js` or CDN
- [ ] Widget initialization logic:
  - [ ] Read `data-*` attributes from script tag
  - [ ] Create iframe element with src: `/chat/:bot_id?embedded=true`
  - [ ] Apply positioning and styling
  - [ ] Append to document
- [ ] Widget DOM structure:
  ```html
  <div id="veriply-widget" class="veriply-widget" style="position: fixed; ...">
    <iframe src="https://veriply.io/chat/:bot_id?embedded=true" 
            sandbox="allow-same-origin allow-forms allow-popups allow-scripts"
            style="border: none; width: 100%; height: 100%; ...">
    </iframe>
  </div>
  ```

### 6) Frontend - Chat Page Embedded Mode

- [ ] Update chat page to detect embedded mode:
  - [ ] Check URL query param: `?embedded=true`
  - [ ] If embedded:
    - [ ] Hide header/footer (keep compact)
    - [ ] Adjust styling for iframe (no full-screen layouts)
    - [ ] Ensure responsive within iframe constraints
    - [ ] Post messages to parent window for analytics (optional)

### 7) Backend - Widget Config Storage

- [ ] Create `WidgetConfig` model in SQLAlchemy:
  ```python
  class WidgetConfig(Base):
      __tablename__ = "widget_configs"
      
      id: UUID = Column(UUID, primary_key=True, default=uuid4)
      bot_id: UUID = Column(UUID, ForeignKey("bots.id"), nullable=False, unique=True)
      position: str = Column(Enum(...), default="bottom-right")  # bottom-right, etc.
      primary_color: str = Column(String(7), default="#3B82F6")  # hex color
      welcome_message: str = Column(String(200), nullable=True)
      auto_open: bool = Column(Boolean, default=False)
      created_at: DateTime = Column(DateTime, default=utcnow)
      updated_at: DateTime = Column(DateTime, default=utcnow, onupdate=utcnow)
  ```
- [ ] Cascade delete: when bot deleted → widget config deleted

### 8) Backend - Widget Config Endpoints

- [ ] Create endpoint: `GET /api/v1/bots/:bot_id/widget/config`
  - [ ] Return widget config for bot
  - [ ] Requires bot owner authentication
- [ ] Create endpoint: `PUT /api/v1/bots/:bot_id/widget/config`
  - [ ] Update widget settings (position, color, welcome, auto_open)
  - [ ] Validate: color is valid hex, position in enum, message length < 200
  - [ ] Requires bot owner authentication
  - [ ] Return updated config

### 9) Deployment - Widget CDN

- [ ] Setup CDN serving for `widget.js`:
  - [ ] Option A: Serve from S3 (AWS CloudFront)
  - [ ] Option B: Serve from Veriply web server with caching headers
  - [ ] Set Cache-Control: max-age=86400 (1 day)
  - [ ] Versioned URL: `/widget/v1/widget.js` (for future updates)

### 10) Testing - Component Tests

- [ ] Test WidgetSettings component:
  - [ ] Code snippet renders with correct bot_id
  - [ ] Copy to clipboard button works
  - [ ] Position dropdown changes code
  - [ ] Color picker changes code
  - [ ] Message field changes code
  - [ ] Auto-open toggle changes code
- [ ] Test WidgetPreview component:
  - [ ] Preview widget appears in correct position
  - [ ] Colors applied to preview
  - [ ] Message displayed in preview
  - [ ] Responsive at different screen sizes
- [ ] Use Vitest + React Testing Library

### 11) Testing - Widget Integration Tests

- [ ] Create test HTML page that embeds widget
- [ ] Test widget loads:
  - [ ] Script tag loads successfully
  - [ ] Iframe created and inserted
  - [ ] Iframe loads chat page
  - [ ] Chat interface appears in widget
- [ ] Test widget positioning:
  - [ ] bottom-right, bottom-left, top-right, top-left all work
  - [ ] Widget doesn't overlap viewport edges excessively
- [ ] Test widget styling:
  - [ ] Primary color applied
  - [ ] Welcome message shows
  - [ ] Auto-open works (widget opens on page load)
- [ ] Test sandbox isolation:
  - [ ] No access to parent window (test postMessage)
  - [ ] Chat data doesn't leak to parent

### 12) Testing - API Tests

- [ ] Test widget config endpoints:
  - [ ] GET returns correct config
  - [ ] PUT updates config correctly
  - [ ] Validation rejects invalid color, position, message length
  - [ ] Authorization: only bot owner can update
- [ ] Test widget.js CDN:
  - [ ] File exists and is accessible
  - [ ] File size < 50KB gzipped
  - [ ] Cache headers set correctly
- [ ] Use pytest + TestClient

### 13) Documentation & Deployment

- [ ] Create widget installation guide:
  - [ ] Instructions for embedding widget code
  - [ ] Examples with different customizations
  - [ ] Troubleshooting section
- [ ] Document widget API:
  - [ ] Available data-* attributes
  - [ ] Configuration options
  - [ ] Browser compatibility (IE11+, modern browsers)
- [ ] Add widget size/performance notes:
  - [ ] Typical bundle size
  - [ ] Load time expectations
  - [ ] Network requests made by widget

## Dev Notes

### Architecture Patterns

- **Iframe Isolation**: Widget runs in sandboxed iframe for security
- **Attribute-Based Configuration**: data-* attributes for flexibility
- **Lazy Loading**: Widget script loads asynchronously, no blocking
- **CDN Distribution**: widget.js served from CDN for fast global delivery

### Component Reuse

- **From Story 4.1**: Reuse chat interface (embedded mode)
- **From Epic 2**: Reuse bot public metadata endpoint
- **From Epic 1**: Reuse bot ownership/authorization patterns

### Security Considerations

- **Sandbox Isolation**: Iframe sandbox prevents access to parent window
- **XSS Prevention**: No DOM manipulation of parent window
- **CSRF Protection**: Widget uses same auth tokens as web app
- **Domain Whitelisting**: Future (Story 4.6) for widget access control

### Performance Optimization

- **Bundle Size**: Keep widget.js minimal (<50KB gzipped)
- **Lazy Chat Loading**: Chat interface loads inside iframe (not in main page)
- **Caching**: Widget config cached on backend, widget.js cached by CDN
- **Async Loading**: Script tag loads non-blocking on host page

### Learnings from Previous Stories

From Story 4.1 (Chat Interface) [Source: epic-4/story-4-1-web-chat-interface.md]:

- **Chat Page Structure**: Embed same chat page in iframe
- **Public Bot Access**: Reuse public bot metadata endpoint

From Epic 2 (Bot Management) [Source: epic-2/story-2-1-bot-creation-configuration.md]:

- **Bot Configuration**: Similar pattern for storing widget config
- **Bot Owner Authorization**: Reuse authorization checks

### Dependencies & Blockers

- **Requires**: Story 4.1 (Chat interface) for embedded chat
- **Blocks**: Story 4.6 (Widget Security) for domain whitelisting
- **Optional**: Story 8.1 (Analytics) for widget usage metrics

### References

- Embeddable widget spec: [Source: docs/epics.md#Story-4.5]
- Chat interface: [Source: epic-4/story-4-1-web-chat-interface.md]
- Security best practices: [Source: docs/prd.md#Security-and-Compliance]
- Architecture: [Source: docs/architecture.md#Embeddable-Widget]
- Test standards: [Source: .bmad/bmm/testarch/knowledge/test-quality.md]

## Dev Agent Record

### Context Reference

<!-- Story context XML will be added by story-context workflow -->

### Agent Model Used

Claude Haiku 3.5

### Debug Log References

- Build widget.js bundle (esbuild)
- Test widget positioning and styling
- Verify iframe sandbox isolation
- Test cross-origin iframe communication

### Completion Notes List

- [ ] Widget settings UI renders correctly
- [ ] Code snippet generated with correct format
- [ ] Copy to clipboard works
- [ ] Live preview updates on setting changes
- [ ] Widget config stored in database
- [ ] widget.js bundle created and deployed
- [ ] Widget loads and displays chat
- [ ] Iframe sandbox isolation working
- [ ] All unit tests passing
- [ ] All integration tests passing

### File List

**Created (NEW):**
- `apps/web/src/components/WidgetSettings.tsx` - Widget config UI
- `apps/web/src/components/WidgetPreview.tsx` - Live preview component
- `apps/web/src/lib/widget/generator.ts` - Code generation
- `apps/web/widget/widget.ts` - Widget entry point (bundled)
- `apps/api/app/models/widget_config.py` - Widget config model
- `apps/api/app/api/routes/widget.py` - Widget API endpoints
- `apps/api/app/services/widget_service.py` - Widget business logic
- `apps/web/__tests__/WidgetSettings.test.tsx` - Component tests

**Modified:**
- `apps/web/next.config.ts` - Add widget bundling config
- `apps/web/src/app/chat/[botId]/page.tsx` - Add embedded mode detection
- `apps/api/app/main.py` - Register widget router
- `apps/api/app/models/bot.py` - Add widget relationship

**Deleted:**
- None
