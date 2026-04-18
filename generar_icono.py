from PIL import Image
import os

try:
    path_png = os.path.join('ui', 'resources', 'logo.png')
    if os.path.exists(path_png):
        img = Image.open(path_png)
        # Ensure it has an alpha channel or converts cleanly
        img = img.convert('RGBA')
        img.save('icono.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32)])
        print("Icono generado con éxito (icono.ico).")
    else:
        print("No se encontró el logo.png en ui/resources/.")
except Exception as e:
    print(f"Error generando icono: {e}")
