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