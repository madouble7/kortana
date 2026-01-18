import os
import io

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not found. Please run: pip install Pillow")
    exit(1)

def create_icon(size, filename, color="#00d4ff"):
    """Create a simple Kor'tana icon."""
    img = Image.new('RGB', (size, size), color='#0f0f1e')
    draw = ImageDraw.Draw(img)
    
    # Draw a stylized 'K' or circle
    padding = size // 5
    draw.ellipse([padding, padding, size - padding, size - padding], outline=color, width=size // 20)
    
    # Draw a lightning bolt (Zap)
    center = size // 2
    offset = size // 10
    points = [
        (center, padding + offset),
        (center - offset, center),
        (center + offset, center),
        (center, size - padding - offset)
    ]
    # Simple line zap
    draw.line([(center, padding), (center - offset, center), (center + offset, center), (center, size-padding)], fill=color, width=size//30)

    # Save
    output_path = os.path.join("frontend", "public", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Created icon: {output_path}")

if __name__ == "__main__":
    print("Generating Kor'tana PWA icons...")
    create_icon(192, "pwa-192x192.png")
    create_icon(512, "pwa-512x512.png")
    create_icon(192, "icon-192.png")
    print("Done. Icons are now in frontend/public/")
