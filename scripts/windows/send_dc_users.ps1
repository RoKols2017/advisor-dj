$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

& "$scriptDir\send_to_advisor_inbox.ps1" `
  -SourceDir "C:\Export\Users" `
  -TargetDir "\\ADVISOR-LINUX\advisor-dc$\incoming" `
  -SourceId "dc" `
  -Pattern "*.csv"
