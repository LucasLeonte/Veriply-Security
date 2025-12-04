# 🚀 VERIPLY TEAM - QUICK REFERENCE

## Before You Start Coding

```powershell
# 1. Check who's working on what
.\scripts\team-status.ps1

# 2. Pull latest changes
git pull origin main

# 3. Assign yourself to a story
.\scripts\assign-story.ps1 <story-id> <your-name>

# Example:
.\scripts\assign-story.ps1 1-4-user-login-session-management Dev1
```

---

## Story Assignment Rules

✅ **DO:**
- Check `team-status.ps1` before picking work
- Assign yourself BEFORE coding
- Respect WIP limit (max 2 stories)
- Check `blocked_by` dependencies
- Pull before assign, push after assign

❌ **DON'T:**
- Start coding without assignment
- Take stories assigned to others
- Exceed WIP limit (2 stories)
- Start blocked stories
- Force push over conflicts

---

## Quick Commands

```powershell
# View team status
.\scripts\team-status.ps1

# View your status only
.\scripts\team-status.ps1 -Developer Dario

# Assign story (claim it)
.\scripts\assign-story.ps1 1-4-user-login-session-management Dario

# Assign and start immediately
.\scripts\assign-story.ps1 1-4-user-login-session-management Dario -StartNow

# Check available stories
.\scripts\team-status.ps1 | Select-String "⭐"
```

---

## Story Status Flow

```
ready-for-dev → assigned → in-progress → review → done
     ↑             ↓           ↓           ↓
   (SM)         (You)       (You)       (You)      (SM)
```

**Your actions:**
1. Assign yourself → status: `assigned`
2. Start coding → status: `in-progress`
3. Finish work → status: `review`
4. SM approves → status: `done`

---

## Daily Workflow

### Morning (9:00 AM)
```powershell
cd "C:\...\Veriply"
git pull origin main
.\scripts\team-status.ps1
# Pick story, assign yourself, start work
```

### During Work
- Commit regularly (every feature/fix)
- Push at least once per day
- Update status in sprint-status.yaml when state changes

### End of Day (5:00 PM)
- Push all commits
- Update story status if completed
- Check blockers for tomorrow

---

## When Stuck

1. **Story blocked?**
   - Update `blocked_by` field
   - Pick different story
   - Help teammates unblock

2. **Assignment conflict?**
   - First commit wins
   - Pick different story
   - Don't force push!

3. **Need help?**
   - Ask in team chat
   - Pair program
   - Tag story owner

---

## Team Members

| Dev | Max WIP | Skills |
|-----|---------|--------|
| Dario | 2 | frontend, backend, auth |
| Lucas | 2 | backend, database, api |
| Kainy | 2 | frontend, ui, testing |
| Soulaymane | 2 | fullstack, devops, integration |

---

## Current Sprint Focus

**Epic 1: Foundation & Auth**
- ✅ 1-1-project-infrastructure-setup (Dario) - DONE
- ✅ 1-2-database-schema-multi-tenancy-foundation (Dario) - DONE
- ✅ 1-3-user-registration-tenant-creation (Dario) - DONE
- 📋 1-4-user-login-session-management (Lucas) - ASSIGNED
- ⏸️ 1-5-team-invitation-role-assignment - BLOCKED by 1-4
- ⏸️ 1-6-user-profile-team-management - BLOCKED by 1-4

**Next:** Lucas completes 1-4 to unblock 1-5 and 1-6

---

## File Locations

| File | Purpose |
|------|---------|
| `docs/sprint-artifacts/sprint-status.yaml` | Master tracking file |
| `docs/team-coordination.md` | Full coordination guide |
| `docs/sprint-artifacts/*.md` | Story files |
| `docs/sprint-artifacts/*.context.xml` | Story context (dev reference) |
| `scripts/team-status.ps1` | Team dashboard |
| `scripts/assign-story.ps1` | Story assignment helper |

---

## Emergency Contacts

- **SM (Scrum Master):** Run `*help` in Copilot
- **Coordination Issues:** Read `docs/team-coordination.md`
- **Story Questions:** Check story .md and .context.xml files

---

## Remember

💡 **Golden Rule:** sprint-status.yaml is single source of truth  
🔒 **WIP Limit:** Max 2 stories per developer  
🤝 **Communication:** Update status → commit → push → notify team  
📋 **Before coding:** Assign → Pull → Code → Push → Review

---

*Last Updated: 2025-12-04*  
*Version: 1.0*
