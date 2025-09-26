@echo off
cd %~dp0\..
git checkout -b feat/public-apis-pack
git add -A
git commit -m "feat(public-apis): adapters + proxy + Weather/Holidays/HN/BookFinder cards"
echo Created branch feat/public-apis-pack and committed changes.
