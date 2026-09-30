import os
import requests
import urllib.parse
import string
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv
from fpdf import FPDF
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def safe_text(text):
    return "".join(c for c in text if c in string.printable)

class Panel(BaseModel):
    panel_number: int
    visual_description: str
    dialogue: str

class ComicScript(BaseModel):
    title: str
    panels: list[Panel]

def generate_comic_story(user_idea: str) -> dict:
    print(f"Generating script for: {user_idea}")
    prompt = f"Create a 4-panel comic script based on this idea: {user_idea}. Provide a detailed visual description for each panel and dialogue."
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ComicScript,
        }
    )
    comic_data = response.parsed
    os.makedirs("static", exist_ok=True)
    
    image_paths = []
    for panel in comic_data.panels:
        print(f"Creating image for Panel {panel.panel_number}...")
        img_path = f"static/panel_{panel.panel_number}.jpg"
        
        try:
            safe_prompt = urllib.parse.quote(f"comic book art, colorful: {safe_text(panel.visual_description)}")
            img_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&nologo=true"
            img_response = requests.get(img_url, timeout=5)
            if img_response.status_code == 200:
                img = Image.open(BytesIO(img_response.content)).convert("RGB")
                img.save(img_path, "JPEG")
            else:
                raise Exception("API timeout")
        except:
            # Bulletproof fallback: Draw a clean comic placeholder box locally
            img = Image.new('RGB', (512, 512), color=(20, 24, 38))
            draw = ImageDraw.Draw(img)
            draw.rectangle([20, 20, 492, 492], outline=(0, 240, 255), width=6)
            draw.text((40, 220), f"PANEL {panel.panel_number}\n\n{safe_text(panel.visual_description[:50])}...", fill=(255, 238, 0))
            img.save(img_path, "JPEG")
            
        image_paths.append(img_path)
        
    pdf_path = generate_pdf(comic_data, image_paths)
    
    return {
        "title": comic_data.title,
        "panels": [p.model_dump() for p in comic_data.panels],
        "pdf_url": f"/{pdf_path}"
    }

def generate_pdf(comic_data: ComicScript, image_paths: list) -> str:
    print("Exporting PDF...")
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, txt=safe_text(comic_data.title), ln=True, align='C')
    pdf.ln(5)
    
    y_pos = 30
    for idx, panel in enumerate(comic_data.panels):
        if idx > 0 and idx % 2 == 0:
            pdf.add_page()
            y_pos = 20
            
        pdf.set_xy(10, y_pos)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 8, txt=f"Panel {panel.panel_number}", ln=True)
        
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(190, 6, txt=safe_text(f"Dialogue: {panel.dialogue}"))
        
        img_path = image_paths[idx]
        pdf.image(img_path, x=10, y=pdf.get_y() + 2, w=80)
        
        y_pos += 110 
        
    pdf_path = "static/comic_output.pdf"
    pdf.output(pdf_path)
    return pdf_path