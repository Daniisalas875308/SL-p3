echo Perparando la configuracion para un entorno rápido
echo Copia el contenido del fichero COPIAR.txt
timeout /nobreak /t 2 >nul
start notepad.exe ".\COPIAR.txt"
pause
echo Abriendo fichero donde hay que copiar el contenido de COPIAR.txt... (Acuerdate de guardar el fichero)
timeout /nobreak /t 2 >nul
cd Database-MSDOS\DOSBox-0.74
DOSBox.exe -editconf notepad.exe -editconf %SystemRoot%\system32\notepad.exe -editconf %WINDIR%\notepad.exe
pause
taskkill /IM notepad.exe /F

:: Ejecutar la aplicación Flask y esperar a que termine 
cd ..\..
echo Lanzando Busca tu videojuego ...
@echo off 
:: Ejecuta Python y espera a que termine
start /wait python ".\app.py"

:: Captura el código de salida
set EXITCODE=%ERRORLEVEL%

:: Comprueba si Python terminó con error
if %EXITCODE% neq 0 (
    echo [ERROR] app.py terminó con código %EXITCODE%
    pause
) else (
    echo [INFO] app.py terminó correctamente
)

:: Cierra DOSBox si sigue abierto
taskkill /IM DOSBox.exe /F
   
endlocal   