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
import uuid
import json
import re

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

async def get_traffic_metrics(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = None, 
    address_filter: Optional[str] = None,
    location_id: Optional[uuid.UUID] = None,
    time_aggregation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get traffic metrics from the timeseries_analytics table.
    
    Returns two types of metrics:
    1. Averages: average of people_ct and vehicle_ct across all data
    2. Time series: people_ct and vehicle_ct over time, averaged when aggregated
    
    Args:
        db: Database session
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return (None for unlimited)
        address_filter: Optional filter by location address (partial match)
        location_id: Optional filter by location ID
        time_aggregation: Time aggregation level (hour, day, or None for raw data)
        
    Returns:
        Dictionary with averages and time series data
    """
    try:
        # Base parameters
        params = {"skip": skip}
        address_condition = ""
        location_id_condition = ""
        
        # Set limit if provided
        if limit is not None:
            params["limit"] = limit
        
        # Add address filter if provided
        if address_filter:
            address_condition = "AND l.address ILIKE :address_filter"
            params["address_filter"] = f"%{address_filter}%"
            
        # Add location_id filter if provided
        if location_id:
            location_id_condition = "AND l.id = :location_id"
            params["location_id"] = str(location_id)
        
        # Get averages with location join
        averages_query = text(f"""
            SELECT 
                AVG(ta.people_ct) AS avg_people,
                AVG(ta.vehicle_ct) AS avg_vehicles,
                COUNT(ta.id) AS total_records
            FROM timeseries_analytics ta
            LEFT JOIN location l ON ta.source_id = l.id::varchar
            WHERE (ta.people_ct IS NOT NULL OR ta.vehicle_ct IS NOT NULL)
                AND (l.address IS NOT NULL)
                {address_condition}
                {location_id_condition}
        """)
        
        averages_result = await db.execute(averages_query, params)
        averages = averages_result.mappings().first()
        
        # Time series data with location info and potential time aggregation
        time_select = ""
        time_group_by = ""
        
        if time_aggregation == "hour":
            time_select = "date_trunc('hour', ta.timestamp) as timestamp,"
            time_group_by = "GROUP BY date_trunc('hour', ta.timestamp), ta.source_id, l.address"
        elif time_aggregation == "day":
            time_select = "date_trunc('day', ta.timestamp) as timestamp,"
            time_group_by = "GROUP BY date_trunc('day', ta.timestamp), ta.source_id, l.address"
        else:
            # Raw data
            time_select = "ta.timestamp,"
            time_group_by = ""
            
        # Build base query
        base_query = f"""
            SELECT 
                {time_select}
                ta.source_id,
                l.address,
        """
        
        # Add aggregation for people and vehicles if needed
        if time_aggregation:
            # Use AVG for hour and day aggregations
            base_query += """
                AVG(ta.people_ct) as people_ct,
                AVG(ta.vehicle_ct) as vehicle_ct,
                COUNT(*) as sample_count
            """
        else:
            base_query += """
                ta.people_ct,
                ta.vehicle_ct,
                1 as sample_count
            """
            
        # Complete the query
        timeseries_query = text(f"""
            {base_query}
            FROM timeseries_analytics ta
            LEFT JOIN location l ON ta.source_id = l.id::varchar
            WHERE (ta.people_ct IS NOT NULL OR ta.vehicle_ct IS NOT NULL)
                AND (l.address IS NOT NULL)
                {address_condition}
                {location_id_condition}
            {time_group_by}
            ORDER BY timestamp DESC
            {f"LIMIT :limit" if limit is not None else ""}
            {f"OFFSET :skip" if skip > 0 else ""}
        """)
        
        timeseries_result = await db.execute(timeseries_query, params)
        timeseries_data = timeseries_result.mappings().all()
        
        # Get total count for pagination
        if time_aggregation:
            # We need a different count query for aggregated data
            count_query = text(f"""
                SELECT COUNT(*) as total FROM (
                    SELECT 
                        {time_select.split(' as ')[0]}
                    FROM timeseries_analytics ta
                    LEFT JOIN location l ON ta.source_id = l.id::varchar
                    WHERE (ta.people_ct IS NOT NULL OR ta.vehicle_ct IS NOT NULL)
                        AND (l.address IS NOT NULL)
                        {address_condition}
                        {location_id_condition}
                    {time_group_by}
                ) as subquery
            """)
        else:
            count_query = text(f"""
                SELECT COUNT(*) as total
                FROM timeseries_analytics ta
                LEFT JOIN location l ON ta.source_id = l.id::varchar
                WHERE (ta.people_ct IS NOT NULL OR ta.vehicle_ct IS NOT NULL)
                    AND (l.address IS NOT NULL)
                    {address_condition}
                    {location_id_condition}
            """)
        
        count_result = await db.execute(count_query, params)
        total_count = count_result.scalar_one()
        
        # Format the response
        return {
            "averages": {
                "avg_people": round(float(averages["avg_people"] or 0), 2),
                "avg_vehicles": round(float(averages["avg_vehicles"] or 0), 2),
                "total_records": int(averages["total_records"] or 0)
            },
            "timeseries": [
                {
                    "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                    "source_id": record["source_id"],
                    "address": record["address"],
                    "people_count": round(float(record["people_ct"] or 0), 2),
                    "vehicle_count": round(float(record["vehicle_ct"] or 0), 2),
                    "sample_count": int(record["sample_count"] or 0)
                } 
                for record in timeseries_data
            ],
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit
            },
            "aggregation": time_aggregation or "none"
        }
    except Exception as e:
        logger.error(f"Error getting traffic metrics: {e}")
        raise

async def get_traffic_metrics_by_location(db: AsyncSession, location_id: Optional[uuid.UUID] = None, address_filter: Optional[str] = None, skip: int = 0, limit: int = None) -> Dict[str, Any]:
    """
    Get traffic metrics from the timeseries_analytics table grouped by location.
    
    Returns:
    1. Totals by location: sum of people_ct and vehicle_ct for each location
    2. Time series by location: people_ct and vehicle_ct over time for each location ordered by latest timestamp
    3. Location details: address, latitude, longitude, etc.
    
    Args:
        db: Database session
        location_id: Optional UUID to filter by specific location
        address_filter: Optional filter by location address (partial match)
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return (None for unlimited)
        
    Returns:
        Dictionary with locations data containing metrics
    """
    try:
        # Base location filter condition
        location_filter = ""
        address_condition = ""
        params = {"skip": skip}
        
        # Set limit if provided
        if limit is not None:
            params["limit"] = limit
        
        if location_id:
            location_filter = "AND l.id = :location_id"
            params["location_id"] = str(location_id)
            
        if address_filter:
            address_condition = "AND l.address ILIKE :address_filter"
            params["address_filter"] = f"%{address_filter}%"
        
        # Get locations with their metrics totals
        locations_query = text(f"""
            SELECT 
                l.id AS location_id,
                l.address,
                l.latitude,
                l.longitude,
                l.description,
                l.tags,
                l.input_stream_url,
                l.output_stream_url,
                l.thumbnail,
                COUNT(ta.id) AS total_records,
                SUM(ta.people_ct) AS total_people,
                SUM(ta.vehicle_ct) AS total_vehicles,
                MAX(ta.timestamp) AS latest_timestamp
            FROM 
                location l
            LEFT JOIN 
                timeseries_analytics ta ON l.id::varchar = ta.source_id
            WHERE 
                (ta.people_ct IS NOT NULL OR ta.vehicle_ct IS NOT NULL OR ta.id IS NULL)
                {location_filter}
                {address_condition}
            GROUP BY 
                l.id
            ORDER BY 
                MAX(ta.timestamp) DESC NULLS LAST
            {f"LIMIT :limit" if limit is not None else ""}
            {f"OFFSET :skip" if skip > 0 else ""}
        """)
        
        locations_result = await db.execute(locations_query, params)
        locations_data = locations_result.mappings().all()
        
        # Get total count for pagination
        count_query = text(f"""
            SELECT COUNT(DISTINCT l.id) as total
            FROM location l
            LEFT JOIN timeseries_analytics ta ON l.id::varchar = ta.source_id
            WHERE TRUE
                {location_filter}
                {address_condition}
        """)
        
        count_result = await db.execute(count_query, params)
        total_count = count_result.scalar_one()
        
        # Get time series data for each location
        locations_with_metrics = []
        
        for location in locations_data:
            location_dict = dict(location)
            
            # Convert UUID to string
            location_id_str = str(location["location_id"])
            
            # Get time series data for this location
            timeseries_query = text("""
                SELECT 
                    timestamp,
                    people_ct,
                    vehicle_ct
                FROM 
                    timeseries_analytics
                WHERE 
                    source_id = :source_id
                    AND (people_ct IS NOT NULL OR vehicle_ct IS NOT NULL)
                ORDER BY 
                    timestamp DESC
            """)
            
            timeseries_result = await db.execute(timeseries_query, {"source_id": location_id_str})
            timeseries_data = timeseries_result.mappings().all()
            
            # Format time series data
            timeseries = [
                {
                    "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                    "people_count": record["people_ct"],
                    "vehicle_count": record["vehicle_ct"]
                } 
                for record in timeseries_data
            ]
            
            # Combine location and metrics
            location_with_metrics = {
                "id": location["location_id"],
                "address": location["address"],
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "description": location["description"],
                "tags": location["tags"],
                "input_stream_url": location["input_stream_url"],
                "output_stream_url": location["output_stream_url"],
                "thumbnail": location["thumbnail"],
                "latest_timestamp": location["latest_timestamp"].isoformat() if location["latest_timestamp"] else None,
                "metrics": {
                    "total_people": int(location["total_people"] or 0),
                    "total_vehicles": int(location["total_vehicles"] or 0),
                    "total_records": int(location["total_records"] or 0)
                },
                "timeseries": timeseries
            }
            
            locations_with_metrics.append(location_with_metrics)
        
        # Get a list of all location IDs for the frontend filter
        all_locations_query = text("""
            SELECT 
                id, 
                address
            FROM 
                location
            ORDER BY 
                address
        """)
        
        all_locations_result = await db.execute(all_locations_query)
        all_locations = all_locations_result.mappings().all()
        
        location_filters = [
            {
                "id": str(loc["id"]),
                "address": loc["address"]
            }
            for loc in all_locations
        ]
        
        return {
            "locations": locations_with_metrics,
            "filters": {
                "locations": location_filters
            },
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting traffic metrics by location: {e}")
        raise

async def generate_business_recommendation(db: AsyncSession, location_id: uuid.UUID, gemini_api_key: str, industry: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a business recommendation based on traffic metrics data for a specific location.
    
    Args:
        db: Database session
        location_id: Location ID to generate recommendation for
        gemini_api_key: Gemini API key
        industry: Optional industry context for more targeted recommendations
        
    Returns:
        Dictionary with recommendation results
    """
    try:
        # Get location information
        location_query = text("""
            SELECT id, address
            FROM location
            WHERE id = :location_id
        """)
        
        location_result = await db.execute(location_query, {"location_id": str(location_id)})
        location = location_result.mappings().first()
        
        if not location:
            raise ValueError(f"Location with ID {location_id} not found")
        
        # Get hourly aggregated data for the location
        hourly_data_query = text("""
            SELECT 
                date_trunc('hour', timestamp) as hour,
                SUM(people_ct) as total_people,
                SUM(vehicle_ct) as total_vehicles,
                COUNT(*) as data_points
            FROM 
                timeseries_analytics
            WHERE 
                source_id = :location_id
                AND people_ct IS NOT NULL 
                AND vehicle_ct IS NOT NULL
            GROUP BY 
                date_trunc('hour', timestamp)
            ORDER BY 
                hour DESC
            LIMIT 168  -- Last 7 days of hourly data
        """)
        
        hourly_result = await db.execute(hourly_data_query, {"location_id": str(location_id)})
        hourly_data = hourly_result.mappings().all()
        
        if not hourly_data:
            raise ValueError(f"No traffic data found for location {location_id}")
        
        # Format the data for the LLM
        formatted_data = []
        for record in hourly_data:
            formatted_data.append({
                "hour": record["hour"].isoformat(),
                "total_people": int(record["total_people"] or 0),
                "total_vehicles": int(record["total_vehicles"] or 0),
                "data_points": int(record["data_points"])
            })
        
        # Create the prompt with industry context if available
        industry_context = f" for the {industry} industry" if industry else ""
        
        prompt = f"""
Based on the following traffic data for location "{location['address']}", please provide recommendations for the best type and placement of physical marketing ads{industry_context}.

The data represents hourly foot traffic (people count) and vehicle traffic (vehicle count) over time.

Data:
{json.dumps(formatted_data, indent=2)}

Based on this data:
1. What's the best place to place a physical marketing ad?
2. What type of ads would be most effective (digital, location-based, pop-up events, etc.)?
3. When would be the best times to display these ads?
{"4. How can these recommendations be tailored specifically for the " + industry + " industry?" if industry else ""}

Please provide specific, actionable recommendations. Return your response as a list of short, concise recommendations, with one sentence per recommendation. Focus on practical marketing strategies based on the traffic patterns{" that are relevant to the " + industry + " industry" if industry else ""}.
"""
        
        # Measure execution time
        start_time = time.time()
        
        # Get recommendation from Gemini
        client = genai.Client(api_key=gemini_api_key)
        response = client.models.generate_content(
            model="gemini-1.5-pro",
            contents=prompt
        )
        
        # Process the recommendation
        recommendation_text = response.text
        
        # Calculate execution time in milliseconds
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract recommendations as a list
        recommendations = []
        for line in recommendation_text.strip().split('\n'):
            # Keep only lines that look like list items
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or bool(re.match(r'^\d+\.', line))):
                # Remove list markers and clean
                clean_line = re.sub(r'^[-*\d\.]+\s*', '', line).strip()
                if clean_line:
                    recommendations.append(clean_line)
        
        # If the LLM didn't format as a list, try to split by periods
        if not recommendations:
            for sentence in recommendation_text.split('.'):
                clean_sentence = sentence.strip()
                if clean_sentence:
                    recommendations.append(clean_sentence + '.')
        
        # Store the recommendation in the LLM analytics table
        recommendation_id = await store_llm_analytics(
            db=db, 
            prompt=prompt, 
            response=recommendation_text, 
            execution_time_ms=execution_time_ms
        )
        
        result = {
            "location_id": location_id,
            "location_address": location["address"],
            "recommendations": recommendations,
            "industry": industry,
            "recommendation_id": recommendation_id,
            "generated_at": datetime.utcnow().isoformat(),
            "execution_time_ms": execution_time_ms
        }
        
        return result
    except Exception as e:
        logger.error(f"Error generating business recommendation: {e}")
        raise

async def get_business_recommendations(db: AsyncSession, limit: int = 10, location_id: Optional[uuid.UUID] = None) -> List[Dict[str, Any]]:
    """
    Get business recommendations from the LLM analytics table.
    
    Args:
        db: Database session
        limit: Maximum number of records to return
        location_id: Optional location ID to filter by
        
    Returns:
        List of business recommendation records
    """
    try:
        if location_id:
            # First get the location address
            location_query = text("""
                SELECT address
                FROM location
                WHERE id = :location_id
            """)
            location_result = await db.execute(location_query, {"location_id": str(location_id)})
            location = location_result.mappings().first()
            
            if not location:
                # Location not found, return empty list
                return []
            
            # Use the location address to filter recommendations
            location_address = location["address"]
            query_text = """
                SELECT 
                    id, 
                    timestamp, 
                    prompt, 
                    response, 
                    execution_time_ms
                FROM 
                    llm_analytics
                WHERE 
                    prompt LIKE '%Based on the following traffic data for location%'
                    AND prompt LIKE :location_pattern
            """
            params = {
                "limit": limit,
                "location_pattern": f"%location \"{location_address}\"%"
            }
        else:
            # Base query without location filter
            query_text = """
                SELECT 
                    id, 
                    timestamp, 
                    prompt, 
                    response, 
                    execution_time_ms
                FROM 
                    llm_analytics
                WHERE 
                    prompt LIKE '%Based on the following traffic data for location%'
            """
            params = {"limit": limit}
        
        # Add ordering and limit
        query_text += " ORDER BY timestamp DESC LIMIT :limit"
        
        # Execute the query
        query = text(query_text)
        result = await db.execute(query, params)
        records = result.mappings().all()
        
        recommendations = []
        for record in records:
            # Try to extract the location info from the prompt
            location_match = re.search(r'location "([^"]+)"', record["prompt"])
            location_address = location_match.group(1) if location_match else "Unknown location"
            
            # Extract recommendations from the response
            recommendation_text = record["response"]
            recs_list = []
            
            for line in recommendation_text.strip().split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('*') or bool(re.match(r'^\d+\.', line))):
                    clean_line = re.sub(r'^[-*\d\.]+\s*', '', line).strip()
                    if clean_line:
                        recs_list.append(clean_line)
            
            # If no list items were found, try to split by periods
            if not recs_list:
                for sentence in recommendation_text.split('.'):
                    clean_sentence = sentence.strip()
                    if clean_sentence:
                        recs_list.append(clean_sentence + '.')
            
            # Format the record
            rec = {
                "id": record["id"],
                "timestamp": record["timestamp"].isoformat(),
                "location_address": location_address,
                "recommendations": recs_list,
                "execution_time_ms": record["execution_time_ms"]
            }
            
            # Add location_id to the response if we're filtering by location
            if location_id:
                rec["location_id"] = location_id
                
            recommendations.append(rec)
        
        return recommendations
    except Exception as e:
        logger.error(f"Error retrieving business recommendations: {e}")
        raise
