#!/bin/bash
echo "=============================================="
echo " CREANDO EL EJECUTABLE DE SHARK CONTABILIDAD"
echo "               (LINUX / FEDORA)               "
echo "=============================================="
echo ""
echo "Paso 1: Instalando PyInstaller y dependencias..."
pip install pyinstaller cryptography Pillow
pip install -r requirements.txt

echo ""
echo "Paso 2: Generando icono..."
python3 generar_icono.py

echo ""
echo "Paso 3: Creando el ejecutable independiente..."
# En Linux, PyInstaller usa ':' como separador en --add-data
ADD_DATA="--add-data ui/styles.qss:ui --add-data ui/resources:ui/resources --add-data locales:locales --add-data web_app:web_app --add-data controllers:controllers --add-data database:database --add-data models:models --add-data utils:utils --add-data deploy.ps1:. --add-data Dockerfile:. --add-data docker-compose.yml:. --add-data requirements-web.txt:. --add-data .dockerignore:. --add-data README.md:. --add-data LICENSE:. --add-data PRIVACY.txt:."

if [ -f "icono.ico" ]; then
    pyinstaller --noconsole --onefile --name "Shark Contabilidad" --icon="icono.ico" $ADD_DATA main.py
else
    pyinstaller --noconsole --onefile --name "Shark Contabilidad" $ADD_DATA main.py
fi

echo ""
echo "Paso 4: Creando lanzador de escritorio (.desktop)..."
cat <<EOF > Shark_Contabilidad.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Shark Contabilidad
Comment=Gestor financiero hiper-seguro
Exec=$(pwd)/dist/Shark\ Contabilidad
Icon=$(pwd)/ui/resources/logo.png
Terminal=false
Categories=Finance;Office;
EOF
chmod +x Shark_Contabilidad.desktop

echo ""
echo "=============================================="
echo "PROCESO COMPLETADO"
echo "Puedes encontrar tu ejecutable listo en:"
echo "$(pwd)/dist/Shark Contabilidad"
echo "Puedes mover 'Shark_Contabilidad.desktop' a ~/.local/share/applications/ para tenerlo en tu menú."
echo "=============================================="
