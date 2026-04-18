import os
from PIL import Image

def create_icon(size, output_filename, source_logo):
    # Open source logo
    if not os.path.exists(source_logo):
        print(f"Error: {source_logo} not found")
        return

    img = Image.open(source_logo)
    
    # Square the image if it's not square (optional, but good for icons)
    # For now, we assume logo is mostly square or okay to resize
    
    # Resize with high quality
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Save
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    img.save(output_filename, "PNG")
    print(f"Created {output_filename} from {source_logo}")

base_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(base_dir, 'static', 'logo.png')
icons_dir = os.path.join(base_dir, 'static', 'icons')

create_icon(192, os.path.join(icons_dir, 'icon-192.png'), logo_path)
create_icon(512, os.path.join(icons_dir, 'icon-512.png'), logo_path)
