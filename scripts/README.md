# Team Coordination Scripts

Quick-reference guide for the team coordination automation scripts.

---

## 📊 team-status.ps1

View real-time team status and available work.

### Usage

```powershell
# View full team dashboard
.\scripts\team-status.ps1

# View specific developer's status
.\scripts\team-status.ps1 -Developer Dev1
```

### Output

```
🚀 VERIPLY TEAM STATUS - 2025-12-04 10:20
═══════════════════════════════════════════

👤 Dev1 - WIP: 1/2
─────────────────────────────────────────
  🔨 1-4-user-login-session-management

👤 Dev2 - WIP: 0/2
─────────────────────────────────────────
  ✓ Available for work

📋 AVAILABLE FOR ASSIGNMENT
═══════════════════════════════════════════
  ⭐ 1-5-team-invitation-role-assignment
```

### Icons

| Icon | Meaning |
|------|---------|
| 🔨 | In progress |
| 📋 | Assigned but not started |
| 👀 | In review |
| ✅ | Completed |
| ⭐ | Available for assignment |
| ✓ | Developer available |

---

## 📝 assign-story.ps1

Assign stories to developers with automatic validation.

### Usage

```powershell
# Assign story (claim it)
.\scripts\assign-story.ps1 <story-id> <developer>

# Assign and start immediately
.\scripts\assign-story.ps1 <story-id> <developer> -StartNow
```

### Examples

```powershell
# Claim story 1-4 for Dario
.\scripts\assign-story.ps1 1-4-user-login-session-management Dario

# Claim and start story 1-5 for Lucas
.\scripts\assign-story.ps1 1-5-team-invitation-role-assignment Lucas -StartNow
```

### What It Does

1. ✅ Pulls latest changes from git
2. ✅ Validates developer name exists
3. ✅ Checks developer WIP limit (max 2)
4. ✅ Verifies story is ready for assignment
5. ✅ Warns if story is blocked
6. ✅ Updates sprint-status.yaml
7. ✅ Commits and pushes changes
8. ✅ Shows next steps

### Validations

| Check | Error Message |
|-------|---------------|
| Invalid dev | "Invalid developer: Dev5" |
| WIP limit | "Dev1 already has 2 stories (WIP limit: 2)" |
| Story taken | "Story status is 'assigned', not ready" |
| Story blocked | "WARNING: Story is blocked by: 1-4..." |

---

## 🎯 Daily Workflow

### Morning (Start of Day)

```powershell
# 1. Navigate to project
cd "C:\Users\Dario\...\Veriply"

# 2. Pull latest changes
git pull origin main

# 3. Check team status
.\scripts\team-status.ps1

# 4. Pick available work
# Look for ⭐ stories under "AVAILABLE FOR ASSIGNMENT"

# 5. Assign yourself
.\scripts\assign-story.ps1 1-4-user-login-session-management Dev1

# 6. Start work when ready
.\scripts\assign-story.ps1 1-4-user-login-session-management Dev1 -StartNow
```

### During Work

```powershell
# Check your current status
.\scripts\team-status.ps1 -Developer Dev1

# Check if blockers resolved
.\scripts\team-status.ps1
```

### End of Day

- Commit and push your code
- Manually update story status if changed (in sprint-status.yaml)
- Run team-status.ps1 to see tomorrow's work

---

## 🔧 Manual Status Updates

Sometimes you need to manually update `sprint-status.yaml`:

### Move to In-Progress

After assigning with `assign-story.ps1`, when you actually start:

```yaml
1-4-user-login-session-management: 
  status: in-progress  # Change from assigned
  assigned_to: Dev1
  blocked_by: null
```

Then commit:
```powershell
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Start work on 1-4-user-login-session-management"
git push
```

### Move to Review

When you finish coding and push PR:

```yaml
1-4-user-login-session-management: 
  status: review  # Change from in-progress
  assigned_to: Dev1
  blocked_by: null
```

Then commit:
```powershell
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Complete 1-4-user-login-session-management - ready for review"
git push
```

### Mark as Blocked

If you discover a dependency:

```yaml
2-3-document-upload-api:
  status: assigned  # Move back from in-progress
  assigned_to: Dev2
  blocked_by: 2-1-bot-creation-configuration  # Add blocker
```

Then commit:
```powershell
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Block 2-3 pending 2-1 completion"
git push
```

---

## 🚨 Troubleshooting

### Script Won't Run

**Error:** "Cannot find path 'team-status.ps1'"

**Solution:**
```powershell
# Make sure you're in project root
cd "C:\Users\Dario\OneDrive - Erasmushogeschool Brussel\Erasmus Hogeschool\2025-2026\IT Project\Veriply"

# Then run with .\scripts\ prefix
.\scripts\team-status.ps1
```

### Git Conflicts

**Error:** "Pull failed! Resolve conflicts first"

**Solution:**
```powershell
# Check git status
git status

# Pull and resolve
git pull origin main

# Fix conflicts in sprint-status.yaml
# Then:
git add docs/sprint-artifacts/sprint-status.yaml
git commit -m "Resolve sprint status conflict"
git push
```

### Push Failed

**Error:** "Push failed! Resolve conflicts manually"

**Solution:**
```powershell
# Someone else assigned the story first
git pull origin main

# Check who got it
.\scripts\team-status.ps1

# Pick different story
.\scripts\assign-story.ps1 <different-story> Dev1
```

---

## 📋 Developer Names

Valid developer names (case-sensitive):

- `Dario`
- `Lucas`
- `Kainy`
- `Soulaymane`

To add more developers, edit `docs/sprint-artifacts/sprint-status.yaml`:

```yaml
team:
  size: 5
  developers:
    - name: NewDev
      max_wip: 2
      current_wip: 0
      skills: [frontend, backend]
```

---

## 🎨 Customization

### Change WIP Limit

Edit `sprint-status.yaml`:

```yaml
- name: Dev1
  max_wip: 3  # Increase from 2
```

### Add Skills

Edit `sprint-status.yaml`:

```yaml
- name: Dev1
  skills: [frontend, backend, auth, docker]  # Add more
```

---

## 📖 Additional Documentation

- **Complete Guide:** `docs/team-coordination.md`
- **Quick Reference:** `docs/TEAM-QUICK-REF.md`
- **Visual Guide:** `docs/team-coordination-visual.md`
- **Setup Summary:** `docs/team-coordination-setup.md`

---

## 💡 Tips

1. **Run team-status.ps1 often** - Stay aware of team capacity
2. **Assign quickly** - First commit wins on popular stories
3. **Check blockers** - Don't start blocked stories
4. **Update immediately** - Status changes = instant commit
5. **Help teammates** - Review PRs while waiting

---

*For questions, read `docs/team-coordination.md` or ask SM via `*help`*
