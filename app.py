import os
import boto3
import botocore
import requests
import logging
from flask import Flask, jsonify, render_template

from failureflags import FailureFlag  # Import the FailureFlags SDK for fault injection
from behaviors import simulate_http_response  # Import the custom behavior from behaviors.py

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Environment Variables
S3_BUCKET = os.getenv("S3_BUCKET", "commoncrawl")  # Default to "commoncrawl" if not set
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"  # Enable debug mode if "true"
PORT = int(os.getenv("PORT", 8080))  # Default to port 8080

# Initialize Flask App
app = Flask(__name__)

# Global variables for region and availability zone
REGION = "unknown"
AVAILABILITY_ZONE = "unknown"

# Custom Exception for Fault Injection
class CustomAppException(Exception):
    pass

def initialize_metadata():
    """
    Retrieve the region and availability zone using AWS Instance Metadata Service (IMDSv2) and store globally.
    """
    global REGION, AVAILABILITY_ZONE
    try:
        token_response = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},  # Token valid for 6 hours
            timeout=2
        )
        token_response.raise_for_status()
        token = token_response.text

        az_response = requests.get(
            "http://169.254.169.254/latest/meta-data/placement/availability-zone",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=2
        )
        az_response.raise_for_status()
        AVAILABILITY_ZONE = az_response.text
        REGION = AVAILABILITY_ZONE[:-1]  # Derive region by removing the last character
        logger.info(f"Metadata initialized: Region = {REGION}, Availability Zone = {AVAILABILITY_ZONE}")
    except Exception as e:
        logger.error(f"Failed to retrieve metadata: {e}")

@app.route("/healthz", methods=["GET"])
def health_check():
    """
    Health check endpoint for Kubernetes liveness probes.
    """
    failure_flag = FailureFlag(
        name="health_check_request",
        labels={
            "path": "/healthz",
            "region": REGION,
            "availability_zone": AVAILABILITY_ZONE
        },
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()

    logger.info(f"[HealthCheck] Region: {REGION}, AZ: {AVAILABILITY_ZONE}, Active: {active}, Impacted: {impacted}, Experiments: {experiments}")
    return jsonify({
        "status": "healthy",
        "region": REGION,
        "availability_zone": AVAILABILITY_ZONE,
        "isActive": active,
        "isImpacted": impacted
    }), 200

@app.route("/readiness", methods=["GET"])
def readiness_check():
    """
    Readiness check endpoint for Kubernetes readiness probes.
    """
    failure_flag = FailureFlag(
        name="readiness_check_request",
        labels={
            "path": "/readiness",
            "region": REGION,
            "availability_zone": AVAILABILITY_ZONE
        },
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()

    logger.info(f"[ReadinessCheck] Region: {REGION}, AZ: {AVAILABILITY_ZONE}, Active: {active}, Impacted: {impacted}, Experiments: {experiments}")
    return jsonify({
        "status": "ready",
        "region": REGION,
        "availability_zone": AVAILABILITY_ZONE,
        "isActive": active,
        "isImpacted": impacted
    }), 200

@app.route("/simulate-http-response", methods=["GET"])
def simulate_http_response_route():
    """
    Simulate various HTTP responses, including AWS throttling and other status codes.
    """
    failure_flag = FailureFlag(
        name="simulate_http_response_request",
        labels={
            "path": "/simulate-http-response",
            "region": REGION,
            "availability_zone": AVAILABILITY_ZONE
        },
        behavior=simulate_http_response,  # Use the custom behavior
        debug=True
    )

    # Invoke the failure flag
    active, impacted, experiments = failure_flag.invoke()

    # Default response values
    status = 200
    message = "Default behavior executed"
    headers = {}

    # Check if a custom response was generated
    if isinstance(impacted, dict):
        status = impacted.get("status", 200)
        message = impacted.get("body", {}).get("message", "Default behavior executed")
        headers = impacted.get("headers", {})

    # Log the simulated HTTP response
    logger.info(f"[SimulateHttpResponse] Region: {REGION}, AZ: {AVAILABILITY_ZONE}, Active: {active}, Impacted: {bool(impacted)}, Experiments: {experiments}")

    # Return a consistent response structure
    return jsonify({
        "status": status,
        "region": REGION,
        "availability_zone": AVAILABILITY_ZONE,
        "isActive": active,
        "isImpacted": bool(impacted),
        "message": message
    }), status, headers

@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    """
    Lists objects in the specified S3 bucket path.
    Includes fault injection for testing scenarios.
    """
    failure_flag = FailureFlag(
        name="list_s3_bucket_request",
        labels={
            "path": f"/{path}" if path else "/",
            "region": REGION,
            "availability_zone": AVAILABILITY_ZONE
        },
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()

    logger.info(f"[ListS3Contents] Region: {REGION}, AZ: {AVAILABILITY_ZONE}, Active: {active}, Impacted: {impacted}, Experiments: {experiments}")

    # Initialize the S3 client
    s3_client = boto3.client("s3")
    try:
        # Fetch the list of objects from the specified S3 bucket and path
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=path, Delimiter="/")
    except botocore.exceptions.BotoCoreError as e:
        logger.error(f"Error accessing S3 bucket '{S3_BUCKET}': {e}")
        return jsonify({"error": "Failed to access S3 bucket"}), 500

    # Parse directories and files from the S3 response
    directories = response.get("CommonPrefixes", [])
    files = response.get("Contents", [])

    if not directories and not files:
        # If no objects are found, render an empty response
        logger.info(f"No objects found in the specified path: {path}")
        return render_template(
            "index.html",
            bucket=S3_BUCKET,
            path=path,
            objects=[],
            message="No objects found in this path."
        )

    # Combine directories and files into a unified list for rendering
    items = [{"Key": d.get("Prefix", "Unknown"), "Size": "Directory"} for d in directories] + \
            [{"Key": f.get("Key", "Unknown"), "Size": f"{f.get('Size', 'Unknown')} bytes"} for f in files]

    return render_template("index.html", bucket=S3_BUCKET, path=path, objects=items)

if __name__ == "__main__":
    # Initialize metadata before starting the Flask application
    initialize_metadata()
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)

