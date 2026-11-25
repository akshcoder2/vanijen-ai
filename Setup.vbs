Option Explicit
Dim shell, fs, folder, launch, code, shortcut, icon, pyw
Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
folder = fs.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = folder
MsgBox "Vanijen AI will install the Python packages it needs, then create a desktop shortcut. Python with the Windows launcher must already be installed.", 64, "Vanijen AI Setup"
code = shell.Run("py -m pip install -r " & Chr(34) & fs.BuildPath(folder, "requirements.txt") & Chr(34), 0, True)
If code <> 0 Then
  MsgBox "Installation failed. Check Python and internet access, or use setup.bat to see the error.", 16, "Vanijen AI Setup"
  WScript.Quit 1
End If
Set launch = shell.Exec("where.exe pyw.exe")
pyw = Trim(Split(launch.StdOut.ReadAll, vbCrLf)(0))
If pyw = "" Then
  MsgBox "Python's windowed launcher (pyw.exe) was not found.", 16, "Vanijen AI Setup"
  WScript.Quit 1
End If
Set shortcut = shell.CreateShortcut(fs.BuildPath(shell.SpecialFolders("Desktop"), "Vanijen AI.lnk"))
shortcut.TargetPath = pyw
shortcut.Arguments = Chr(34) & fs.BuildPath(folder, "jarvis.py") & Chr(34)
shortcut.WorkingDirectory = folder
icon = fs.BuildPath(folder, "assets\vanijen-icon.ico")
If fs.FileExists(icon) Then shortcut.IconLocation = icon & ",0"
shortcut.Save
MsgBox "Done. Open Vanijen AI from your Desktop.", 64, "Vanijen AI Setup"
