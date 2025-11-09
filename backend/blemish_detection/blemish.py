"""
Blemish detection using Google Gemini Robotics ER 1.5 Preview model.
Detects blemishes or rot on food/fruit items using segmentation masks.
"""

import json
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

load_dotenv()


def detect_blemishes(
    image_path: str,
    api_key: Optional[str] = None,
    model_name: str = "models/gemini-robotics-er-1.5-preview",
    temperature: float = 0.0,
) -> Dict:
    """
    Detect blemishes or rot on a food/fruit item using Google Gemini segmentation.
    
    Args:
        image_path: Path to the input image file
        api_key: Google Gemini API key (if None, uses GEMINI_API_KEY env var)
        model_name: Name of the Gemini model to use
        temperature: Temperature for the model (0.0 for deterministic results)
    
    Returns:
        Dictionary containing:
            - image: PIL Image object (original image)
            - bboxes: List of bounding boxes, each with:
                - box_2d: [ymin, xmin, ymax, xmax] in normalized coordinates (0-1000)
                - label: Text label describing the blemish
            - labels: List of all labels found
    """
    # Initialize API key
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable not set. "
                "Please set it or pass api_key parameter."
            )
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Load image
    image = Image.open(image_path)
    print(f"🔍 [Gemini] Starting blemish detection for image: {image_path}")
    
    # Convert to RGB if necessary (for PNG with transparency)
    if image.mode != "RGB":
        image_rgb = Image.new("RGB", image.size, (255, 255, 255))
        image_rgb.paste(image, mask=image.split()[3] if image.mode == "RGBA" else None)
        image = image_rgb
    
    # Use the exact same prompt format as the segmentation example
    # From consts.tsx: ['Give the segmentation masks for', 'all objects', '. Output a JSON list...']
    prompt = (
        "Give the segmentation masks for individual blemish spots, rot patches, damaged areas, or irregular regions on the food item. "
        "Detect each damaged spot separately, not the entire food item. "
        "Output a JSON list of segmentation masks where each entry contains the 2D bounding box in the key \"box_2d\", the segmentation mask in key \"mask\", and the text label in the key \"label\". Use descriptive labels."
    )
    
    # Prepare the request payload (similar to TypeScript version)
    # Create the content parts - PIL Images can be passed directly
    contents = [image, prompt]
    
    # Generate content config with correct format
    generate_content_config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json",
        thinking_config=types.ThinkingConfig(
            thinking_budget=0,  # Disable thinking for faster, more direct responses
        ),
        # image_config=types.ImageConfig(
        #     image_size="1K",
        # ),
    )
    
    try:
        print(f"🤖 [Gemini] Calling Gemini API (model: {model_name})...")
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=generate_content_config,
        )
        print(f"✅ [Gemini] Received response from Gemini API")
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Handle markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        # Parse JSON response
        print(f"📊 [Gemini] Parsing response JSON...")
        annotations = json.loads(response_text)
        
        # Extract only bboxes and labels (no masks)
        bboxes = []
        labels = []
        for ann in annotations:
            if "box_2d" in ann and "label" in ann:
                bboxes.append({
                    "box_2d": ann["box_2d"],
                    "label": ann["label"]
                })
                labels.append(ann["label"])
        
        print(f"✨ [Gemini] Processing complete! Found {len(bboxes)} blemish(es)")
        
        return {
            "image": image,
            "bboxes": bboxes,
            "labels": labels,
        }
    
    except Exception as e:
        print(f"❌ [Gemini] Error during processing: {str(e)}")
        raise RuntimeError(f"Error calling Gemini API: {str(e)}") from e


def visualize_detections(
    image: Image.Image,
    bboxes: List[Dict],
    output_path: str,
) -> Image.Image:
    """
    Visualize blemish detections on the image.
    
    Args:
        image: PIL Image object
        bboxes: List of bounding boxes with box_2d and label
        output_path: Path to save the output image
    
    Returns:
        PIL Image with visualizations
    """
    # Create a copy for drawing
    vis_image = image.copy().convert("RGB")
    draw = ImageDraw.Draw(vis_image)
    
    # Colors for different detections
    colors = [
        (255, 0, 0),      # Red
        (0, 255, 0),      # Green
        (0, 0, 255),      # Blue
        (255, 255, 0),    # Yellow
        (255, 0, 255),    # Magenta
        (0, 255, 255),    # Cyan
    ]
    
    img_width, img_height = image.size
    
    for idx, bbox_data in enumerate(bboxes):
        color = colors[idx % len(colors)]
        
        # Parse bounding box (remember: y first, then x, normalized to 0-1000)
        box_2d = bbox_data.get("box_2d", [])
        if len(box_2d) != 4:
            continue
        
        ymin, xmin, ymax, xmax = box_2d
        
        # Convert from normalized (0-1000) to pixel coordinates
        xmin_px = int((xmin / 1000) * img_width)
        ymin_px = int((ymin / 1000) * img_height)
        xmax_px = int((xmax / 1000) * img_width)
        ymax_px = int((ymax / 1000) * img_height)
        
        # Draw bounding box
        draw.rectangle(
            [xmin_px, ymin_px, xmax_px, ymax_px],
            outline=color,
            width=3,
        )
        
        # Draw label
        label = bbox_data.get("label", f"Blemish {idx + 1}")
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None
        
        # Get text bounding box for background
        bbox = draw.textbbox((xmin_px, ymin_px - 20), label, font=font)
        draw.rectangle(bbox, fill=color)
        draw.text((xmin_px, ymin_px - 20), label, fill=(255, 255, 255), font=font)
    
    # Save the visualization
    vis_image.save(output_path)
    return vis_image


if __name__ == "__main__":
    # Default input/output paths
    input_path = "input.png"
    output_path = "output.png"
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' not found.")
        print("Please provide an 'input.png' file in the current directory.")
        exit(1)
    
    print(f"Processing image: {input_path}")
    print("Detecting blemishes using Gemini Robotics ER 1.5 Preview...")
    
    try:
        # Detect blemishes
        result = detect_blemishes(input_path)
        
        print(f"\nFound {len(result['bboxes'])} blemish(es):")
        for i, bbox in enumerate(result["bboxes"]):
            label = bbox.get("label", "Unknown")
            box_2d = bbox.get("box_2d", [])
            print(f"  {i + 1}. {label} - Box: {box_2d}")
        
        # Visualize and save
        print(f"\nVisualizing detections and saving to: {output_path}")
        visualize_detections(
            result["image"],
            result["bboxes"],
            output_path,
        )
        
        print(f"\nDone! Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

