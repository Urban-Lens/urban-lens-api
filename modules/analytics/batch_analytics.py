"""Batch analytics module for processing traffic images"""
import boto3
import mimetypes
import logging
import time
import requests
from datetime import datetime, timedelta
from botocore import UNSIGNED
from botocore.config import Config
from google import genai
from google.genai import types
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger(__name__)

# Hard-coded prompt for LLM analysis
LLM_ANALYSIS_PROMPT = """Provide a purely objective, fact-based structured analysis of the traffic image with no personal opinions or bias.

Analyze:
1. Vehicle types and counts visible in the image
2. Objective inferences about the socioeconomic characteristics based solely on vehicle types present
3. Pedestrian/foot traffic patterns and density
4. Level of activity/busyness in the area
5. Any notable infrastructure or environmental elements

Your response MUST:
- Be properly formatted with clear sections and bullet points
- Include only observable facts from the image
- Avoid subjective interpretations or personal opinions
- Present quantitative data when available
- Include a structured summary at the end

This is for an analytics engine, so maintain a professional, analytical tone throughout.
"""

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

def analyze_image_with_gemini_base64(image_url: str, api_key: str, prompt: str = "What is in this image?") -> str:
    """
    Fetches an image from a URL (S3 or HTTP), converts it into an inline base64-compatible data part,
    and analyzes it using the Gemini API.
    
    Args:
        image_url: URL of the image to analyze (can be S3 URL or HTTP URL)
        api_key: Gemini API key
        prompt: Prompt to send to Gemini
        
    Returns:
        Analysis response from Gemini
    """
    try:
        # Get image bytes based on URL type
        image_bytes = get_image_bytes(image_url)
        
        # Guess the MIME type based on the file extension (default to PNG if unknown)
        mime_type, _ = mimetypes.guess_type(image_url)
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
        error_msg = f"Error during Gemini analysis with image: {e}"
        logger.error(error_msg)
        return error_msg

def get_image_bytes(image_url: str) -> bytes:
    """
    Get image bytes from a URL, supporting both S3 and HTTP URLs.
    
    Args:
        image_url: URL of the image (S3 or HTTP)
        
    Returns:
        Bytes content of the image
    """
    # Parse URL to determine type
    parsed_url = urlparse(image_url)
    
    # Handle S3 protocol URLs (s3://)
    if parsed_url.scheme == 's3':
        # Extract bucket and key from S3 URL
        bucket_name = parsed_url.netloc
        key = parsed_url.path.lstrip('/')
        
        # Create an S3 client for anonymous access
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
        response = s3.get_object(Bucket=bucket_name, Key=key)
        return response["Body"].read()
    
    # Handle HTTP/HTTPS URLs
    elif parsed_url.scheme in ['http', 'https']:
        # For public S3 URLs (like https://bucket-name.s3.amazonaws.com/key)
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()  # Raise an exception for error status codes
        return response.content
    
    else:
        raise ValueError(f"Unsupported URL scheme: {parsed_url.scheme}")

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
            """Provide a purely objective, fact-based structured analysis of the traffic image with no personal opinions or bias.

Analyze:
1. Vehicle types and counts visible in the image
2. Objective inferences about the socioeconomic characteristics based solely on vehicle types present
3. Pedestrian/foot traffic patterns and density
4. Level of activity/busyness in the area
5. Any notable infrastructure or environmental elements

Your response MUST:
- Be properly formatted with clear sections and bullet points
- Include only observable facts from the image
- Avoid subjective interpretations or personal opinions
- Present quantitative data when available
- Include a structured summary at the end

This is for an analytics engine, so maintain a professional, analytical tone throughout.
"""
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

async def store_llm_analytics(db: AsyncSession, prompt: str, response: str, execution_time_ms: int) -> None:
    """
    Store LLM analytics data in the llm_analytics table.
    
    Args:
        db: Database session
        prompt: The prompt sent to the LLM
        response: The response from the LLM
        execution_time_ms: Execution time in milliseconds
    """
    try:
        # Insert a new record with the LLM analytics data
        query = text("""
            INSERT INTO llm_analytics (prompt, response, execution_time_ms)
            VALUES (:prompt, :response, :execution_time_ms)
            RETURNING id
        """)
        
        result = await db.execute(
            query, 
            {
                "prompt": prompt, 
                "response": response, 
                "execution_time_ms": execution_time_ms
            }
        )
        await db.commit()
        record_id = result.scalar_one()
        logger.info(f"Stored LLM analytics data with ID {record_id}")
        return record_id
    except Exception as e:
        await db.rollback()
        logger.error(f"Error storing LLM analytics data: {e}")
        raise

async def get_llm_analytics(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get LLM analytics data from the llm_analytics table.
    
    Args:
        db: Database session
        limit: Maximum number of records to return
        
    Returns:
        List of LLM analytics records
    """
    try:
        query = text("""
            SELECT id, timestamp, prompt, response, execution_time_ms
            FROM llm_analytics
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        
        result = await db.execute(query, {"limit": limit})
        records = result.mappings().all()
        return [dict(record) for record in records]
    except Exception as e:
        logger.error(f"Error retrieving LLM analytics data: {e}")
        raise

async def run_llm_analysis(db: AsyncSession, gemini_api_key: str) -> Dict[str, Any]:
    """
    Run LLM analysis with a hard-coded prompt and store the results.
    
    Args:
        db: Database session
        gemini_api_key: Gemini API key
        
    Returns:
        Dictionary with analysis results
    """
    # Get the most recent image record with output_img_path not null
    query = text("""
        SELECT id, timestamp, source_id, output_img_path
        FROM timeseries_analytics
        WHERE output_img_path IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    
    result = await db.execute(query)
    record = result.mappings().first()
    
    if not record:
        logger.warning("No images found to process")
        return {"error": "No images found to process"}
    
    record_id = record["id"]
    image_url = record["output_img_path"]
    source_id = record["source_id"]
    
    logger.info(f"Processing image for record {record_id} from source {source_id}")
    
    # Set up the prompt for traffic analysis (using the hard-coded prompt)
    analysis_prompt = LLM_ANALYSIS_PROMPT
    
    # Measure execution time
    start_time = time.time()
    
    # Analyze the image (supports both S3 and HTTP URLs)
    analysis_result = analyze_image_with_gemini_base64(image_url, gemini_api_key, analysis_prompt)
    
    # Calculate execution time in milliseconds
    execution_time_ms = int((time.time() - start_time) * 1000)
    
    # Store the analysis result in the timeseries_analytics table
    await store_analysis_results(db, record_id, analysis_result)
    
    # Store LLM analytics data
    await store_llm_analytics(db, analysis_prompt, analysis_result, execution_time_ms)
    
    # Return the result
    return {
        "id": record_id,
        "source_id": source_id,
        "timestamp": record["timestamp"],
        "analysis_result": analysis_result,
        "execution_time_ms": execution_time_ms
    }

async def get_traffic_metrics(db: AsyncSession) -> Dict[str, Any]:
    """
    Get traffic metrics from the timeseries_analytics table.
    
    Returns two types of metrics:
    1. Totals: sum of people_ct and vehicle_ct
    2. Time series: people_ct and vehicle_ct over time
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with totals and time series data
    """
    try:
        # Get totals
        totals_query = text("""
            SELECT 
                SUM(people_ct) AS total_people,
                SUM(vehicle_ct) AS total_vehicles,
                COUNT(*) AS total_records
            FROM timeseries_analytics
            WHERE people_ct IS NOT NULL OR vehicle_ct IS NOT NULL
        """)
        
        totals_result = await db.execute(totals_query)
        totals = totals_result.mappings().first()
        
        # Get time series data
        timeseries_query = text("""
            SELECT 
                timestamp,
                source_id,
                people_ct,
                vehicle_ct
            FROM timeseries_analytics
            WHERE people_ct IS NOT NULL OR vehicle_ct IS NOT NULL
            ORDER BY timestamp
        """)
        
        timeseries_result = await db.execute(timeseries_query)
        timeseries_data = timeseries_result.mappings().all()
        
        # Format the response
        return {
            "totals": {
                "total_people": int(totals["total_people"] or 0),
                "total_vehicles": int(totals["total_vehicles"] or 0),
                "total_records": int(totals["total_records"] or 0)
            },
            "timeseries": [
                {
                    "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                    "source_id": record["source_id"],
                    "people_count": record["people_ct"],
                    "vehicle_count": record["vehicle_ct"]
                } 
                for record in timeseries_data
            ]
        }
    except Exception as e:
        logger.error(f"Error getting traffic metrics: {e}")
        raise
