from PIL import Image
import os

# Define the directory containing the images
image_dir = 'raw'  # Current directory
output_image_path = 'merged_image.jpeg'

# List all image files to be merged
image_files = [f for f in sorted(os.listdir(image_dir)) if f.endswith('.jpeg') and f.startswith('page_')]

# Open all images and store them in a list
images = [Image.open(os.path.join(image_dir, img_file)) for img_file in image_files]

# Get the width and height of the images (assuming all images have the same dimensions)
img_width, img_height = images[0].size

# Calculate the total height of the final image
total_height = sum(img.size[1] for img in images)

# Create a new blank image with the total height and the width of the images
merged_image = Image.new('RGB', (img_width, total_height))

# Paste each image into the new image
y_offset = 0
for img in images:
    merged_image.paste(img, (0, y_offset))
    y_offset += img.size[1]

# Save the merged image
merged_image.save(output_image_path)

print(f'Merged image saved as {output_image_path}')

