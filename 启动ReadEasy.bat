@echo off
chcp 65001 >nul
title ReadEasy - 瑞典语电子书阅读器
echo 正在启动 ReadEasy 瑞典语阅读器...
start "" "%~dp0dist\ReadEasy\ReadEasy.exe"
exit
