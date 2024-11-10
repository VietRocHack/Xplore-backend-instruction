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

# Constants
GRID_SIZE = 50
PADDING_TOP = 100
PADDING_LEFT = 100

def add_padding_to_image(image, padding_top=PADDING_TOP, padding_left=PADDING_LEFT):
    width, height = image.size
    new_width = width + padding_left
    new_height = height + padding_top
    
    # Create a new white image with padding
    padded_image = Image.new('RGB', (new_width, new_height), color='white')
    padded_image.paste(image, (padding_left, padding_top))
    
    return padded_image, width // GRID_SIZE, height // GRID_SIZE

def chess_to_pixel(chess_coord):
    col = string.ascii_uppercase.index(chess_coord[0])
    row = int(chess_coord[1:]) - 1
    return (col * GRID_SIZE, row * GRID_SIZE)

def process_image(image_path):
    # Open and resize the image
    with Image.open(image_path) as img:
        img_resized = img.resize((1024, 768))  # XGA resolution
    
    # Add padding to the image and get dimensions
    img_with_padding, cols, rows = add_padding_to_image(img_resized)
    
    # Convert the image to base64
    buffered = io.BytesIO()
    img_with_padding.save(buffered, format="PNG")
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
                    "text": f"Analyze this image as if it had a chess-like grid overlay with {cols} columns (A-{string.ascii_uppercase[cols-1]}) and {rows} rows (1-{rows}). Each grid cell is {GRID_SIZE}x{GRID_SIZE} pixels. Identify all interesting or notable elements in the image. For each element, provide its location using the grid coordinates (e.g., ['B2', 'B3'] for an element spanning two cells) and a brief description. Format your response as a JSON object with an 'elements' array, where each element has 'grid_locations' (an array of grid coordinates) and 'description' fields. Limit your response to the 5 most interesting or notable elements."
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
    return result, img_resized  # Return the resized image without padding

def draw_ovals_on_image(image, elements):
    draw = ImageDraw.Draw(image)
    for element in elements:
        min_col = min(string.ascii_uppercase.index(loc[0]) for loc in element['grid_locations'])
        max_col = max(string.ascii_uppercase.index(loc[0]) for loc in element['grid_locations'])
        min_row = min(int(loc[1:]) - 1 for loc in element['grid_locations'])
        max_row = max(int(loc[1:]) - 1 for loc in element['grid_locations'])
        
        # Calculate coordinates without padding
        top_left = (min_col * GRID_SIZE, min_row * GRID_SIZE)
        bottom_right = ((max_col + 1) * GRID_SIZE, (max_row + 1) * GRID_SIZE)
        
        # Calculate center and radii for the oval
        EXTRA_PADDING = 50
        center_x = (top_left[0] + bottom_right[0]) / 2
        center_y = (top_left[1] + bottom_right[1]) / 2
        radius_x = (bottom_right[0] - top_left[0]) / 2 + EXTRA_PADDING
        radius_y = (bottom_right[1] - top_left[1]) / 2 + EXTRA_PADDING
        
        # Draw the oval
        draw.ellipse([center_x - radius_x, center_y - radius_y, 
                      center_x + radius_x, center_y + radius_y], 
                     outline='red', width=3)
    return image

# Example usage
if __name__ == "__main__":
    image_path = "test_image.jpg"

    try:
        result, img = process_image(image_path)
        print(json.dumps(result, indent=2))

        # Draw ovals on the image
        if 'elements' in result:
            img_with_ovals = draw_ovals_on_image(img, result['elements'])
            img_with_ovals.show()
        else:
            print("No elements found in the API response.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")