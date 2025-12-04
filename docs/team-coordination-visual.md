# Team Coordination Visual Guide

## 🎯 The Problem We Solved

### ❌ BEFORE (Chaotic)
```
Dev1 ──→ Story A ──┐
                    ├──→ CONFLICT! 💥
Dev2 ──→ Story A ──┘

Dev3 ──→ Story B (blocked!) ──→ WASTED TIME ⏰

Dev4 ──→ 5 stories at once ──→ NOTHING DONE 😵
```

### ✅ AFTER (Organized)
```
sprint-status.yaml (Single Source of Truth)
         │
         ├──→ Dev1: Story A (in-progress) ✓
         ├──→ Dev2: Story C (in-progress) ✓
         ├──→ Dev3: Story D (assigned) ⏳
         └──→ Dev4: Available (0/2 WIP) 🟢

Story B: blocked_by Story A → waiting ⏸️
```

---

## 📊 Sprint Status Structure

```yaml
team:
  developers:
    - name: Dev1
      max_wip: 2          # Can work on max 2 stories
      current_wip: 0      # Currently working on 0
      skills: [frontend, backend, auth]

development_status:
  1-4-user-login-session-management:
    status: ready-for-dev        # Current state
    assigned_to: null            # No owner yet
    blocked_by: null             # Not blocked
    
  1-5-team-invitation-role-assignment:
    status: ready-for-dev
    assigned_to: null
    blocked_by: 1-4-user-login-session-management  # BLOCKED!
```

---

## 🔄 Story Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     SCRUM MASTER ZONE                       │
│  ┌──────────┐      ┌──────────┐      ┌──────────────────┐  │
│  │ backlog  │ ───→ │ drafted  │ ───→ │ ready-for-dev    │  │
│  └──────────┘      └──────────┘      └──────────────────┘  │
└───────────────────────────────────────────┬─────────────────┘
                                            │
                                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     DEVELOPER ZONE                          │
│                                                              │
│  ┌──────────┐      ┌──────────────┐      ┌────────┐        │
│  │ assigned │ ───→ │ in-progress  │ ───→ │ review │        │
│  └──────────┘      └──────────────┘      └────────┘        │
│       ↑                                        │            │
│       │                                        ↓            │
│       │                                   ┌─────────┐       │
│       └───────────── (blocked) ───────────│  done   │       │
│                                           └─────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Who Updates What?

| Status | Updated By | Tool/Action |
|--------|-----------|-------------|
| `backlog` → `drafted` | SM | `*create-story` |
| `drafted` → `ready-for-dev` | SM | `*create-story-context` |
| `ready-for-dev` → `assigned` | Developer | `assign-story.ps1` |
| `assigned` → `in-progress` | Developer | Manual edit + commit |
| `in-progress` → `review` | Developer | Manual edit + commit |
| `review` → `done` | SM | After code review |

---

## 🚦 WIP Limit Enforcement

```
Dev1's Capacity:
┌─────────────────────────────┐
│ WIP: 2/2                    │  ← AT LIMIT
├─────────────────────────────┤
│ 🔨 Story A (in-progress)    │
│ 📋 Story B (assigned)       │
└─────────────────────────────┘
        ↓
   Can't take more!
   Must finish one first.


Dev2's Capacity:
┌─────────────────────────────┐
│ WIP: 0/2                    │  ← AVAILABLE
├─────────────────────────────┤
│ ✓ Available for work        │
└─────────────────────────────┘
        ↓
   Can take 2 stories!
```

---

## 🔗 Dependency Chain Example

```
Epic 1: Foundation & Auth
┌──────────────────────────────────────────────────────┐
│                                                      │
│  1-4: Login System ──┐                              │
│   status: in-progress │                             │
│   assigned_to: Dev1   │                             │
│                       │                             │
│                       ↓                             │
│  1-5: Team Invites ◄──┴─── blocked_by: 1-4         │
│   status: ready-for-dev                             │
│   assigned_to: null                                 │
│   ⚠️ WAITING FOR 1-4!                               │
│                                                      │
│                       ↓                             │
│  1-6: Profile Mgmt ◄───── blocked_by: 1-4          │
│   status: ready-for-dev                             │
│   assigned_to: null                                 │
│   ⚠️ WAITING FOR 1-4!                               │
│                                                      │
└──────────────────────────────────────────────────────┘

RESULT: Dev1 working on 1-4 unblocks 2 other stories!
```

---

## 📋 Daily Team Flow

```
Morning (9:00 AM)
─────────────────
All Devs:
  ↓
  git pull
  ↓
  .\scripts\team-status.ps1
  ↓
  See available work
  ↓
  Pick story
  ↓
  .\scripts\assign-story.ps1 <story> <name>
  ↓
  Start coding


During Day
──────────
  Code
  ↓
  Commit often
  ↓
  Push regularly
  ↓
  Update status when state changes


End of Day (5:00 PM)
────────────────────
  Push all commits
  ↓
  Update sprint-status.yaml
  ↓
  If done → status: review
  ↓
  If blocked → update blocked_by
  ↓
  Team sync tomorrow
```

---

## 🎭 Team Coordination Scenarios

### Scenario 1: Perfect Day ✅
```
09:00 - team-status.ps1 shows:
  ⭐ 1-4 available
  ⭐ 2-1 available (but blocked by 1-4)
  
Dev1: Takes 1-4 (login system)
Dev2: Takes 2-1 (wait... blocked by 1-4!) ❌
      Checks again, takes different work ✅

Result: No conflicts, smooth workflow
```

### Scenario 2: Race Condition ⚠️
```
09:00 - Both Dev1 and Dev2 want Story 1-4

Dev1: 09:00:15 - assign-story.ps1 1-4 Dev1 → commit → push ✅
Dev2: 09:00:30 - assign-story.ps1 1-4 Dev2 → CONFLICT! ❌

Git shows:
  ! [rejected] Your branch is behind
  
Dev2: git pull → sees 1-4 taken → picks 1-5 instead ✅

Prevention: Quick assign, quick commit, quick push!
```

### Scenario 3: Mid-Sprint Block 🚧
```
Day 1: Dev3 starts Story 2-3 (document upload)
       Status: in-progress
       
Day 2: Dev3 discovers needs API change from Story 2-1
       Action: Update sprint-status.yaml
       
       2-3-document-upload-api:
         status: assigned  (moved back)
         blocked_by: 2-1-bot-creation-configuration
         
       Dev3 picks different work while blocked
       
Day 3: Dev2 completes 2-1
       Dev3 resumes 2-3 ✅

Result: No wasted time, clear communication
```

---

## 🛠️ Tool Ecosystem

```
┌─────────────────────────────────────────────────┐
│          sprint-status.yaml                     │
│      (Single Source of Truth)                   │
└───────┬────────────────────────┬────────────────┘
        │                        │
        ↓                        ↓
┌──────────────┐        ┌───────────────┐
│team-status   │        │assign-story   │
│.ps1          │        │.ps1           │
│              │        │               │
│View who's    │        │Claim stories  │
│working on    │        │automatically  │
│what          │        │with validation│
└──────────────┘        └───────────────┘
        │                        │
        ↓                        ↓
┌──────────────────────────────────────┐
│         Developer Actions             │
│  • Check status                       │
│  • Assign stories                     │
│  • Update progress                    │
│  • Commit changes                     │
└──────────────────────────────────────┘
```

---

## 📈 Success Metrics

### Good Team Coordination
```
✅ Zero assignment conflicts
✅ All devs respect WIP limits
✅ Blocked stories identified quickly
✅ sprint-status.yaml always up-to-date
✅ Regular commits and pushes
```

### Red Flags
```
❌ Multiple devs on same story
❌ WIP limits exceeded
❌ Stories blocked but devs working on them
❌ sprint-status.yaml outdated
❌ Infrequent commits (< 1 per day)
```

---

## 🎯 Quick Decision Tree

```
Want to start new work?
  │
  ├─→ Run team-status.ps1
  │     │
  │     ├─→ Your WIP ≥ 2?
  │     │     └─→ YES: Finish current work first ❌
  │     │     └─→ NO: Continue ✓
  │     │
  │     ├─→ Story available?
  │     │     └─→ YES: Continue ✓
  │     │     └─→ NO: Wait for SM to draft more ⏳
  │     │
  │     ├─→ Story blocked?
  │     │     └─→ YES: Pick different story ❌
  │     │     └─→ NO: Continue ✓
  │     │
  │     ├─→ Story already assigned?
  │     │     └─→ YES: Pick different story ❌
  │     │     └─→ NO: Continue ✓
  │     │
  │     └─→ All clear!
  │           │
  │           └─→ git pull
  │                 │
  │                 └─→ assign-story.ps1
  │                       │
  │                       └─→ Start coding! 🎉
```

---

## 💡 Pro Tips

1. **Morning Sync**
   - First thing: `git pull && .\scripts\team-status.ps1`
   - Prevents assignment conflicts

2. **Atomic Commits**
   - Assign story → commit → push IMMEDIATELY
   - Don't wait hours to push assignment

3. **Help Unblock Others**
   - If your story unblocks 2 others, prioritize it!
   - Check `blocked_by` references

4. **Pair on Complex Stories**
   - Both devs can work together
   - Keep `assigned_to` as primary owner
   - Count as 1 WIP for each dev

5. **End-of-Day Cleanup**
   - Push everything
   - Update all status changes
   - Tomorrow's you will thank you!

---

*This visual guide complements `team-coordination.md`*  
*Print this and keep it at your desk!*
