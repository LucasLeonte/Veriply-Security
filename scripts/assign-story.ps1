# Assign Story to Developer
# Quick assignment helper

param(
    [Parameter(Mandatory=$true)]
    [string]$StoryID,
    
    [Parameter(Mandatory=$true)]
    [string]$Developer,
    
    [switch]$StartNow
)

$sprintFile = "$PSScriptRoot\..\docs\sprint-artifacts\sprint-status.yaml"

if (-not (Test-Path $sprintFile)) {
    Write-Host "❌ Sprint status file not found!" -ForegroundColor Red
    exit 1
}

# Pull latest first
Write-Host "📥 Pulling latest changes..." -ForegroundColor Cyan
git pull origin main | Out-Null

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Pull failed! Resolve conflicts first." -ForegroundColor Yellow
    exit 1
}

# Read current status
$content = Get-Content $sprintFile -Raw
$lines = Get-Content $sprintFile

# Validate developer exists
$validDevs = @('Dario', 'Lucas', 'Kainy', 'Soulaymane')
if ($Developer -notin $validDevs) {
    Write-Host "❌ Invalid developer: $Developer" -ForegroundColor Red
    Write-Host "Valid options: Dario, Lucas, Kainy, Soulaymane" -ForegroundColor Gray
    exit 1
}

# Check developer WIP
$devWIP = 0
foreach ($line in $lines) {
    if ($line -match "assigned_to:\s*$Developer") {
        $idx = [array]::IndexOf($lines, $line)
        if ($idx -gt 0) {
            $prevLine = $lines[$idx - 1]
            if ($prevLine -match 'status:\s*(assigned|in-progress)') {
                $devWIP++
            }
        }
    }
}

if ($devWIP -ge 2) {
    Write-Host "❌ $Developer already has $devWIP stories in progress (WIP limit: 2)" -ForegroundColor Red
    Write-Host "Finish current work before taking new stories." -ForegroundColor Yellow
    exit 1
}

# Find story
$storyFound = $false
$storyBlocked = $false
$blockedBy = $null
$currentStatus = $null
$currentAssigned = $null

$inStory = $false
foreach ($line in $lines) {
    if ($line -match "^\s+$StoryID\:\s*$") {
        $storyFound = $true
        $inStory = $true
        continue
    }
    
    if ($inStory) {
        if ($line -match '^\s+status:\s*(.+)$') {
            $currentStatus = $Matches[1].Trim()
        }
        
        if ($line -match '^\s+assigned_to:\s*(.+)$') {
            $currentAssigned = $Matches[1].Trim()
        }
        
        if ($line -match '^\s+blocked_by:\s*(.+)$') {
            $blockedBy = $Matches[1].Trim()
            if ($blockedBy -ne 'null') {
                $storyBlocked = $true
            }
        }
        
        # Exit if we hit next story
        if ($line -match '^\s+\d+-\d+-.+:\s*$') {
            break
        }
    }
}

if (-not $storyFound) {
    Write-Host "❌ Story not found: $StoryID" -ForegroundColor Red
    exit 1
}

if ($currentStatus -ne 'ready-for-dev' -and $currentStatus -ne 'backlog') {
    Write-Host "❌ Story status is '$currentStatus', not ready for assignment" -ForegroundColor Red
    
    if ($currentAssigned -ne 'null' -and $currentAssigned) {
        Write-Host "Already assigned to: $currentAssigned" -ForegroundColor Yellow
    }
    exit 1
}

if ($storyBlocked) {
    Write-Host "⚠️  WARNING: Story is blocked by: $blockedBy" -ForegroundColor Yellow
    $confirm = Read-Host "Continue anyway? (y/N)"
    if ($confirm -ne 'y' -and $confirm -ne 'Y') {
        Write-Host "Assignment cancelled." -ForegroundColor Gray
        exit 0
    }
}

# Update file
$newStatus = if ($StartNow) { 'in-progress' } else { 'assigned' }

# Replace assigned_to
$content = $content -replace "($StoryID\:[\s\S]*?assigned_to:\s*)null", "`${1}$Developer"

# Replace status
$content = $content -replace "($StoryID\:[\s\S]*?status:\s*)$currentStatus", "`${1}$newStatus"

# Write back
$content | Set-Content $sprintFile -NoNewline

# Commit
Write-Host "`n✅ Assigned $StoryID to $Developer" -ForegroundColor Green
Write-Host "Status: $newStatus" -ForegroundColor Cyan

$commitMsg = if ($StartNow) {
    "Assign $StoryID to $Developer and start work"
} else {
    "Assign $StoryID to $Developer"
}

Write-Host "`n📝 Committing changes..." -ForegroundColor Cyan
git add $sprintFile
git commit -m $commitMsg | Out-Null
git push | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Changes pushed successfully!" -ForegroundColor Green
    
    Write-Host "`n📋 Next steps:" -ForegroundColor Magenta
    if (-not $StartNow) {
        Write-Host "  1. Review story context: docs/sprint-artifacts/$StoryID.md" -ForegroundColor White
        Write-Host "  2. When ready to start: .\scripts\assign-story.ps1 $StoryID $Developer -StartNow" -ForegroundColor White
    } else {
        Write-Host "  1. Read story context: docs/sprint-artifacts/$StoryID.md" -ForegroundColor White
        Write-Host "  2. Read story XML (if exists): docs/sprint-artifacts/$StoryID.context.xml" -ForegroundColor White
        Write-Host "  3. Start coding!" -ForegroundColor White
    }
} else {
    Write-Host "⚠️  Push failed! Resolve conflicts manually." -ForegroundColor Yellow
}

Write-Host ""
