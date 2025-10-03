from PIL import Image

def compress_image(file, output_path, quality=40):
    img = Image.open(file)
    img.save(output_path, "JPEG", optimize=True, quality=quality)
