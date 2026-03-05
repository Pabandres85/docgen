param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("up", "down", "logs", "ps", "migrate", "test-api", "smoke", "release")]
    [string]$Action,
    [string]$Version
)

$ErrorActionPreference = "Stop"

function Invoke-Release {
    param([Parameter(Mandatory = $true)][string]$ReleaseVersion)

    if ($ReleaseVersion -notmatch '^\d+\.\d+\.\d+$') {
        throw "Version invalida: $ReleaseVersion (usa formato x.y.z)"
    }

    $date = Get-Date -Format "yyyy-MM-dd"
    $hasTag = $true
    try {
        $lastTag = git describe --tags --abbrev=0
    } catch {
        $hasTag = $false
    }

    if ($hasTag) {
        $commits = git log --pretty=format:"- %h %s" "$lastTag..HEAD"
    } else {
        $commits = git log --pretty=format:"- %h %s"
    }

    if (-not $commits) {
        $commits = "- Sin commits desde el ultimo release."
    }

    $section = @"
## [$ReleaseVersion] - $date

### Commits
$commits

"@

    if (Test-Path "CHANGELOG.md") {
        $content = Get-Content -Raw "CHANGELOG.md"
        if ($content -match "## \[Unreleased\]") {
            $content = $content -replace "## \[Unreleased\]\r?\n", "## [Unreleased]`n`n$section"
        } else {
            $content = "# Changelog`n`n## [Unreleased]`n`n$section$content"
        }
    } else {
        $content = "# Changelog`n`n## [Unreleased]`n`n$section"
    }

    Set-Content -Path "CHANGELOG.md" -Value $content
    Set-Content -Path "VERSION" -Value $ReleaseVersion
    Write-Host "Release preparado: $ReleaseVersion"
}

switch ($Action) {
    "up" {
        docker compose up --build -d
    }
    "down" {
        docker compose down
    }
    "logs" {
        docker compose logs -f
    }
    "ps" {
        docker compose ps
    }
    "migrate" {
        docker compose exec api sh -c "cd /app/apps/api && alembic -c alembic.ini upgrade head"
    }
    "test-api" {
        docker compose run --rm api sh -c "cd /app/apps/api && pip install --no-cache-dir -r requirements-dev.txt && pytest -q"
    }
    "smoke" {
        docker compose exec api sh -c "python -c \"import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health', timeout=5).read().decode())\""
    }
    "release" {
        if (-not $Version) {
            throw "Para release debes enviar -Version x.y.z"
        }
        Invoke-Release -ReleaseVersion $Version
    }
}
