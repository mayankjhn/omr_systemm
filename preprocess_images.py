import os
import cv2
from PIL import Image, ImageEnhance

def enhance_image(image_path, output_path, contrast_factor=1.5, sharpness_factor=1.2):
    """
    Enhances the contrast and sharpness of an image.
    """
    try:
        with Image.open(image_path) as img:
            # Enhance Contrast
            enhancer = ImageEnhance.Contrast(img)
            img_contrasted = enhancer.enhance(contrast_factor)
            
            # Enhance Sharpness
            enhancer = ImageEnhance.Sharpness(img_contrasted)
            img_sharp = enhancer.enhance(sharpness_factor)
            
            img_sharp.save(output_path, quality=95)
        return True
    except Exception as e:
        print(f"Error enhancing {image_path}: {e}")
        return False

def main():
    # Define the folders for your hackathon data
    input_folders = ["data/SetA", "data/SetB"]
    output_parent_folder = "data/processed"

    # Create the main output folder if it doesn't exist
    os.makedirs(output_parent_folder, exist_ok=True)
    
    print("Starting image pre-processing...")

    for folder in input_folders:
        output_folder = os.path.join(output_parent_folder, os.path.basename(folder))
        os.makedirs(output_folder, exist_ok=True)
        
        if not os.path.isdir(folder):
            print(f"Warning: Input folder '{folder}' not found. Skipping.")
            continue

        image_files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        print(f"\nProcessing {len(image_files)} images in '{folder}'...")
        
        for filename in image_files:
            input_path = os.path.join(folder, filename)
            output_path = os.path.join(output_folder, filename)
            
            if enhance_image(input_path, output_path):
                print(f"  ✓ Enhanced '{filename}' and saved to '{output_folder}'")

    print("\nPre-processing complete! The enhanced images are in the 'data/processed' directory.")
    print("Now, run the Streamlit app and upload the images from these new folders.")

if __name__ == "__main__":
    main()
