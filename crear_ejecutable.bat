@echo off
echo ==============================================
echo  CREANDO EL EJECUTABLE DE SHARK CONTABILIDAD
echo ==============================================
echo.
echo Paso 1: Instalando PyInstaller y librerias...
pip install pyinstaller cryptography pypiwin32 winshell Pillow

echo.
echo Paso 2: Generando icono a partir de tu foto...
python generar_icono.py

echo.
echo Paso 3: Creando el ejecutable independiente...
set ADD_DATA=--add-data "ui/styles.qss;ui" --add-data "ui/resources;ui/resources" --add-data "locales;locales" --add-data "web_app;web_app" --add-data "controllers;controllers" --add-data "database;database" --add-data "models;models" --add-data "utils;utils" --add-data "deploy.ps1;." --add-data "Dockerfile;." --add-data "docker-compose.yml;." --add-data "requirements-web.txt;." --add-data ".dockerignore;." --add-data "README.md;." --add-data "LICENSE;." --add-data "PRIVACY.txt;."

if exist icono.ico (
    pyinstaller --noconsole --onefile --name "Shark Contabilidad" --icon="icono.ico" %ADD_DATA% main.py
) else (
    pyinstaller --noconsole --onefile --name "Shark Contabilidad" %ADD_DATA% main.py
)

echo.
echo ==============================================
echo PROCESO COMPLETADO
echo Puedes encontrar tu ejecutable listo para compartir en:
echo D:\Proyectos\App_presupuesto\dist\Shark Contabilidad.exe
echo ==============================================
