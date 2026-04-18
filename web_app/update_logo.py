import os
from PIL import Image

src = r"d:\Proyectos\App_presupuesto\ui\resources\logo.png"
dest192 = r"d:\Proyectos\App_presupuesto\web_app\static\icons\icon-192.png"
dest512 = r"d:\Proyectos\App_presupuesto\web_app\static\icons\icon-512.png"

if os.path.exists(src):
    img = Image.open(src).convert("RGBA")
    img192 = img.resize((192, 192), Image.Resampling.LANCZOS)
    img192.save(dest192, format="PNG")
    img512 = img.resize((512, 512), Image.Resampling.LANCZOS)
    img512.save(dest512, format="PNG")
    print("Logos actualizados correctamente desde el original.")
else:
    print("Logo original no encontrado en " + src)
