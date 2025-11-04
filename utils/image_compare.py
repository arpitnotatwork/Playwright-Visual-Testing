from PIL import Image, ImageChops
import os

def compare_images(old_path, new_path, diff_path):
    old = Image.open(old_path)
    new = Image.open(new_path)
    
    diff = ImageChops.difference(old, new)
    
    if diff.getbbox():
        diff.save(diff_path)
        return False  # images are different
    return True  # images are same

def batch_compare(old_dir, new_dir, diff_dir):
    os.makedirs(diff_dir, exist_ok=True)
    results = {}
    
    for filename in os.listdir(old_dir):
        old_path = os.path.join(old_dir, filename)
        new_path = os.path.join(new_dir, filename)
        diff_path = os.path.join(diff_dir, filename)
        
        if os.path.exists(new_path):
            result = compare_images(old_path, new_path, diff_path)
            results[filename] = result
    
    return results
