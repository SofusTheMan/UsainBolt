from PIL import Image

# File paths
file1_path = "static/images/bong_empty.png"
file2_path = "static/images/bong_filled.png"

# Open images
img1 = Image.open(file1_path)
img2 = Image.open(file2_path)


# Calculate crop box to remove 35% from top and bottom, and 5% from left and right
width, height = img1.size
crop_left = int(width * 0.03)
crop_right = int(width * 0.97)
crop_top = int(height * 0.40)
crop_bottom = int(height * 0.55)
crop_box = (crop_left, crop_top, crop_right, crop_bottom)

img1_cropped = img1.crop(crop_box)
img2_cropped = img2.crop(crop_box)
# Save results
output1_path = "static/images/bong_empty_test.png"
output2_path = "static/images/bong_filled_test.png"


img1_cropped.save(output1_path)
img2_cropped.save(output2_path)
