from PIL import Image

img = Image.open('/tmp/file_attachments/WhatsApp Image 2026-07-13 at 12.40.07 AM.jpeg')
logo = img.crop((160, 200, 1920, 520))
logo.save('logo.jpg')
