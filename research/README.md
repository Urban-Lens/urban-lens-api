# YouTube Video Analysis with Vertex AI

This tool allows you to analyze YouTube videos using Google's Vertex AI Gemini model. The analysis provides insights about the content, topics, and key points of the video.

## Prerequisites

- Python 3.8 or higher
- Google Cloud account with Vertex AI API enabled
- Service account with appropriate permissions

## Installation

1. Install the required Python packages:

```bash
pip install google-cloud-aiplatform google-auth google-auth-oauthlib
```

## Authentication

The script uses a service account for authentication. The service account credentials are embedded in `setup_credentials.py` for convenience. In a production environment, you should use a more secure method to handle credentials.

### Enabling the Vertex AI API

Before using this script, you need to enable the Vertex AI API for your project:

1. Go to: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
2. Make sure you're in the correct project (personal-finance-app-430916)
3. Click 'Enable' to activate the Vertex AI API
4. Wait a few minutes for the activation to propagate

### Service Account Permissions

The service account needs the following roles:
- Vertex AI User
- Service Account User
- Storage Object Admin (if using Cloud Storage)

## Usage

### Simple Test Run

To run a quick test with a sample video:

```bash
python run_analysis.py
```

### Analyze a Specific YouTube Video

```bash
python youtube_streaming_analysis.py --url "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
```

Or run it interactively:

```bash
python youtube_streaming_analysis.py
```

## Troubleshooting

### API Not Enabled

If you see an error about the Vertex AI API not being enabled, follow the instructions in the "Enabling the Vertex AI API" section above.

### Authentication Issues

If you encounter authentication issues:

1. Check that your service account has the correct permissions
2. Verify that the credentials in `setup_credentials.py` are valid
3. Try authenticating with gcloud: `gcloud auth application-default login`

## License

This project is for educational and research purposes only. Use responsibly and respect YouTube's terms of service. 