@echo off
echo Checking Kor'tana's learning database...
echo.

rem Query total memories
echo Querying total memories:
sqlite3.exe c:\project-kortana\kortana.db "SELECT COUNT(*) as total_memories FROM core_memories;" > temp_results.txt 2>&1
type temp_results.txt
echo.

rem Query core beliefs
echo Querying core beliefs:
sqlite3.exe c:\project-kortana\kortana.db "SELECT COUNT(*) as core_beliefs FROM core_memories WHERE memory_type = 'CORE_BELIEF';" >> temp_results.txt 2>&1
type temp_results.txt | find "core_beliefs"
echo.

rem Query learning loop activity
echo Querying learning loop activity:
sqlite3.exe c:\project-kortana\kortana.db "SELECT COUNT(*) as learning_memories FROM core_memories WHERE memory_metadata LIKE '%%performance_analysis_task%%';" >> temp_results.txt 2>&1
type temp_results.txt | find "learning_memories"
echo.

rem Query recent beliefs
echo Querying recent beliefs:
sqlite3.exe c:\project-kortana\kortana.db "SELECT title, created_at FROM core_memories WHERE memory_type = 'CORE_BELIEF' ORDER BY created_at DESC LIMIT 3;" >> temp_results.txt 2>&1
echo Recent beliefs found in temp_results.txt

rem Query total goals
echo Querying total goals:
sqlite3.exe c:\project-kortana\kortana.db "SELECT COUNT(*) as total_goals FROM goals;" >> temp_results.txt 2>&1
type temp_results.txt | find "total_goals"

echo.
echo Full results saved to temp_results.txt
pause
