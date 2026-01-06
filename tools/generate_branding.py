from PIL import Image, ImageDraw, ImageFont

ORANGE = (255, 102, 0)
WHITE = (255, 255, 255)


def make_image(size, text, filename):
    img = Image.new("RGB", size, ORANGE)
    draw = ImageDraw.Draw(img)
    # Draw white rounded rectangle border
    pad = int(min(size) * 0.06)
    draw.rounded_rectangle([pad, pad, size[0]-pad, size[1]-pad], radius=int(min(size)*0.12), outline=WHITE, width=int(min(size)*0.03))
    # Write text centered
    font = ImageFont.load_default()
    # Try to scale font by drawing multiple times to thicken
    w, h = draw.textbbox((0,0), text, font=font)[2:4]
    # Simple scale factor based on image size
    scale = int(min(size) / max(w, h) * 0.5)
    try:
        # Try a larger truetype font if available
        font = ImageFont.truetype("arial.ttf", int(scale*12))
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0,0), text, font=font)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
    x = (size[0]-tw)//2
    y = (size[1]-th)//2
    draw.text((x, y), text, font=font, fill=WHITE)
    img.save(filename, format="PNG")

if __name__ == "__main__":
    make_image((256, 256), "JBL", "icon.png")
    make_image((512, 512), "JBL 4305P", "logo.png")
    print("Generated icon.png and logo.png")
