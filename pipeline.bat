@echo off
setlocal
title Riverside Prospect Pipeline
cd /d "%~dp0"

if "%~1"=="" goto menu
if /i "%~1"=="discover" goto discover
if /i "%~1"=="qualify" goto qualify
if /i "%~1"=="enrich" goto enrich
if /i "%~1"=="score" goto score
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
echo   1. discover   Search Podcast Index + parse RSS
echo   2. qualify    AI classification (person/org, language)
echo   3. enrich     Enrich qualified prospects via Prospeo
echo   4. score      Apply filters + scoring
echo   5. upload     Push to Airtable
echo.
echo   6. all        Run all steps end-to-end
echo   7. status     Show current pipeline state
echo   0. exit
echo.
echo  ================================================
echo.
set /p choice="  Pick a step (0-7): "

if "%choice%"=="1" goto discover
if "%choice%"=="2" goto qualify
if "%choice%"=="3" goto enrich
if "%choice%"=="4" goto score
if "%choice%"=="5" goto upload
if "%choice%"=="6" goto all
if "%choice%"=="7" goto status
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
