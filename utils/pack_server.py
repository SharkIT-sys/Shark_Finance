import os
import zipfile
import shutil

def export_server_kit(output_path):
    """
    Exports the server component of Shark to a zip file.
    """
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    temp_dir = os.path.join(base_dir, "shark_server_kit_temp_export")
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Files to copy
    files = [
        "docker-compose.yml",
        "Dockerfile",
        ".dockerignore",
        "requirements-web.txt",
        "deploy.ps1"
    ]
    
    dirs = [
        "web_app",
        "controllers",
        "database",
        "models",
        "locales",
        "utils"
    ]
    
    try:
        for f in files:
            src = os.path.join(base_dir, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(temp_dir, f))
                
        for d in dirs:
            src = os.path.join(base_dir, d)
            if os.path.exists(src):
                shutil.copytree(src, os.path.join(temp_dir, d), ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        
        # Create ZIP
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
                    
        return True, "Exportado correctamente."
    except Exception as e:
        return False, str(e)
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
