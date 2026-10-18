Set WshShell = CreateObject("WScript.Shell")
strCurrentPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run """" & strCurrentPath & "\dist\ReadEasy\ReadEasy.exe""", 0, False
