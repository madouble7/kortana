@echo off
REM LobeChat Docker deployment script for Windows CMD
REM Replace sk-xxxx with your actual OpenAI API key and lobe66 with your desired access code

REM stop & remove any existing instance
docker stop lobe-chat 2>nul
docker rm   lobe-chat 2>nul

REM launch LobeChat mapping host:7777 → container:3210
docker run -d -p 7777:3210 ^
  -e OPENAI_API_KEY=sk-6Lx93NexO3n9d2UBtXNGv24DwD6HRjZFJpAowMrY0oT3BlbkFJbbi7z4jSzsBC18ZQkE2yzNQHumO5riv4hYeToUL34A ^
  -e ACCESS_CODE=1129 ^
  --name lobe-chat ^
  lobehub/lobe-chat

echo LobeChat container started. Access it at http://localhost:7777/
