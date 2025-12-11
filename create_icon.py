"""
Script to combine multiple icon sizes into a single multi-size .ico file.
This creates app_icon.ico that contains 16x16, 32x32, 48x48, and 256x256 versions.
"""

from PIL import Image
import os

def create_multi_size_icon():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(script_dir, 'res')
    
    # Icon files to combine
    icon_files = ['16x.ico', '32x.ico', '48x.ico', '256x.ico']
    sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
    
    images = []
    
    print("Loading icon files...")
    for icon_file in icon_files:
        icon_path = os.path.join(res_dir, icon_file)
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            # Convert to RGBA if not already
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            images.append(img)
            print(f"  Loaded: {icon_file} ({img.size[0]}x{img.size[1]})")
        else:
            print(f"  Warning: {icon_file} not found at {icon_path}")
    
    if not images:
        print("Error: No icon files found!")
        return False
    
    # Output path
    output_path = os.path.join(res_dir, 'app_icon.ico')
    
    # Save as multi-size .ico
    # The first image is the base, append_images adds the rest
    print(f"\nCreating multi-size icon: {output_path}")
    images[0].save(
        output_path,
        format='ICO',
        sizes=sizes[:len(images)],
        append_images=images[1:]
    )
    
    print(f"Successfully created {output_path}")
    print(f"Icon contains {len(images)} sizes: {[f'{s[0]}x{s[1]}' for s in sizes[:len(images)]]}")
    return True

if __name__ == '__main__':
    create_multi_size_icon()