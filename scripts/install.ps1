param(
    [string]$TargetSkillsDir = "$env:USERPROFILE\.gemini\config\skills",
    [switch]$SkipMcpHint
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SourceSkills = Join-Path $RepoRoot "skills"

if (-not (Test-Path $TargetSkillsDir)) {
    New-Item -ItemType Directory -Path $TargetSkillsDir -Force | Out-Null
}

Get-ChildItem $SourceSkills -Directory | ForEach-Object {
    $dest = Join-Path $TargetSkillsDir $_.Name
    if (Test-Path $dest) {
        Remove-Item $dest -Recurse -Force
    }
    Copy-Item $_.FullName -Destination $dest -Recurse -Force
    Write-Host "Installed skill: $($_.Name) -> $dest"
}

if (-not $SkipMcpHint) {
    $McpSnippet = @{
        "canva-skills-mcp" = @{
            "command" = "python"
            "args"    = @("-m", "mcp_server")
            "cwd"     = $RepoRoot
        }
    } | ConvertTo-Json -Depth 4

    Write-Host "`nAdd this entry under `"mcpServers`" in $env:USERPROFILE\.gemini\config\mcp_config.json:"
    Write-Host $McpSnippet
}
