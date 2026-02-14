from google import genai
from google.genai import types
from foundry.config.settings import settings
from PIL import Image

def generate_image(prompt: str):
    
    aspect_ratio = "1:1" # "1:1","2:3","3:2","3:4","4:3","4:5","5:4","9:16","16:9","21:9"
    resolution = "1K" # "1K", "2K", "4K"

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=[
            prompt,
            Image.open("coco_beach.jpg")
        ],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE'],
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
                image_size=resolution
            ),
        )
    )

    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif image:= part.as_image():
            image.save("coco_4.png")