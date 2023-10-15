import os
import exifread
import json
from PIL import Image
import rawpy

# Input and output directories
feed_folder = "source"
gallery_folder = "gallery"
thumbnails_folder = "thumbnails"
fetchlist_path = "fetchlist.json"

# Ensure the output directories exist
os.makedirs(gallery_folder, exist_ok=True)
os.makedirs(thumbnails_folder, exist_ok=True)

# Lists to store the image and thumbnail paths
image_data = []

# Define the tags you want to extract (excluding 'Image Model')
desired_tags = [
    'EXIF ExifImageWidth',
    'EXIF FocalLength',
    'EXIF ExposureTime',
    'EXIF FNumber',
    'EXIF ISOSpeedRatings',
    'EXIF LensModel',
    'Image Make',
]

# Define the new dimensions for the original image
new_width = 3000
new_height = 2000

# Iterate through the files in the feed folder
for filename in os.listdir(feed_folder):
    if filename.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.ARW')):
        try:
            # Check if the file is an ARW file
            is_arw = filename.endswith('.ARW')

            if is_arw:
                # Open and process the ARW file using rawpy
                with rawpy.imread(os.path.join(feed_folder, filename)) as raw:
                    # Extract the RGB image
                    rgb = raw.postprocess()

                image = Image.fromarray(rgb)
            else:
                # Open other image formats using PIL
                image = Image.open(os.path.join(feed_folder, filename))

            # Save the original image as webp in the gallery folder with new dimensions
            gallery_filename = os.path.splitext(filename)[0] + '.webp'
            image = image.resize((new_width, new_height), Image.BILINEAR)
            image.save(os.path.join(gallery_folder, gallery_filename), 'webp')

            # Calculate the new size (420x280) for the thumbnail
            thumbnail_width = 420
            thumbnail_height = 280

            # Resize the image using the BILINEAR filter
            resized_image = image.resize((thumbnail_width, thumbnail_height), Image.BILINEAR)

            # Create the thumbnail file name
            thumbnail_filename = os.path.splitext(filename)[0] + '.webp'

            # Save the resized image as webp in the thumbnails folder
            resized_image.save(os.path.join(thumbnails_folder, thumbnail_filename), 'webp')

            # Extract metadata
            arw_file_path = os.path.join(feed_folder, filename)
            with open(arw_file_path, 'rb') as arw_file:
                tags = exifread.process_file(arw_file)

                # Create a dictionary to store metadata for this file
                metadata = {}
                for tag in desired_tags:
                    if tag in tags:
                        if tag == 'EXIF FNumber':
                            fnumber_fraction = tags[tag].values[0]
                            fnumber_decimal = fnumber_fraction.numerator / fnumber_fraction.denominator
                            metadata["fStop"] = f'f/{fnumber_decimal:.1f}'
                        elif tag == 'EXIF ExifImageWidth':
                            # Combine ExifImageWidth with ExifImageLength to form 'Dimensions'
                            if 'EXIF ExifImageLength' in tags:
                                width = tags['EXIF ExifImageWidth'].values[0]
                                length = tags['EXIF ExifImageLength'].values[0]
                                metadata["Dimensions"] = f"{width}x{length}"
                        elif tag == 'EXIF FocalLength':
                            focal_length = str(tags[tag])
                            metadata["FocalLength"] = f'{focal_length}mm'
                        elif tag == 'EXIF ExposureTime':
                            exposure_time = str(tags[tag])
                            metadata["Exposure"] = f'{exposure_time}s'
                        elif tag == 'EXIF ISOSpeedRatings':
                            iso_value = str(tags[tag])
                            metadata["ISO"] = f'ISO{iso_value}'
                        elif tag == 'EXIF LensModel':
                            lens_model = str(tags[tag])
                            metadata["Lens"] = lens_model
                        elif tag == 'Image Make':
                            make_model = f"{tags['Image Make']} {tags['Image Model']}"
                            metadata["Model"] = make_model
                        else:
                            metadata[tag] = str(tags[tag])

                # Append the gallery and thumbnail paths to the respective lists
                image_data.append({
                    "src": f"./{gallery_folder}/{gallery_filename}",
                    "thumbnailSrc": f"./{thumbnails_folder}/{thumbnail_filename}",
                    "info": metadata
                })

                print(f"Resized and saved: {thumbnail_filename}")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

# Write the updated data back to fetchlist.json
with open(fetchlist_path, 'w') as fetchlist_file:
    json.dump({"images": image_data}, fetchlist_file, indent=4)

print("All images saved as webp in gallery and as thumbnails in thumbnails folder.")
print("Metadata extracted and saved to fetchlist.json.")
