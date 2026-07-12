from PIL import Image, ImageDraw, ImageFont

# Load the shape image
try:
    shape_img = Image.open('logo_shape.png').convert('RGBA')
except Exception as e:
    print(f"Error loading logo_shape.png: {e}")
    exit(1)

# Resize shape to fit nicely
target_height = 80
aspect_ratio = shape_img.width / shape_img.height
target_width = int(target_height * aspect_ratio)
shape_img = shape_img.resize((target_width, target_height), Image.Resampling.LANCZOS)

# Create a new blank image for the full logo
# We will add text "abiz" next to it.
# We'll use a large enough width to fit the text.
full_width = target_width + 150
full_img = Image.new('RGBA', (full_width, target_height), (255, 255, 255, 0))

# Paste the shape onto the new image
full_img.paste(shape_img, (0, 0), shape_img)

# Add the text "abiz"
draw = ImageDraw.Draw(full_img)
try:
    # Try to load a nice bold font if available, otherwise use default
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
except:
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 40)
    except:
        font = ImageFont.load_default()

# The user wants "abiz" text next to it. Let's make it a nice dark color.
text = "abiz"
# Need to use getbbox or getmask for newer Pillow versions
try:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
except AttributeError:
    text_width, text_height = draw.textsize(text, font=font)

# Position text vertically centered relative to the shape
text_x = target_width + 10
text_y = (target_height - text_height) / 2

# Actually, the user says "abiz" next to it. We will use black color.
draw.text((text_x, text_y), text, fill=(0, 0, 0, 255), font=font)

# Save the final logo
full_img.save('new_logo.png')
print("Saved new_logo.png")

# Also, convert it to base64 so we can embed it directly in the HTML
import base64
with open("new_logo.png", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    with open("logo_base64.txt", "w") as f:
        f.write(encoded_string)
