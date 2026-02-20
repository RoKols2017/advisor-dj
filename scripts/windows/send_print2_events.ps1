$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$scriptDir\send_to_advisor_inbox.ps1" `
  -SourceDir "C:\Export\PrintEvents" `
  -TargetDir "\\ADVISOR-LINUX\advisor-print2$\incoming" `
  -SourceId "print2" `
  -Pattern "*.json"
