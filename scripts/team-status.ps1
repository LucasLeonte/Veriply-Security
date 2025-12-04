# Team Status Dashboard
# Quick view of who's working on what

param(
    [string]$Developer = $null
)

$sprintFile = "$PSScriptRoot\..\docs\sprint-artifacts\sprint-status.yaml"

if (-not (Test-Path $sprintFile)) {
    Write-Host "[X] Sprint status file not found!" -ForegroundColor Red
    exit 1
}

$content = Get-Content $sprintFile -Raw
$lines = $content -split "`n"

Write-Host "`n>> VERIPLY TEAM STATUS - $(Get-Date -Format 'yyyy-MM-dd HH:mm')" -ForegroundColor Cyan
Write-Host "-----------------------------------------------------------`n" -ForegroundColor Cyan

# Parse team info
$inTeamSection = $false
$developers = @()

# Valid developer names
$validDevNames = @('Dario', 'Lucas', 'Kainy', 'Soulaymane')

foreach ($line in $lines) {
    if ($line -match '^\s*-\s*name:\s*(.+)$') {
        $devName = $Matches[1].Trim()
        $currentDev = @{Name = $devName; MaxWIP = 2; CurrentWIP = 0; Stories = @()}
        $developers += $currentDev
    }
}

# Parse work assignments (use indexed loop so look-ahead finds the correct assigned_to for each story)
$currentStory = $null
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line -match '^\s+(\d+-\d+-.+?):\s*$') {
        $currentStory = $Matches[1].Trim()
        continue
    }

    if ($currentStory -and $line -match '^\s+status:\s*(.+)$') {
        $status = $Matches[1].Trim()
        $storyData = @{ID = $currentStory; Status = $status; AssignedTo = $null}

        # Look ahead for assigned_to within the next few lines
        for ($j = $i + 1; ($j -lt $lines.Count) -and ($j -le $i + 3); $j++) {
            $nextLine = $lines[$j]
            if ($nextLine -match '^\s+assigned_to:\s*(.+)$') {
                $assignedTo = $Matches[1].Trim()
                if ($assignedTo -ne 'null') {
                    $storyData.AssignedTo = $assignedTo

                    # Add to developer's stories
                    $dev = $developers | Where-Object { $_.Name -eq $assignedTo }
                    if ($dev) {
                        $dev.Stories += $storyData
                        if ($status -eq 'in-progress' -or $status -eq 'assigned') {
                            $dev.CurrentWIP++
                        }
                    }
                }
                break
            }
        }

        $currentStory = $null
    }
}

# Display team view
if ($Developer) {
    $dev = $developers | Where-Object { $_.Name -eq $Developer }
    if (-not $dev) {
        Write-Host "[X] Developer '$Developer' not found!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ">> $($dev.Name) - WIP: $($dev.CurrentWIP)/$($dev.MaxWIP)" -ForegroundColor Yellow
    Write-Host "-----------------------------------------------------------`n" -ForegroundColor Gray
    
    if ($dev.Stories.Count -eq 0) {
        Write-Host "  No assigned stories" -ForegroundColor Gray
    } else {
        foreach ($story in $dev.Stories) {
            $statusColor = switch ($story.Status) {
                'in-progress' { 'Green' }
                'assigned' { 'Yellow' }
                'review' { 'Cyan' }
                'done' { 'DarkGray' }
                default { 'White' }
            }
            Write-Host "  [$($story.Status.ToUpper())]" -ForegroundColor $statusColor -NoNewline
            Write-Host " $($story.ID)" -ForegroundColor White
        }
    }
} else {
    # Show all developers
    foreach ($dev in $developers) {
        $wipColor = if ($dev.CurrentWIP -ge $dev.MaxWIP) { 'Red' } elseif ($dev.CurrentWIP -gt 0) { 'Yellow' } else { 'Green' }
        
        Write-Host ">> $($dev.Name)" -ForegroundColor White -NoNewline
        Write-Host " - WIP: " -NoNewline
        Write-Host "$($dev.CurrentWIP)/$($dev.MaxWIP)" -ForegroundColor $wipColor
        Write-Host "-----------------------------------------------------------" -ForegroundColor Gray
        
        if ($dev.Stories.Count -eq 0) {
            Write-Host "  [OK] Available for work" -ForegroundColor Green
        } else {
            foreach ($story in $dev.Stories) {
                $statusIcon = switch ($story.Status) {
                    'in-progress' { '[WIP]' }
                    'assigned' { '[ASN]' }
                    'review' { '[REV]' }
                    'done' { '[OK]' }
                    default { '[?]' }
                }
                $statusColor = switch ($story.Status) {
                    'in-progress' { 'Green' }
                    'assigned' { 'Yellow' }
                    'review' { 'Cyan' }
                    'done' { 'DarkGray' }
                    default { 'White' }
                }
                Write-Host "  $statusIcon " -NoNewline
                Write-Host "$($story.ID)" -ForegroundColor $statusColor
            }
        }
        Write-Host ""
    }
}

# Show available work
Write-Host "`n>> AVAILABLE FOR ASSIGNMENT" -ForegroundColor Magenta
Write-Host "-----------------------------------------------------------`n" -ForegroundColor Magenta

$availableStories = @()
$currentStory = $null
$currentStatus = $null
$currentAssigned = $null

foreach ($line in $lines) {
    if ($line -match '^\s+(\d+-\d+-.+?):\s*$') {
        if ($currentStory -and $currentStatus -eq 'ready-for-dev' -and $currentAssigned -eq 'null') {
            $availableStories += $currentStory
        }
        $currentStory = $Matches[1].Trim()
        $currentStatus = $null
        $currentAssigned = $null
    }
    
    if ($line -match '^\s+status:\s*(.+)$') {
        $currentStatus = $Matches[1].Trim()
    }
    
    if ($line -match '^\s+assigned_to:\s*(.+)$') {
        $currentAssigned = $Matches[1].Trim()
    }
}

# Check last story
if ($currentStory -and $currentStatus -eq 'ready-for-dev' -and $currentAssigned -eq 'null') {
    $availableStories += $currentStory
}

if ($availableStories.Count -eq 0) {
    Write-Host "  No stories ready for assignment" -ForegroundColor Gray
} else {
    foreach ($story in $availableStories) {
        Write-Host "  [*] $story" -ForegroundColor Cyan
    }
}

Write-Host "`n-----------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Usage: .\team-status.ps1 [-Developer Dev1]`n" -ForegroundColor DarkGray
