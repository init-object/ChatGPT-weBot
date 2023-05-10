;请先安装微信客户端3.6.0.18版本 下载路径https://github.com/SnapdragonLee/ChatGPT-weBot/releases/download/v0.98-dev/WeChat-3.6.0.18.exe
wxpath := "C:\Program Files (x86)\Tencent\WeChat\WeChat.exe"
project_path := "C:\Users\wan\Desktop\ChatGPT-weBot-master\ChatGPT-weBot-master"
dll_inject_path := project_path . "\auto_start"
Sleep 60000
Run wxpath
Loop {
	WinWait "ahk_class WeChatLoginWndForPC"
	WinActivate
	Click 103, 287
	if WinWait("ahk_class WeChatMainWndForPC", , 10)
		break
}

Sleep 10000


Run dll_inject_path . "\DLLinjector_V1.0.3.exe", dll_inject_path
Loop {
	if WinExist("ahk_class #32770")
		break
	WinWait "ahk_exe DLLinjector_V1.0.3.exe"
	WinActivate
	Sleep 3000
	SendEvent "{Click 155 319}"
	Click 155, 319
	ControlClick "x135 y291", "ahk_exe DLLinjector_V1.0.3.exe",,,, "NA"
	Sleep 100
	if WinExist("ahk_class #32770")
		break
	Sleep 3000
}

/*
Run dll_inject_path . "\funtool_3.6.0.18-1.0.0013.exe"
WinWait "ahk_exe funtool_3.6.0.18-1.0.0013.exe"
WinActivate
Click 186, 61
;ControlClick "start", "【FunTool】"
*/

Sleep 3000
Run project_path . "\start.bat"
