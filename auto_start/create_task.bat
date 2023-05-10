@echo off
rem 请先安装微信客户端3.6.0.18版本 https://github.com/SnapdragonLee/ChatGPT-weBot/releases/download/v0.98-dev/WeChat-3.6.0.18.exe
rem autoHotKey 编排自动化 https://www.autohotkey.com/download/ahk-v2.exe
Ahk2Exe.exe /in "auto_start.ahk" /out "auto_start.exe"
set current_dir=%cd%
schtasks /create /sc ONLOGON  /tn “Webot” /tr current_dir\auto_start.exe /ru SYSTEM /RL HIGHEST