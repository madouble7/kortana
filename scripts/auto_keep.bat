@echo off
:loop
git add -A
git commit -m "auto-keep: save all agent progress"
timeout /t 60
goto loop
