import os
import json
from fastapi import FastAPI, HTTPException
from google import genai
from pydantic import BaseModel
from google.genai import types
import dotenv
from typing import List
from pydantic import BaseModel

dotenv.load_dotenv()


class Item(BaseModel):
    name: str
    quantity: int
    aisle: str


class ShoppingListResponse(BaseModel):
    items: List[Item]


schema_config = {
    "response_mime_type": "application/json",
    "response_schema": list[Item],  # <— Gemini will use this schema
}


from fastapi.responses import JSONResponse, FileResponse
from fastapi.requests import Request
from fastapi.staticfiles import StaticFiles

# The app will listen on port 8080 (see Dockerfile CMD)
app = FastAPI()

# Mount static directory for favicon
import pathlib

static_dir = pathlib.Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})


# Initialize the Gen AI client for Vertex AI
client = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
)


@app.get("/get-list", response_model=ShoppingListResponse)
async def shopping_list():
    prompt = (
        "Think of an American household with n adults and m children."
        "Think of an event that this household might be preparing for"
        "Generate a Costco shopping list of 5-10 items for that household"
        "The list should be in JSON format as an array of objects. "
        "Each object must have fields: name (string), quantity (integer), aisle (string)."
        "Return the list as a JSON array. Don't include any additional text or formatting."
    )

    # Call the Gemini model via the Gen AI SDK
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=schema_config,
        )  # :contentReference[oaicite:1]{index=1}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GenAI API error: {e}")

    # Parse the returned text as JSON
    raw = response.text
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse JSON from GenAI response: {e}",
        )

    return {"items": items}
