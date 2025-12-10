# Story 4.6: Widget Security & Responsiveness

**Epic:** 4. Chat Experience  
**Status:** ready-for-dev  
**Assigned to:** Unassigned  
**Blocked by:** 4-5-embeddable-widget-generation  
**Context:** docs/sprint-artifacts/epic-4/story-4-6.context.xml

## Story

As a User,  
I want to restrict which domains can use my widget,  
so that my bot isn't embedded on unauthorized sites.

## Acceptance Criteria

### Domain Whitelist Configuration

1. **Given** I am on the widget settings page  
   **When** I look for domain restrictions  
   **Then** I see a "Allowed Domains" section  
   **And** an input field to add domains

2. **Given** I enter "example.com" in the allowed domains field  
   **When** I click Add or press Enter  
   **Then** "example.com" is added to the list  
   **And** it appears as a tag/chip in the list

3. **Given** I enter "*.example.com" (wildcard)  
   **When** I save the configuration  
   **Then** the wildcard is saved  
   **And** it allows the widget to load on any subdomain

4. **Given** I have multiple domains in the list  
   **When** I look at the whitelist  
   **Then** I see all domains listed with:
   - Domain name
   - Edit button (edit the domain)
   - Delete button (remove the domain)

5. **Given** I want to remove a domain  
   **When** I click the delete button  
   **Then** the domain is removed from the whitelist  
   **And** the updated config is saved

### Domain Validation

6. **Given** I try to add an invalid domain: "not a domain!@#"  
   **When** I submit  
   **Then** an error appears: "Invalid domain format"  
   **And** the domain is NOT added to the whitelist

7. **Given** I try to add "localhost" (for testing)  
   **When** I submit  
   **Then** it's accepted (valid for testing)  
   **And** added to the whitelist

8. **Given** I try to add a domain twice  
   **When** I submit  
   **Then** an error appears: "Domain already in whitelist"

### Widget Loading Enforcement

9. **Given** a website embeds my widget code  
   **When** the widget loads on "allowed-domain.com"  
   **Then** the widget initializes normally  
   **And** the chat interface appears

10. **Given** a website embeds my widget code  
    **When** the widget tries to load on "unauthorized-domain.com"  
    **Then** the widget does NOT load  
    **And** the user sees a message: "This widget is not authorized for this domain"  
    **And** NO chat interface is displayed

11. **Given** the domain whitelist is empty (no restrictions)  
    **When** anyone embeds the widget  
    **Then** the widget loads on ANY domain (backward compatible, no security)  
    **And** a warning appears in bot settings: "No domain restrictions. Widget is publicly accessible."

### Server-Side Verification

12. **Given** the widget makes a request to load chat  
    **When** the request arrives at the server  
    **Then** the server checks:
    - [ ] Origin header or Referer header
    - [ ] Match against configured whitelist
    - [ ] If not in whitelist (and whitelist not empty): return 403 Forbidden
    - [ ] If in whitelist: return 200 OK with chat page

13. **Given** a user manually edits widget code to bypass domain check  
    **When** the iframe tries to load chat  
    **Then** the server validates Origin/Referer (not trusting client)  
    **And** blocks unauthorized requests

### Mobile Responsiveness

14. **Given** the widget is embedded on a mobile website  
    **When** I view the widget on iPhone/Android  
    **Then** the chat interface is fully responsive  
    **And** text is readable (no zoom required)  
    **And** input field is touch-friendly (44px minimum)

15. **Given** I interact with the chat on a mobile device  
    **When** keyboard appears (iOS/Android)  
    **Then** the chat window adjusts:
    - [ ] Shifts up to stay visible above keyboard
    - [ ] Message list scrolls properly
    - [ ] Input remains accessible

16. **Given** the widget is on a small mobile screen (360px width)  
    **When** the widget loads  
    **Then** the chat interface scales appropriately  
    **And** no horizontal scrolling is needed

17. **Given** I rotate my mobile device (portrait ↔ landscape)  
    **When** the device rotates  
    **Then** the widget adapts to new dimensions  
    **And** no layout breaks occur

### Touch-Friendly Interface

18. **Given** I'm using the widget on a mobile device  
    **When** I look at interactive elements  
    **Then** all buttons and inputs meet 44x44px minimum (WCAG guideline)  
    **And** spacing between clickable elements is >= 8px

19. **Given** I'm typing a message on mobile  
    **When** I use the send button  
    **Then** the button is large enough (44px) for accurate touch

### Accessibility

20. **Given** I'm using a screen reader on mobile  
    **When** I interact with the widget  
    **Then** all ARIA labels are present and correct  
    **And** focus management is logical  
    **And** widget works with keyboard navigation

21. **Given** I'm on a low-vision mobile setting  
    **When** I view the widget  
    **Then** text contrast ratios meet WCAG AA (4.5:1)  
    **And** font sizes are readable (min 14px)

### Browser Compatibility

22. **Given** I embed the widget in various browsers  
    **When** the page loads  
    **Then** the widget works on:
    - [ ] Chrome/Edge (latest 2 versions)
    - [ ] Firefox (latest 2 versions)
    - [ ] Safari (latest 2 versions, desktop & mobile)
    - [ ] Safari on iOS 14+

23. **Given** I use the widget on an older browser (IE11)  
    **When** the widget loads  
    **Then** graceful degradation: widget doesn't crash  
    **And** fallback message: "This browser is not fully supported"

### Performance on Mobile

24. **Given** I load the widget on a slow 3G connection  
    **When** the page loads  
    **Then** the widget loads within 3 seconds  
    **And** chat interface appears (possibly with placeholder)  
    **And** user can start typing while chat connects

25. **Given** I'm on a mobile device with limited data  
    **When** the widget runs  
    **Then** network requests are minimized  
    **And** bundle size is optimized (< 50KB gzipped)

## Tasks / Subtasks

### 1) Frontend - Domain Whitelist UI

- [ ] Add "Allowed Domains" section to WidgetSettings:
  - [ ] Text input: "Enter domain (e.g., example.com, *.example.com)"
  - [ ] Add button or on-Enter handler
  - [ ] Error message area for validation errors
- [ ] List component:
  - [ ] Display all whitelisted domains as tags/chips
  - [ ] Each tag has delete (X) button
  - [ ] Hover states and smooth animations
  - [ ] Use shadcn/ui for consistent styling

### 2) Frontend - Domain Validation

- [ ] Implement domain validation function:
  - [ ] Regex or URL parsing to validate domain format
  - [ ] Accept: example.com, *.example.com, localhost, 127.0.0.1
  - [ ] Reject: invalid formats, special characters
  - [ ] Reject duplicates (check against existing list)
  - [ ] Show validation errors inline

### 3) Frontend - Warning Message

- [ ] When whitelist is empty:
  - [ ] Show yellow/amber banner: "⚠️ No domain restrictions. Widget is publicly accessible on ANY website."
  - [ ] Use shadcn/ui Alert component
  - [ ] Include a link to documentation on why to restrict domains

### 4) Backend - Domain Whitelist Storage

- [ ] Update `WidgetConfig` model:
  - [ ] Add field: `allowed_domains: List[str]` (JSON array)
  - [ ] Or create `AllowedDomain` junction table (one-to-many relationship)
  - [ ] Prefer JSON array for simplicity (PostgreSQL native support)

### 5) Backend - Domain Whitelist Endpoints

- [ ] Update `PUT /api/v1/bots/:bot_id/widget/config`:
  - [ ] Accept `allowed_domains: List[str]` in request body
  - [ ] Validate each domain:
    - [ ] Valid format (regex check)
    - [ ] Not duplicates
    - [ ] Max 50 domains per bot
  - [ ] Store in database
  - [ ] Return updated config with domains list

### 6) Backend - Server-Side Domain Verification

- [ ] Create middleware/decorator: `@verify_widget_origin`
  - [ ] Extract Origin or Referer header from request
  - [ ] Load bot's allowed_domains from database
  - [ ] If list empty: allow all (no restrictions)
  - [ ] If list not empty:
    - [ ] Check if Origin/Referer matches whitelist
    - [ ] Support wildcard matching: "*.example.com" matches "api.example.com"
    - [ ] Return 403 Forbidden if not matched
- [ ] Apply middleware to:
  - [ ] `GET /api/v1/bots/:bot_id/chat/query` endpoint
  - [ ] `GET /api/v1/bots/:bot_id/public` endpoint (optionally)

### 7) Backend - Origin Matching Logic

- [ ] Implement domain matching function:
  ```python
  def matches_whitelist(origin: str, allowed_domains: List[str]) -> bool:
      """
      Check if origin matches any allowed domain.
      Supports wildcards: *.example.com matches api.example.com
      """
      from urllib.parse import urlparse
      parsed = urlparse(origin)
      domain = parsed.netloc.lower()  # e.g., "api.example.com"
      
      for allowed in allowed_domains:
          if allowed.startswith('*.'):
              # Wildcard matching: *.example.com
              base = allowed[2:]  # "example.com"
              if domain.endswith('.' + base) or domain == base:
                  return True
          else:
              # Exact matching
              if domain == allowed.lower():
                  return True
      return False
  ```
- [ ] Test with various formats:
  - [ ] "example.com" matches "example.com"
  - [ ] "*.example.com" matches "api.example.com", "test.example.com"
  - [ ] "*.example.com" does NOT match "example.com" (if not explicitly added)

### 8) Frontend - Mobile Responsive CSS

- [ ] Update widget CSS for mobile:
  - [ ] Chat window scales to device width (max 100vw)
  - [ ] Font sizes responsive: 14px on mobile, 16px on desktop
  - [ ] Button sizes: 44x44px minimum
  - [ ] Spacing: 8px minimum between clickable elements
  - [ ] Use CSS media queries or Tailwind responsive prefixes

### 9) Frontend - Keyboard Handling (Mobile)

- [ ] Handle mobile keyboard appearance:
  - [ ] Use `visualViewport` API to detect keyboard presence
  - [ ] On keyboard show: scroll chat up so send button visible
  - [ ] On keyboard hide: reset scroll
  - [ ] Alternative: use window.innerHeight / window.visualViewport.height
- [ ] Test on real iOS/Android devices:
  - [ ] Safari on iPhone
  - [ ] Chrome on Android
  - [ ] Firefox on Android

### 10) Frontend - Viewport Meta Tag

- [ ] Ensure HTML has proper viewport meta tag:
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  ```
- [ ] Applied to both:
  - [ ] Main website (if it has single viewport tag, affects embedded widgets too)
  - [ ] Widget iframe (set via widget.js injection)

### 11) Testing - Component Tests

- [ ] Test WidgetSettings domain input:
  - [ ] Add valid domain (example.com)
  - [ ] Add wildcard domain (*.example.com)
  - [ ] Reject invalid format
  - [ ] Reject duplicate
  - [ ] Delete domain from list
- [ ] Test empty whitelist warning:
  - [ ] Shown when no domains added
  - [ ] Hidden when first domain added
- [ ] Use Vitest + React Testing Library

### 12) Testing - API Tests

- [ ] Test domain validation endpoint:
  - [ ] Valid domains accepted
  - [ ] Invalid formats rejected
  - [ ] Duplicates rejected
  - [ ] Max domain limit enforced
- [ ] Test origin verification:
  - [ ] Request from allowed domain: 200 OK
  - [ ] Request from unauthorized domain: 403 Forbidden
  - [ ] Wildcard matching works
  - [ ] Empty whitelist allows all origins
- [ ] Test Referer header fallback:
  - [ ] Use Referer if Origin header missing
  - [ ] Properly parse domain from Referer URL
- [ ] Use pytest + TestClient

### 13) Testing - Mobile Responsiveness

- [ ] Manual testing on real devices:
  - [ ] iPhone 12 / 13 / 14 (various sizes)
  - [ ] Android device (Samsung, Pixel)
  - [ ] Test in portrait and landscape
- [ ] Automated testing:
  - [ ] Playwright/Cypress viewport tests (mobile sizes)
  - [ ] 375x667 (iPhone SE), 412x915 (Pixel 5)
  - [ ] 768x1024 (iPad)
- [ ] Check for:
  - [ ] No horizontal scrolling
  - [ ] Text readable without zoom
  - [ ] Buttons touch-friendly (tap and verify hit areas)
  - [ ] Keyboard interactions work

### 14) Testing - Accessibility (Mobile)

- [ ] Screen reader testing on mobile:
  - [ ] VoiceOver on iOS
  - [ ] TalkBack on Android
  - [ ] Verify ARIA labels announced correctly
- [ ] Contrast testing:
  - [ ] Use WebAIM contrast checker
  - [ ] Verify 4.5:1 for text on mobile
  - [ ] Check in both light and dark modes (if applicable)

### 15) Testing - Browser Compatibility

- [ ] Test on:
  - [ ] Chrome 100+ (Linux, Windows, macOS)
  - [ ] Firefox 100+ (Linux, Windows, macOS)
  - [ ] Safari 14+ (macOS, iOS)
  - [ ] Edge 100+
  - [ ] Graceful degradation on older browsers (IE11 optional fallback)
- [ ] Use BrowserStack or local testing

### 16) Documentation & Deployment

- [ ] Create domain whitelist guide:
  - [ ] How to add allowed domains
  - [ ] Why domain restrictions are important
  - [ ] Wildcard vs exact domain matching
  - [ ] Examples and common use cases
- [ ] Add mobile testing guide:
  - [ ] How to test on iOS/Android
  - [ ] Common mobile issues and fixes
  - [ ] Performance testing on slow networks
- [ ] Update accessibility documentation:
  - [ ] WCAG 2.1 AA compliance checklist
  - [ ] Mobile accessibility best practices

## Dev Notes

### Architecture Patterns

- **Server-Side Verification**: Origin check on backend (client can't bypass)
- **Wildcard Matching**: Flexible domain control with *.example.com pattern
- **Graceful Degradation**: Empty whitelist = no restrictions (backward compatible)
- **Mobile-First CSS**: Responsive design from 320px up

### Component Reuse

- **From Story 4.5**: Extend WidgetSettings with domain whitelist UI
- **From Epic 2**: Reuse bot authorization patterns
- **From Epic 1**: Reuse error/alert messaging

### Security Considerations

- **Server-Side Enforcement**: Client-side domain checking is not secure (can be bypassed)
- **Origin vs Referer**: Origin header preferred (always present), Referer as fallback
- **Wildcard Limitations**: *.example.com allows all subdomains (use with caution)
- **Privacy**: Don't log domain whitelists in user-facing analytics

### Performance Optimization

- **Mobile Bundle**: Keep widget.js < 50KB to minimize impact on host pages
- **Lazy Loading**: Chat interface only fully initializes when widget clicked
- **Network**: Minimize requests on mobile (batching, caching)
- **Display**: Use CSS containment to improve rendering performance

### Learnings from Previous Stories

From Story 4.5 (Embeddable Widget) [Source: epic-4/story-4-5-embeddable-widget-generation.md]:

- **Widget Architecture**: Iframe sandboxing in place
- **Domain Configuration**: Already storing widget config in database (extend with domains)
- **Widget.js Bundle**: Performance considerations for mobile

From Epic 1 (Foundation) [Source: epic-1/story-1-*]:

- **Mobile-First Design**: Architecture supports responsive design
- **Authorization Patterns**: Reuse from BotService

### Dependencies & Blockers

- **Requires**: Story 4.5 (Widget generation) for widget infrastructure
- **Blocks**: Nothing (terminal story in Epic 4)
- **Optional**: Story 8.1 (Analytics) for widget domain usage metrics

### References

- Widget security specification: [Source: docs/epics.md#Story-4.6]
- Embeddable widget: [Source: epic-4/story-4-5-embeddable-widget-generation.md]
- UX/mobile design: [Source: docs/ux-design-specification.md]
- Security best practices: [Source: docs/prd.md#Security-and-Compliance]
- Accessibility: [Source: .bmad/bmm/testarch/knowledge/test-quality.md]

## Dev Agent Record

### Context Reference

<!-- Story context XML will be added by story-context workflow -->

### Agent Model Used

Claude Haiku 3.5

### Debug Log References

- Implement origin matching logic (wildcard support)
- Test mobile keyboard behavior on real iOS/Android devices
- Verify domain verification middleware
- Test browser compatibility

### Completion Notes List

- [ ] Domain whitelist UI works
- [ ] Domain validation prevents invalid entries
- [ ] Duplicate prevention works
- [ ] Server-side origin verification working
- [ ] Wildcard domain matching works
- [ ] Widget responsive on mobile devices
- [ ] Keyboard behavior correct (viewport adjustment)
- [ ] Touch targets 44x44px minimum
- [ ] Accessibility standards met (WCAG AA)
- [ ] Browser compatibility tested
- [ ] All unit tests passing
- [ ] All integration tests passing

### File List

**Created (NEW):**
- `apps/api/app/services/domain_whitelist_service.py` - Domain validation and matching
- `apps/web/__tests__/WidgetDomainWhitelist.test.tsx` - Domain UI tests
- `apps/api/tests/test_widget_domain_security.py` - Security tests

**Modified:**
- `apps/web/src/components/WidgetSettings.tsx` - Add domain whitelist UI
- `apps/api/app/models/widget_config.py` - Add allowed_domains field
- `apps/api/app/api/routes/widget.py` - Add origin verification middleware
- `apps/web/src/widget/widget.ts` - Mobile responsive CSS
- `apps/web/src/app/chat/[botId]/page.tsx` - Mobile viewport optimization

**Deleted:**
- None
