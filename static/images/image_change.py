from PIL import Image

# File paths
file1_path = "/mnt/data/viking_lbong_100_cm_.jpg"
file2_path = "/mnt/data/ChatGPT Image Sep 15, 2025, 03_00_15 PM.png"

# Open images
img1 = Image.open(file1_path)
img2 = Image.open(file2_path)

# Rotate both images 90 degrees clockwise
img1_rot = img1.rotate(-90, expand=True)
img2_rot = img2.rotate(-90, expand=True)

# Resize both images to the same size (based on the smaller one for consistency)
common_size = (min(img1_rot.width, img2_rot.width), min(img1_rot.height, img2_rot.height))
img1_resized = img1_rot.resize(common_size, Image.LANCZOS)
img2_resized = img2_rot.resize(common_size, Image.LANCZOS)

# Crop evenly from top and bottom (keeping central beer bong part)
def crop_even(img, crop_percent=0.1):
    w, h = img.size
    crop_h = int(h * crop_percent)
    return img.crop((0, crop_h, w, h - crop_h))

img1_cropped = crop_even(img1_resized, crop_percent=0.1)
img2_cropped = crop_even(img2_resized, crop_percent=0.1)

# Save results
output1_path = "/mnt/data/beer_bong_yellow_progress.png"
output2_path = "/mnt/data/beer_bong_empty_progress.png"

img1_cropped.save(output1_path)
img2_cropped.save(output2_path)

output1_path, output2_path
