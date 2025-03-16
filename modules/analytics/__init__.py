"""Analytics module for processing and analyzing data."""

from modules.analytics.batch_analytics import (
    process_hourly_traffic_images,
    get_hourly_images,
    analyze_image_with_gemini_base64
)

from modules.analytics.scheduled_tasks import (
    schedule_tasks,
    shutdown_tasks
)

__all__ = [
    'process_hourly_traffic_images',
    'get_hourly_images',
    'analyze_image_with_gemini_base64',
    'schedule_tasks',
    'shutdown_tasks',
]
