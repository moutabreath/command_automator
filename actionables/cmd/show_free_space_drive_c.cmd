@echo off

REM Get the total free space on drive C:
set total_free_space=0
for /f "delims=" %%i in ('wmic logicaldisk get freespace where caption="C:"') do set total_free_space=%%i

REM Convert the free space to GB
set free_space_in_gb=%total_free_space% / 1073741824

REM Display the free space
echo The free space on drive C: is %free_space_in_gb% GB.

