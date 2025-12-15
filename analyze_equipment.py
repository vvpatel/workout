#!/usr/bin/env python3
"""
Script to analyze workout images and identify equipment
"""
import os
import glob
from PIL import Image
import base64
import json

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env file at startup
load_env_file()

def get_image_files():
    """Get all JPG image files in the current directory"""
    image_files = sorted(glob.glob("IMG_*.JPG"))
    return image_files

def analyze_image_with_openai(image_path):
    """Analyze image using OpenAI Vision API"""
    try:
        from openai import OpenAI
        
        # Initialize OpenAI client
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print("Warning: OPENAI_API_KEY not found in environment")
            return None
        
        client = OpenAI(api_key=api_key)
        
        # Read and encode image
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Call OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4o",  # Updated to use gpt-4o which supports vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "List all workout equipment, gym equipment, exercise machines, weights, or fitness tools visible in this image. Be specific about the type and name of each piece of equipment. Format as a simple list."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        return response.choices[0].message.content
    except ImportError:
        return None
    except Exception as e:
        print(f"Error analyzing {image_path}: {e}")
        return None

def analyze_image_basic(image_path):
    """Basic image analysis - extract metadata"""
    try:
        img = Image.open(image_path)
        width, height = img.size
        return f"Image: {os.path.basename(image_path)} - Size: {width}x{height}"
    except Exception as e:
        return f"Error reading {image_path}: {e}"

def main():
    image_files = get_image_files()
    print(f"Found {len(image_files)} image files")
    
    all_equipment = set()
    
    # Try OpenAI API first
    try:
        from openai import OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        print("Using OpenAI Vision API for analysis...")
        for img_file in image_files:
            print(f"Analyzing {img_file}...")
            result = analyze_image_with_openai(img_file)
            if result:
                # Extract equipment from result
                lines = result.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                        equipment = line.lstrip('- •0123456789. ').strip()
                        if equipment:
                            all_equipment.add(equipment)
    except (ImportError, ValueError) as e:
        print(f"OpenAI library not available or API key missing: {e}")
        print("Using basic analysis...")
        for img_file in image_files:
            print(f"Processing {img_file}...")
            analyze_image_basic(img_file)
    
    # If no equipment found via API, provide manual instructions
    if not all_equipment:
        print("\nCould not automatically identify equipment.")
        print("Please install openai library: pip install openai")
        print("And set OPENAI_API_KEY environment variable")
        return
    
    # Write to TPC file
    equipment_list = sorted(list(all_equipment))
    with open("TPC", "w") as f:
        f.write("Equipment Available for Workout Program:\n")
        f.write("=" * 50 + "\n\n")
        for i, equipment in enumerate(equipment_list, 1):
            f.write(f"{i}. {equipment}\n")
    
    print(f"\nFound {len(equipment_list)} unique pieces of equipment")
    print("Results written to TPC file")

if __name__ == "__main__":
    main()


