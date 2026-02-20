$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$scriptDir\send_to_advisor_inbox.ps1" `
  -SourceDir "C:\Export\PrintEvents" `
  -TargetDir "\\ADVISOR-LINUX\advisor-print1$\incoming" `
  -SourceId "print1" `
  -Pattern "*.json"
