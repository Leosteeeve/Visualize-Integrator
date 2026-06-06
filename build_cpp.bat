@echo off
setlocal

if not exist cpp\integrator.cpp (
  echo cpp\integrator.cpp was not found.
  exit /b 1
)

where g++ >nul 2>nul
if errorlevel 1 (
  echo g++ was not found on PATH.
  echo The Python server can also try known MinGW paths automatically.
  exit /b 1
)

g++ -O3 -std=c++17 cpp\integrator.cpp -o cpp\integrator.exe
if errorlevel 1 exit /b 1

echo Built cpp\integrator.exe
