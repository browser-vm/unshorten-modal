import modal
import time
from fastapi import FastAPI, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import List, Optional

# Initialize the Modal App
app = modal.App("url-unshortener-api")

# Add 'pydantic' to our image dependencies for data validation
image = modal.Image.debian_slim().pip_install("requests", "fastapi==0.135.1", "pydantic")

# Initialize the FastAPI app with metadata for the docs page
web_app = FastAPI(
    title="URL Unshortener API",
    description="An API to trace redirects, count hops, and unshorten URLs.",
    version="0.1.0",
)


# Define a Pydantic model so the docs page knows exactly what the response looks like
class UnshortenResponse(BaseModel):
    success: bool
    input_url: str
    final_url: Optional[str] = None
    redirect_count: Optional[int] = None
    redirect_chain: Optional[List[str]] = None
    time_taken_seconds: float
    error: Optional[str] = None


# Redirect the base URL to the Swagger docs
@web_app.get("/", include_in_schema=False)
def redirect_to_docs():
    """Redirects the root URL to the API documentation."""
    return RedirectResponse(url="/docs")


@web_app.get("/unshorten", response_model=UnshortenResponse, tags=["Unshortener"])
def unshorten(
    url: str = Query(..., description="The short URL or tracker link to resolve"),
):
    """
    Takes a URL, follows all HTTP redirects, and returns the final destination URL
    along with the redirect chain and execution time.
    """
    import requests

    start_time = time.perf_counter()

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, allow_redirects=True, headers=headers, timeout=15)
        end_time = time.perf_counter()

        redirect_chain = [res.url for res in response.history]

        return UnshortenResponse(
            success=True,
            input_url=url,
            final_url=response.url,
            redirect_count=len(response.history),
            redirect_chain=redirect_chain,
            time_taken_seconds=round(end_time - start_time, 4),
        )

    except requests.exceptions.RequestException as e:
        end_time = time.perf_counter()
        return UnshortenResponse(
            success=False,
            input_url=url,
            time_taken_seconds=round(end_time - start_time, 4),
            error=str(e),
        )


# Bind the FastAPI app to Modal
@app.function(image=image)
@modal.asgi_app()
def fastapi_app():
    return web_app
