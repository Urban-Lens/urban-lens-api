"""Command-line tools for analytics operations"""
import asyncio
import click
import logging
from datetime import datetime, timedelta

from database import get_db
from config.config import settings
from modules.analytics.batch_analytics import process_hourly_traffic_images

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@click.group()
def analytics():
    """Analytics operations command group"""
    pass

@analytics.command()
@click.option('--hours-ago', default=1, help='Process images from X hours ago')
@click.option('--api-key', default=None, help='Gemini API key (defaults to settings)')
@click.option('--prompt', default=None, help='Custom analysis prompt (defaults to standard prompt)')
async def analyze_traffic_images(hours_ago, api_key, prompt):
    """Process traffic images from a specific hour"""
    target_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=hours_ago)
    
    if not api_key:
        api_key = settings.GEMINI_API_KEY
    
    click.echo(f"Processing traffic images from {target_hour}")
    
    async for db in get_db():
        try:
            # Override the default prompt if a custom one is provided
            custom_params = {}
            if prompt:
                # Create a custom processing function with the custom prompt
                async def custom_processing(target_hour):
                    records = await get_hourly_images(db, target_hour)
                    
                    if not records:
                        return []
                    
                    results = []
                    for record in records:
                        analysis_result = analyze_image_with_gemini_base64(
                            record["output_img_path"], 
                            api_key, 
                            prompt
                        )
                        await store_analysis_results(db, record["id"], analysis_result)
                        record["analysis_result"] = analysis_result
                        results.append(record)
                    
                    return results
                
                results = await custom_processing(target_hour)
            else:
                results = await process_hourly_traffic_images(
                    db=db,
                    gemini_api_key=api_key,
                    target_hour=target_hour
                )
            
            click.echo(f"Successfully processed {len(results)} images")
            
            # Print analysis results
            for result in results:
                click.echo(f"Record ID: {result['id']}")
                click.echo(f"Source: {result['source_id']}")
                click.echo(f"Timestamp: {result['timestamp']}")
                click.echo("Analysis:")
                click.echo(result['analysis_result'])
                click.echo("-" * 50)
        
        except Exception as e:
            click.echo(f"Error processing images: {e}")
            logger.error(f"Error in analyze_traffic_images: {e}", exc_info=True)

if __name__ == "__main__":
    # Use this to run the CLI commands directly
    # This allows running: python -m cli.analytics_tools analyze-traffic-images
    loop = asyncio.get_event_loop()
    loop.run_until_complete(analytics()) 