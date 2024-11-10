import base64
import io
import json
import string
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from anthropic import Anthropic

# Load environment variables
load_dotenv()
GRID_SIZE = 75
def add_chess_grid_to_image(image, grid_size=GRID_SIZE):
    width, height = image.size
    cols = width // grid_size
    rows = height // grid_size
    
    draw = ImageDraw.Draw(image)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()

    # Draw vertical lines and label them
    for i in range(cols + 1):
        x = i * grid_size
        draw.line([(x, 0), (x, height)], fill='red', width=2)
        if i < cols:
            label = string.ascii_uppercase[i]
            draw.text((x + 15, 5), label, fill='red', font=font)

    # Draw horizontal lines and label them
    for i in range(rows + 1):
        y = i * grid_size
        draw.line([(0, y), (width, y)], fill='red', width=2)
        if i < rows:
            label = str(i + 1)
            draw.text((5, y + 15), label, fill='red', font=font)

    return cols, rows

def chess_to_pixel(chess_coord, grid_size=GRID_SIZE):
    col = string.ascii_uppercase.index(chess_coord[0])
    row = int(chess_coord[1:]) - 1
    return col * grid_size + grid_size // 2, row * grid_size + grid_size // 2

def process_image(image_path):
    # Open and resize the image
    with Image.open(image_path) as img:
        img_resized = img.resize((1024, 768))  # XGA resolution
    
    # Add chess grid to the image and get dimensions
    cols, rows = add_chess_grid_to_image(img_resized)
    
    # Convert the image to base64
    buffered = io.BytesIO()
    img_resized.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Set up the Anthropic client
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        raise ValueError("CLAUDE_API_KEY not found in environment variables")
    client = Anthropic(api_key=api_key)

    # Prepare the message for the API
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64
                    }
                },
                {
                    "type": "text",
                    "text": f"Analyze this image with the chess-like grid overlay. Identify the Phone app and provide its location using the grid coordinates (e.g., B2). Also, give a brief description of its appearance. Format your response as a JSON object with fields 'grid_location' and 'description'."
                }
            ]
        }
    ]

    # Call the Anthropic API
    response = client.beta.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=messages,
        betas=["computer-use-2024-10-22"],
    )

    # Parse the JSON response
    result = json.loads(response.content[0].text)
    return result, img_resized

def draw_circle_on_image(image, chess_coord):
    draw = ImageDraw.Draw(image)
    x, y = chess_to_pixel(chess_coord)
    circle_radius = 100
    draw.ellipse((x-circle_radius, y-circle_radius, x+circle_radius, y+circle_radius), 
                 outline='red', width=3)
    return image

# Example usage
if __name__ == "__main__":
    image_path = "test_image.jpg"

    try:
        result, img = process_image(image_path)
        print(json.dumps(result, indent=2))

        # Draw circle on the image
        if 'grid_location' in result:
            img_with_circle = draw_circle_on_image(img, result['grid_location'])
            img_with_circle.show()
        else:
            print("Grid location not found in the API response.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")