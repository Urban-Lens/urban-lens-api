"""Batch analytics module for processing traffic images"""
import boto3
import mimetypes
import logging
from datetime import datetime, timedelta
from botocore import UNSIGNED
from botocore.config import Config
from google import genai
from google.genai import types
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

async def get_hourly_images(db: AsyncSession, hour_timestamp: datetime = None) -> List[Dict[str, Any]]:
    """
    Get 5 evenly spaced image records from a specific hour.
    
    Args:
        db: Database session
        hour_timestamp: The hour to get records from (defaults to previous hour)
        
    Returns:
        List of records with image URLs and metadata
    """
    if hour_timestamp is None:
        # Default to the previous hour
        current_time = datetime.utcnow()
        hour_timestamp = current_time.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    
    # Set the hour range
    start_time = hour_timestamp
    end_time = start_time + timedelta(hours=1)
    
    logger.info(f"Fetching image data between {start_time} and {end_time}")
    
    # Query to get all records for the hour with output_img_path not null
    query = text("""
        SELECT id, timestamp, source_id, output_img_path, people_ct, vehicle_ct, detections
        FROM timeseries_analytics
        WHERE timestamp >= :start_time 
        AND timestamp < :end_time
        AND output_img_path IS NOT NULL
        ORDER BY timestamp
    """)
    
    result = await db.execute(
        query, 
        {"start_time": start_time, "end_time": end_time}
    )
    records = result.mappings().all()
    
    if not records:
        logger.warning(f"No records found between {start_time} and {end_time}")
        return []
    
    # Select 5 evenly spaced records
    total_records = len(records)
    if total_records <= 5:
        # Return all records if there are 5 or fewer
        return [dict(record) for record in records]
    else:
        # Calculate indices for evenly spaced records
        step = total_records / 5
        indices = [int(i * step) for i in range(5)]
        return [dict(records[i]) for i in indices]

def analyze_image_with_gemini_base64(s3_url: str, api_key: str, prompt: str = "What is in this image?") -> str:
    """
    Fetches an image from a public S3 URI, converts it into an inline base64-compatible data part,
    and analyzes it using the Gemini API.
    
    Args:
        s3_url: S3 URL of the image to analyze
        api_key: Gemini API key
        prompt: Prompt to send to Gemini
        
    Returns:
        Analysis response from Gemini
    """
    try:
        s3_prefix = "s3://"
        if not s3_url.startswith(s3_prefix):
            raise ValueError(f"Invalid S3 URL format: {s3_url}")

        # Remove the "s3://" prefix and split into bucket and key
        s3_url_no_prefix = s3_url[len(s3_prefix):]
        bucket_name, key = s3_url_no_prefix.split("/", 1)

        # Create an S3 client for anonymous access
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        response = s3.get_object(Bucket=bucket_name, Key=key)
        image_bytes = response["Body"].read()

        # Guess the MIME type based on the file extension (default to PNG if unknown)
        mime_type, _ = mimetypes.guess_type(s3_url)
        if mime_type is None:
            mime_type = "image/png"

        client = genai.Client(api_key=api_key)
        # Wrap the image bytes into a Gemini API inline part
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        # Generate content using Gemini with the provided prompt and inline image
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt, image_part]
        )
        return response.text
    except Exception as e:
        error_msg = f"Error during Gemini analysis with base64 image: {e}"
        logger.error(error_msg)
        return error_msg

async def store_analysis_results(db: AsyncSession, record_id: int, analysis_result: str) -> None:
    """
    Store the analysis results in the database.
    
    Args:
        db: Database session
        record_id: ID of the record to update
        analysis_result: Analysis result to store
    """
    try:
        # Update the record with the analysis result
        query = text("""
            UPDATE timeseries_analytics
            SET analysis_result = :analysis_result
            WHERE id = :id
        """)
        
        await db.execute(
            query, 
            {"id": record_id, "analysis_result": analysis_result}
        )
        await db.commit()
        logger.info(f"Stored analysis result for record {record_id}")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing analysis result: {e}")
        raise

async def process_hourly_traffic_images(db: AsyncSession, gemini_api_key: str, target_hour: datetime = None) -> List[Dict[str, Any]]:
    """
    Process 5 evenly spaced traffic images for a specific hour.
    
    Args:
        db: Database session
        gemini_api_key: Gemini API key
        target_hour: Hour to process (defaults to previous hour)
        
    Returns:
        List of records with analysis results
    """
    # Get the image records
    records = await get_hourly_images(db, target_hour)
    
    if not records:
        logger.warning("No images found to process")
        return []
    
    results = []
    for record in records:
        record_id = record["id"]
        s3_url = record["output_img_path"]
        source_id = record["source_id"]
        
        logger.info(f"Processing image for record {record_id} from source {source_id}")
        
        # Set up the prompt for traffic analysis
        analysis_prompt = (
            "Analyze this traffic image and provide: "
            "1. Count of vehicles visible "
            "2. Types of vehicles present (car, truck, bus, etc.) "
            "3. Traffic density assessment (light, moderate, heavy) "
            "4. Any unusual events or hazards"
        )
        
        # Analyze the image
        analysis_result = analyze_image_with_gemini_base64(s3_url, gemini_api_key, analysis_prompt)
        
        # Store the result
        try:
            await store_analysis_results(db, record_id, analysis_result)
            
            # Add to results list
            record["analysis_result"] = analysis_result
            results.append(record)
            
            logger.info(f"Successfully processed image for record {record_id}")
        except Exception as e:
            logger.error(f"Failed to process record {record_id}: {e}")
    
    return results

# Example usage for manual testing
async def test_process_images(db: AsyncSession):
    gemini_api_key = "AIzaSyDkyJnz9_Os6pyg-pgnjhHbgyIMdnsbbNQ"  # Replace with actual key from config
    results = await process_hourly_traffic_images(db, gemini_api_key)
    
    for result in results:
        print(f"Record ID: {result['id']}")
        print(f"Source ID: {result['source_id']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Analysis Result: {result['analysis_result']}")
        print("-" * 50)
