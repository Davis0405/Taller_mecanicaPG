@echo off
REM === Script para enviar recordatorios de citas ===

REM Ir al directorio del proyecto Django (cuidado con espacios en la ruta)
cd /d "C:\Users\feshernandez\OneDrive - FENACOAC, R.L\Escritorio\taller_mecanica\taller_mecanico"

REM Activar entorno virtual (verifica que esta ruta sea correcta)
call "C:\Users\feshernandez\OneDrive - FENACOAC, R.L\Escritorio\taller_mecanica\venv\Scripts\activate"

REM Ejecutar comando de Django
python manage.py enviar_recordatorios

REM Desactivar entorno virtual (opcional)
REM deactivate

REM Pausa para ver resultados si se ejecuta a mano
pause
