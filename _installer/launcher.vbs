Option Explicit
Dim fso, appDir, pythonExe, appPy, ws

Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)

pythonExe = appDir & "\python\python.exe"
appPy     = appDir & "\app.py"

Set ws = CreateObject("WScript.Shell")
ws.CurrentDirectory = appDir

' Start Streamlit server (hidden window - no CMD popup)
ws.Run """" & pythonExe & """ -m streamlit run """ & appPy & _
    """ --server.headless true --server.port 8501" & _
    " --browser.gatherUsageStats false", 0, False

' Wait for server to boot up
WScript.Sleep 5000

' Open browser
ws.Run "cmd /c start http://localhost:8501", 0, False
