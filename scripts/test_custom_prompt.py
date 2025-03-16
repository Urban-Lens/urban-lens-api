#!/usr/bin/env python
"""
Test script for the custom traffic image analysis prompt
"""
import asyncio
import sys
import os
from pathlib import Path
import logging

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

from config.config import settings
from modules.analytics.batch_analytics import analyze_image_with_gemini_base64

# Test S3 image URL
TEST_IMAGE_URL = "s3://intellibus-hackathon-bucket/detection_test/Screenshot 2025-03-15 at 4.54.39 PM.png"

# Custom analysis prompt
CUSTOM_PROMPT = """give a stuctured analysis based on the traffic image 

analyse the image to look at the type of vehicles, also i want to get some inference on the overall income based on the vehicles, also analyze foot traffic and so on give insights in to whether it's a busy area or not 
etc"""

async def test_custom_prompt():
    """Test the custom analysis prompt on a specific image"""
    logger.info("Testing custom analysis prompt...")
    
    try:
        # Analyze the image with the custom prompt
        result = analyze_image_with_gemini_base64(
            s3_url=TEST_IMAGE_URL,
            api_key=settings.GEMINI_API_KEY,
            prompt=CUSTOM_PROMPT
        )
        
        logger.info("Analysis result:")
        print("\n" + "="*80)
        print("CUSTOM PROMPT ANALYSIS RESULT:")
        print("="*80)
        print(result)
        print("="*80)
        
        return result
    except Exception as e:
        logger.error(f"Error in test_custom_prompt: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    result = asyncio.run(test_custom_prompt())
    
    if result:
        # Save the result to a file for reference
        output_dir = Path(__file__).parent / "output"
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "custom_prompt_analysis.txt"
        with open(output_file, "w") as f:
            f.write(result)
        
        print(f"Result saved to {output_file}")
    else:
        print("Analysis failed") 