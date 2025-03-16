"""
Test script to verify the image analysis works with HTTP URLs.
"""
import asyncio
import os
import sys
import time
from datetime import datetime

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import settings
from modules.analytics.batch_analytics import analyze_image_with_gemini_base64

# Test image URL (public S3 URL as HTTP)
TEST_IMAGE_URL = "https://intellibus-hackathon-bucket.s3.amazonaws.com/detections/rnXIjl_Rzy4_detection_20250316_015117.png"

async def test_http_image_analysis():
    """Test analyzing an image from an HTTP URL."""
    print(f"Testing image analysis with HTTP URL: {TEST_IMAGE_URL}")
    
    # Measure execution time
    start_time = time.time()
    
    # Define a simple prompt
    prompt = "Describe what you see in this traffic image."
    
    # Analyze the image
    result = analyze_image_with_gemini_base64(
        image_url=TEST_IMAGE_URL,
        api_key=settings.GEMINI_API_KEY,
        prompt=prompt
    )
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    print("\nAnalysis completed!")
    print(f"Execution time: {execution_time:.2f} seconds")
    print("\nPrompt:")
    print("-" * 80)
    print(prompt)
    print("\nResult:")
    print("-" * 80)
    print(result)

if __name__ == "__main__":
    asyncio.run(test_http_image_analysis()) 