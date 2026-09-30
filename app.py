from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from core import generate_comic_story

# Initialize FastAPI app
app = FastAPI(title="ComicCraft AI")

# Mount the static directory to serve generated images and the final PDF
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates for the frontend UI
templates = Jinja2Templates(directory="templates")

# Define the expected JSON input schema from the frontend
class PromptRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renders the main web interface."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/generate")
async def generate(request: PromptRequest):
    """Handles the comic generation request and returns JSON data."""
    if not request.prompt:
        return JSONResponse(status_code=400, content={"error": "Please provide a story idea."})
    
    try:
        # Call the PyTorch/Diffusers and Gemini logic from core.py
        comic_data = generate_comic_story(request.prompt)
        
        # Return the generated panels and the PDF URL back to the frontend
        return comic_data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    # Runs the Uvicorn ASGI server on port 8000 (Required by SkillWallet rubric)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)