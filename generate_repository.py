import os
import hashlib
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import shutil

def generate_md5(filepath):
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            md5_hash.update(byte_block)
    return md5_hash.hexdigest()

def create_addon_zip(addon_folder, version):
    # Get base name and create zip path
    base_name = os.path.basename(addon_folder)
    if base_name == '.':  # If we're in the root folder
        base_name = 'repository.weebay'  # Use the correct name
    zip_name = f"{base_name}-{version}.zip"
    zip_path = os.path.join('zips', base_name, zip_name)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    
    # Define files to exclude
    exclude = [
        '.git', '.github', '__pycache__', '*.pyc', 
        '*.pyo', '*.pyd', '.gitignore', '.DS_Store',
        'zips', 'docs', '*.zip'
    ]
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(addon_folder):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude]
            
            for file in files:
                # Skip excluded files
                if any(file.endswith(ext) for ext in exclude):
                    continue
                
                file_path = os.path.join(root, file)
                # Skip if file is a zip file in zips directory
                if 'zips' in file_path and file.endswith('.zip'):
                    continue
                    
                arc_path = os.path.relpath(file_path, os.path.dirname(addon_folder))
                try:
                    zip_file.write(file_path, arc_path)
                except Exception as e:
                    print(f"Error adding {file_path}: {str(e)}")
    
    return zip_path

def generate_addons_xml():
    print("Generating addons.xml...")
    addons_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    
    # Add repository addon
    print("Processing repository addon...")
    repo_addon_xml = ET.parse('addon.xml')
    addons_xml += ET.tostring(repo_addon_xml.getroot(), encoding='unicode')
    
    # Add video addon if exists
    video_addon_path = 'plugin.video.Weebay/addon.xml'
    if os.path.exists(video_addon_path):
        print("Processing video addon...")
        addon_xml = ET.parse(video_addon_path)
        addons_xml += ET.tostring(addon_xml.getroot(), encoding='unicode')
    
    addons_xml += '</addons>\n'
    
    # Create zips directory
    print("Creating directories...")
    os.makedirs('zips', exist_ok=True)
    os.makedirs('docs', exist_ok=True)
    
    # Write addons.xml
    print("Writing addons.xml...")
    with open('zips/addons.xml', 'w', encoding='utf-8') as f:
        f.write(addons_xml)
    
    # Generate MD5
    print("Generating MD5...")
    with open('zips/addons.xml.md5', 'w') as f:
        f.write(generate_md5('zips/addons.xml'))

    # Copy to docs folder
    print("Copying files to docs folder...")
    shutil.copy2('zips/addons.xml', 'docs/addons.xml')
    shutil.copy2('zips/addons.xml.md5', 'docs/addons.xml.md5')
    
    # Create repository ZIP
    print("Creating repository ZIP...")
    repo_zip_path = create_addon_zip('.', '1.0.0')
    
    # Copy repository ZIP to docs
    print("Copying repository ZIP to docs...")
    repo_zip_dest = 'docs/repository.weebay'
    os.makedirs(repo_zip_dest, exist_ok=True)
    shutil.copy2(repo_zip_path, os.path.join(repo_zip_dest, os.path.basename(repo_zip_path)))

if __name__ == "__main__":
    try:
        print("Starting repository generation...")
        generate_addons_xml()
        print("Repository files generated successfully!")
    except Exception as e:
        print(f"Error generating repository: {str(e)}")