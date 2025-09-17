from PIL import Image

# File paths
file1_path = "static/images/bong_empty.png"
file2_path = "static/images/bong_filled.png"

# Open images
img1 = Image.open(file1_path)
img2 = Image.open(file2_path)


# Crop evenly from top and bottom (keeping central beer bong part)
def crop_even(img, crop_percent=0.1):
    w, h = img.size
    crop_h = int(h * crop_percent)
    return img.crop((0, crop_h, w, h - crop_h))

# Crop 5% from the left of img1
def crop_left(img, crop_percent=0.05):
    w, h = img.size
    crop_w = int(w * crop_percent)
    return img.crop((crop_w, 0, w, h))

img1_cropped = crop_left(img1, crop_percent=0.045)
img1_cropped = img1_cropped.resize((img2.width, img2.height), Image.LANCZOS)
# Save results
output1_path = "static/images/bong_filled_test2.png"

img1_cropped.save(output1_path)
