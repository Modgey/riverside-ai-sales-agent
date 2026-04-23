@echo off
setlocal
title Riverside Prospect Pipeline
cd /d "%~dp0"

if "%~1"=="" goto menu
if /i "%~1"=="discover" goto discover
if /i "%~1"=="qualify" goto qualify
if /i "%~1"=="enrich" goto enrich
if /i "%~1"=="score" goto score
if /i "%~1"=="deep_enrich" goto deep_enrich
if /i "%~1"=="phone_enrich" goto phone_enrich
if /i "%~1"=="call_context" goto call_context
if /i "%~1"=="upload" goto upload
if /i "%~1"=="all" goto all
if /i "%~1"=="status" goto status
goto menu

:menu
echo.
echo  ================================================
echo   Riverside Prospect Pipeline
echo  ================================================
echo.
echo   1. discover        Find podcasts via Podcast Index + parse RSS
echo   2. qualify          AI cleans names, detects language, filters orgs
echo   3. enrich           Look up emails + company data
echo   4. score            Rank prospects by fit + activity
echo   5. deep_enrich      Pull episode details, company pages, LLM summaries
echo   6. phone_enrich     Look up mobile numbers for top prospects
echo   7. call_context     Generate personalized call briefings (AI)
echo   8. upload           Push final list to Airtable
echo.
echo   9. all              Run full pipeline (1-8) end-to-end
echo   10. status          Show what's been run so far
echo   0. exit
echo.
echo  ================================================
echo.
set /p choice="  Pick a step (0-9): "

if "%choice%"=="1" goto discover
if "%choice%"=="2" goto qualify
if "%choice%"=="3" goto enrich
if "%choice%"=="4" goto score
if "%choice%"=="5" goto deep_enrich
if "%choice%"=="6" goto phone_enrich
if "%choice%"=="7" goto call_context
if "%choice%"=="8" goto upload
if "%choice%"=="9" goto all
if "%choice%"=="10" goto status
if "%choice%"=="0" goto end
echo  Invalid choice.
goto menu

:discover
echo.
py -X utf8 src/run_pipeline.py discover
echo.
pause
goto menu

:qualify
echo.
py -X utf8 src/run_pipeline.py qualify
echo.
pause
goto menu

:enrich
echo.
py -X utf8 src/run_pipeline.py enrich
echo.
pause
goto menu

:score
echo.
py -X utf8 src/run_pipeline.py score
echo.
pause
goto menu

:deep_enrich
echo.
py -X utf8 src/run_pipeline.py deep_enrich
echo.
pause
goto menu

:phone_enrich
echo.
py -X utf8 src/run_pipeline.py phone_enrich
echo.
pause
goto menu

:call_context
echo.
py -X utf8 src/run_pipeline.py generate_context
echo.
pause
goto menu

:upload
echo.
py -X utf8 src/run_pipeline.py upload
echo.
pause
goto menu

:all
echo.
py -X utf8 src/run_pipeline.py all
echo.
pause
goto menu

:status
echo.
py -X utf8 src/run_pipeline.py status
echo.
pause
goto menu

:end
echo.
echo  Done.
endlocal
