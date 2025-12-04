# Team Coordination Guide - Veriply

**Team Size:** 4 Developers  
**WIP Limit:** 2 stories per developer  
**Last Updated:** 2025-12-04

---

## 🎯 Quick Rules

1. **Check before you start** - Run `.\scripts\team-status.ps1` to see what's available
2. **Assign yourself first** - Update `sprint-status.yaml` before coding
3. **Respect WIP limits** - Max 2 in-progress stories per person
4. **Check dependencies** - Look at `blocked_by` field before starting
5. **Update status regularly** - Keep the team informed

---

## 📋 Story Assignment Workflow

### Step 1: Find Available Work
```powershell
# See all team status
.\scripts\team-status.ps1

# Check your own status
.\scripts\team-status.ps1 -Developer Dev1
```

### Step 2: Pick a Story
From the "AVAILABLE FOR ASSIGNMENT" section, choose a story where:
- ✅ Status is `ready-for-dev`
- ✅ `blocked_by: null` (not blocked)
- ✅ Matches your skills
- ✅ Your WIP < 2

### Step 3: Assign Yourself
Edit `docs/sprint-artifacts/sprint-status.yaml`:

```yaml
1-4-user-login-session-management: 
  status: assigned        # Change from ready-for-dev
  assigned_to: Dev1       # Add your name (not null)
  blocked_by: null
```

### Step 4: Commit Assignment
```powershell
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Assign 1-4-user-login-session-management to Dev1"
git push
```

### Step 5: Start Work
```yaml
1-4-user-login-session-management: 
  status: in-progress     # Change from assigned
  assigned_to: Dev1
  blocked_by: null
```

Commit again:
```powershell
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Start work on 1-4-user-login-session-management"
git push
```

---

## 🔄 Story Status Transitions

```
ready-for-dev → assigned → in-progress → review → done
     ↑             ↓           ↓
     └─────────────┴───────────┘
     (unassign if blocked/changed)
```

### Status Meanings

| Status | Who Updates | When |
|--------|-------------|------|
| `ready-for-dev` | SM | Story drafted + context created |
| `assigned` | Developer | You claim the story |
| `in-progress` | Developer | You start coding |
| `review` | Developer | You finish + push PR |
| `done` | SM | After code review passes |

---

## 🚫 Conflict Prevention

### Rule 1: One Owner Per Story
- Only ONE `assigned_to` per story
- If you see a name, don't take it
- If you want to help, coordinate with owner first

### Rule 2: WIP Limits
- Each dev max 2 stories in `assigned` or `in-progress`
- Finish before starting new work
- Exception: One story blocked? Pick a second

### Rule 3: Check Dependencies
```yaml
1-5-team-invitation-role-assignment: 
  status: ready-for-dev
  assigned_to: null
  blocked_by: 1-4-user-login-session-management  # ⚠️ WAIT FOR THIS
```

**Don't start a story if its `blocked_by` story isn't `done` yet.**

### Rule 4: Pull Before Assign
```powershell
# ALWAYS pull latest before assigning yourself
git pull origin main
```

Someone else might have just claimed it!

---

## 🛠️ Parallel Work Strategy

### Epic 1 Foundation (Current)
- **3 ready stories, 0 blockers**
- Can work in parallel:
  - Dev1 → `1-4-user-login-session-management`
  - Dev2 → `1-5-team-invitation-role-assignment` (blocked by 1-4)
  - Dev3 → `1-6-user-profile-team-management` (blocked by 1-4)

**Recommendation:** Dev1 starts 1-4 first, others wait or help with testing.

### Later Epics
- Epic 2 blocked until 1-4 done
- Multiple stories can run parallel once dependencies clear
- Coordinate in team chat before starting

---

## 📊 Daily Standup Checks

Each developer should answer:

1. **What did I complete?**
   - Stories moved to `review` or `done`
   
2. **What am I working on?**
   - Stories in `in-progress` status
   
3. **Am I blocked?**
   - Waiting on another story?
   - Update `blocked_by` field

Run `.\scripts\team-status.ps1` at start of standup for team view.

---

## 🔧 Common Scenarios

### Scenario: Two Devs Want Same Story
1. First one to **commit assignment** wins
2. Second dev gets merge conflict
3. Second dev picks different story

**Prevention:** Quick assign → quick commit → quick push

### Scenario: Story is Harder Than Expected
1. Ask for help in team chat
2. Consider splitting story (talk to SM)
3. Another dev can be temporarily added (pair programming)
4. Don't change `assigned_to` without coordinating

### Scenario: Dependencies Changed
1. If your story gets blocked mid-work:
   ```yaml
   blocked_by: 2-1-bot-creation-configuration  # Add blocker
   ```
2. Move status back to `assigned` or `ready-for-dev`
3. Pick different work while blocked

### Scenario: Emergency Bug Fix
1. Ask SM to create urgent story
2. SM sets `assigned_to` immediately
3. Dev pauses current work (don't exceed WIP limit)

---

## 🎨 Skill-Based Assignment

Update your skills in `sprint-status.yaml`:

```yaml
team:
  developers:
    - name: Dev1
      skills: [frontend, backend, auth]  # ← Update these
```

When picking stories:
- Match story requirements to your skills
- Stretch assignments ok if team capacity allows
- Pair with skilled dev for learning

---

## 📞 Communication

### Before Starting
- Pull latest sprint-status.yaml
- Check team chat for updates
- Verify story not taken

### During Work
- Update status when state changes
- Commit regularly (push daily minimum)
- Report blockers immediately

### After Completion
- Move to `review`
- Ping SM in chat
- Help review others' PRs while waiting

---

## 🚀 Example Flow

**Dev2 picks up new story:**

```powershell
# 1. Check status
cd "C:\Users\Dario\OneDrive - Erasmushogeschool Brussel\Erasmus Hogeschool\2025-2026\IT Project\Veriply"
.\scripts\team-status.ps1

# Output shows:
# 👤 Dev2 - WIP: 0/2
# ✓ Available for work
#
# 📋 AVAILABLE FOR ASSIGNMENT
# ⭐ 1-4-user-login-session-management

# 2. Pull latest
git pull origin main

# 3. Edit sprint-status.yaml
# Change 1-4 to: assigned_to: Dev2, status: assigned

# 4. Commit assignment
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Assign 1-4-user-login-session-management to Dev2"
git push

# 5. Start coding
# (update story context if needed)

# 6. Update to in-progress
# Edit sprint-status.yaml: status: in-progress
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Start 1-4-user-login-session-management"
git push

# 7. Code, test, commit
git add .
git commit -m "Implement user login endpoint"
git push

# 8. Finish work
# Edit sprint-status.yaml: status: review
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Complete 1-4-user-login-session-management - ready for review"
git push

# 9. Notify SM in chat
# "Story 1-4 ready for review"
```

---

## 📈 Metrics to Track

Track these weekly:
- Stories completed per dev
- Average story duration
- WIP violations (should be 0)
- Assignment conflicts (should be 0)

SM runs retrospective to review coordination effectiveness.

---

## ⚡ Quick Commands

```powershell
# View full team status
.\scripts\team-status.ps1

# View your status
.\scripts\team-status.ps1 -Developer Dev1

# Pull before starting work
git pull origin main

# Commit status change
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Update story status"
git push
```

---

## 🎓 Best Practices

1. **Morning routine:** Pull latest → Check status → Assign work
2. **Commit small:** Don't wait days to push
3. **Update often:** Status changes = immediate commit
4. **Help others:** Review PRs, unblock teammates
5. **Ask early:** Stuck? Don't wait hours to ask
6. **Document:** Add notes to stories if you learn something

---

## 🆘 When Coordination Breaks

If you see conflicts or confusion:

1. **Stop** - Don't force push
2. **Communicate** - Team chat immediately  
3. **Check** - Run team-status.ps1
4. **Resolve** - Talk to story owner
5. **Update** - SM fixes sprint-status.yaml if needed

**Remember:** The sprint-status.yaml file is the single source of truth!

---

*Questions? Ask SM (Scrum Master agent) via `*help` command.*
