import modal
import time

# Initialize the Modal App (Replaces 'modal.Stub' in newer Modal versions)
app = modal.App("url-unshortener-api")

# Define the container image with necessary dependencies
image = modal.Image.debian_slim().pip_install("requests", "fastapi")


@app.function(image=image)
@modal.web_endpoint(method="GET")
def unshorten(url: str):
    import requests

    start_time = time.perf_counter()

    try:
        # We use a standard browser User-Agent to prevent email trackers
        # or link shorteners from blocking the request as a bot.
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        # Make the request and automatically follow redirects
        response = requests.get(url, allow_redirects=True, headers=headers, timeout=15)

        end_time = time.perf_counter()

        # Extract the chain of URLs we passed through
        redirect_chain = [res.url for res in response.history]

        return {
            "success": True,
            "input_url": url,
            "final_url": response.url,
            "redirect_count": len(response.history),
            "redirect_chain": redirect_chain,
            "time_taken_seconds": round(end_time - start_time, 4),
        }

    except requests.exceptions.RequestException as e:
        end_time = time.perf_counter()
        return {
            "success": False,
            "error": str(e),
            "input_url": url,
            "time_taken_seconds": round(end_time - start_time, 4),
        }
