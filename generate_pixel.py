from PIL import Image

img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))  # transparent pixel
img.save("pixel.png")
print("✅ pixel.png created")
