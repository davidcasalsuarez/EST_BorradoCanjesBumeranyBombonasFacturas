@echo off
setlocal

if not exist "Y:\WASOIL5\" (
    echo Conectando Y: con \\192.168.10.4\c...
    net use Y: "\\192.168.10.4\c" /persistent:no
)

if not exist "Y:\WASOIL5\" (
    echo ERROR: No se pudo acceder a Y:\WASOIL5\. El proceso no se ejecutara.
    pause
    endlocal
    exit /b 2
)

"\\Vmapp\c\Program Files (x86)\Python\python.exe" "C:\PROGRAMAS GALURESA\Procesos Batch\ESTACIONES\EST_BorradoCanjesBumeran\batchCanjesBumeran.py"
set "codigo_salida=%errorlevel%"
pause
endlocal & exit /b %codigo_salida%
