# Moderation Guide: Handling Feedback Alerts

## Overview

This guide explains how to monitor, triage, and respond to feedback-related moderation alerts in Veriply. The feedback system automatically detects patterns of harmful content and abusive user behavior, creating alerts that require human review.

---

## Alert Types

### 1. Moderation Alerts (Harmful Content)

**What it is:** Automatically created when 3+ users mark the same bot answer as "harmful" within 24 hours.

**Purpose:** Identifies bot responses that may contain:
- Offensive, discriminatory, or hateful language
- Misinformation or dangerous advice
- Privacy violations or leaked sensitive data
- Malicious links or phishing attempts

**Data Included:**
- `answer_id`: The specific bot response flagged
- `bot_id`: Which bot generated the response
- `feedback_count`: Number of users who marked it harmful (minimum 3)
- `user_ids`: Comma-separated list of users who reported it
- `created_at`: When the threshold was reached

### 2. User Abuse Suspicions

**What it is:** Automatically flagged when a single user submits 5+ "harmful" feedback within 1 hour.

**Purpose:** Detects users who may be:
- Attempting to game or sabotage the feedback system
- Mass-reporting content maliciously
- Testing bot boundaries with harmful prompts

**Data Included:**
- `user_id`: The flagged user's ID
- `bot_id`: Which bot received the feedback
- `feedback_ids`: Comma-separated list of feedback submissions (minimum 5)
- `ip_address`: User's IP address for investigation
- `created_at`: When the threshold was reached

---

## Access Control

### Who Can View Alerts?

**Moderation Alerts:**
- All authenticated users within the tenant
- Access via: `GET /moderation/alerts`
- Optional filtering by `bot_id`

**User Abuse Suspicions:**
- **Admin-only** (requires admin role in JWT token)
- Access via: `GET /moderation/abuse-suspicions`
- Optional filtering by `bot_id`

### Why the Difference?
- Moderation alerts focus on content issues (public concern)
- Abuse suspicions involve user investigation (privacy-sensitive)

---

## Alert Workflow

### Step 1: Monitor for New Alerts

**Recommended:** Set up automated notifications (see "Notification System" section)

**Manual Check:**
```bash
# Check moderation alerts
curl -X GET https://api.veriply.com/moderation/alerts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check abuse suspicions (admin only)
curl -X GET https://api.veriply.com/moderation/abuse-suspicions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Dashboard Integration:**
- Display alert count on admin dashboard
- Badge notification for new alerts
- Daily/weekly email digest of pending alerts

### Step 2: Triage the Alert

#### For Moderation Alerts (Harmful Content):

1. **Retrieve the flagged answer:**
   - Query your message/answer database using `answer_id`
   - Review the full conversation context (original question + bot response)

2. **Assess severity:**
   - **Critical:** Immediate safety concern (violence, self-harm, illegal activity)
   - **High:** Offensive content, misinformation, privacy violation
   - **Medium:** Inappropriate tone, poor quality answer
   - **Low/False Positive:** Users misunderstood feedback options

3. **Review user feedback:**
   - Check if users left `additional_notes` with more context
   - Query: `SELECT * FROM feedback WHERE answer_id = '{answer_id}' AND reason = 'harmful'`
   - Look for patterns: Are all complaints about the same issue?

#### For User Abuse Suspicions:

1. **Review user's feedback history:**
   - Query: `SELECT * FROM feedback WHERE user_id = '{user_id}' ORDER BY created_at DESC LIMIT 50`
   - Check: Are all "harmful" tags legitimate concerns or spam?

2. **Check IP address patterns:**
   - Compare with known VPN/proxy ranges
   - Look for multiple accounts from same IP

3. **Assess intent:**
   - **Legitimate User:** May be frustrated, testing limits, or genuinely finding issues
   - **Bad Actor:** Systematic spam, malicious reporting, coordinated attacks

### Step 3: Take Action

#### Moderation Alert Actions:

**If content is genuinely harmful:**
1. ✅ **Remove/Update Bot Response:**
   - Delete the answer from the database
   - Update bot's knowledge base to prevent recurrence
   - Add to content filter/block list

2. ✅ **Notify Users:**
   - Send apology message to affected users
   - Explain corrective action taken

3. ✅ **Log Resolution:**
   - Document what was found and fixed
   - Update bot training data
   - Create incident report for compliance

**If content is acceptable (false positive):**
1. ✅ **Verify User Understanding:**
   - Review if users misunderstood "harmful" option
   - Consider UI improvements to feedback form

2. ✅ **Dismiss Alert:**
   - Mark as resolved in your tracking system
   - Document reasoning

#### User Abuse Actions:

**If user is legitimately frustrated:**
1. ✅ **Reach Out:**
   - Send personalized support message
   - Offer to help resolve their issues
   - Explain feedback system purpose

**If user is abusive:**
1. ✅ **Temporary Measures:**
   - Increase rate limiting for this user
   - Add to watch list for monitoring

2. ✅ **Escalation:**
   - If pattern continues: Suspend feedback privileges
   - If severe: Suspend account (following your TOS)
   - Document for legal compliance

### Step 4: Document & Learn

**Required Documentation:**
- Alert ID and timestamp
- Triage findings (severity, content summary)
- Action taken (removed, updated, dismissed)
- Resolution time
- Follow-up needed (yes/no)

**Analytics to Track:**
- Alert volume over time
- False positive rate
- Average time to resolution
- Top categories of harmful content
- Repeat offender users

---

## Notification System

### Email Alerts (Recommended)

Configure your system to send email notifications when:
- New moderation alert created (3+ harmful feedback)
- User abuse suspicion flagged (5+ harmful in 1h)
- Weekly digest of unresolved alerts

**Example Email Template:**

```
Subject: [Veriply] Moderation Alert: Bot #{bot_id} Answer Flagged

Hi Team,

A bot answer has been flagged as harmful by 3+ users:

- Bot ID: {bot_id}
- Answer ID: {answer_id}
- Feedback Count: {feedback_count}
- User IDs: {user_ids}
- Timestamp: {created_at}

Action Required:
1. Review the flagged answer in the dashboard
2. Determine if content should be removed/updated
3. Mark alert as resolved when complete

View Alert: https://app.veriply.com/moderation/alerts/{alert_id}

---
Veriply Moderation System
```

### Webhook Integrations

Send alert data to external tools:
- **Slack:** Post to #moderation-alerts channel
- **PagerDuty:** Escalate critical alerts
- **Jira:** Create tickets for tracking

**Webhook Payload Example:**
```json
{
  "event": "moderation_alert_created",
  "alert_id": "uuid",
  "bot_id": "uuid",
  "answer_id": "uuid",
  "feedback_count": 3,
  "user_ids": ["uuid1", "uuid2", "uuid3"],
  "severity": "high",
  "created_at": "2026-01-06T12:00:00Z"
}
```

---

## Best Practices

### 1. Response Time SLAs

**Recommended Targets:**
- Critical alerts: Review within 1 hour
- High severity: Review within 4 hours
- Medium/Low: Review within 24 hours

### 2. Team Structure

**Moderation Team Roles:**
- **L1 Reviewer:** Initial triage, dismisses false positives
- **L2 Moderator:** Makes removal/update decisions
- **L3 Admin:** Handles user suspensions, escalations

### 3. Regular Audits

**Monthly Review:**
- Sample 10% of resolved alerts for quality check
- Identify recurring issues with bot training
- Update moderation guidelines based on new patterns

### 4. Privacy & Compliance

**Data Handling:**
- Limit access to user_ids and IP addresses
- Log all moderator actions for audit trail
- Anonymize data in public reports
- Comply with GDPR right-to-erasure (delete user feedback on request)

### 5. Continuous Improvement

**Feedback Loop:**
- Track which bot responses get flagged most often
- Identify knowledge gaps in bot training data
- Update content filters based on alert patterns
- Refine detection thresholds (e.g., adjust from 3 to 4 harmful reports)

---

## Escalation Path

### When to Escalate to Leadership

- **Immediate:** Safety threats, illegal activity, data breach
- **Within 24h:** Coordinated abuse campaign, repeat offender patterns
- **Weekly Report:** Trends in harmful content, bot performance issues

### External Escalation

- **Legal Team:** Content that may violate laws or regulations
- **Product Team:** Systemic bot failures causing repeated alerts
- **Customer Success:** Users who need personalized support

---

## FAQ

**Q: Can users see how many people flagged an answer as harmful?**  
A: No, only moderators with API access can see `feedback_count`.

**Q: Are users notified when their flagged content is reviewed?**  
A: Not automatically - you must implement custom notifications.

**Q: What if the same answer gets flagged again after we dismiss the alert?**  
A: The system creates a new alert if 3+ additional harmful reports arrive. Consider if dismissal was correct.

**Q: Can we adjust the thresholds (3 harmful, 5 abusive)?**  
A: Yes, these are configurable in `feedback_service.py` - adjust based on your user base size.

**Q: How long are alerts stored?**  
A: Indefinitely for audit trail. Implement your own retention policy if needed.

---

## Technical Reference

### Database Tables

```sql
-- Moderation alerts
SELECT * FROM moderation_alerts 
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- User abuse suspicions
SELECT * FROM user_abuse_suspicions
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;

-- Related feedback
SELECT * FROM feedback
WHERE answer_id = '{answer_id}' 
  AND reason = 'harmful'
ORDER BY created_at DESC;
```

### Code References

- Alert creation logic: `apps/api/app/services/feedback_service.py`
  - `_maybe_create_moderation_alert()` (line ~160)
  - `_maybe_flag_user_abuse()` (line ~190)
- API endpoints: `apps/api/app/api/routes/feedback.py`
- Tests: `apps/api/tests/test_feedback_moderation.py`

---

## Contact & Support

For questions about moderation alerts:
- **Internal:** #moderation-support Slack channel
- **External:** moderation@veriply.com
- **Escalations:** security@veriply.com

---

*Last Updated: January 6, 2026*  
*Version: 1.0*
