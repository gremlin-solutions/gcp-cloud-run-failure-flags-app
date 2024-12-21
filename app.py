import os
import boto3
import botocore
import requests
import logging
from flask import Flask, jsonify, render_template
from failureflags import FailureFlag  # Import the FailureFlags SDK for fault injection

# Configure logging
# Logs will include timestamps, log levels, and messages for easier debugging.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Environment Variables
# Configure S3 bucket, debug mode, and application port via environment variables.
S3_BUCKET = os.getenv("S3_BUCKET", "commoncrawl")  # Default to "commoncrawl" if not set
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"  # Enable debug mode if "true"
PORT = int(os.getenv("PORT", 8080))  # Default to port 8080

# Initialize Flask App
# Flask is used to create the API endpoints.
app = Flask(__name__)

@app.route("/healthz", methods=["GET"])
def health_check():
    """
    Health check endpoint for Kubernetes liveness probes.
    Dynamically retrieves the region and availability zone from AWS Instance Metadata Service (IMDSv2).
    Includes fault injection capabilities via FailureFlags.
    """
    try:
        # Step 1: Obtain a session token for the AWS metadata service (IMDSv2)
        token_response = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},  # Token valid for 6 hours
            timeout=2
        )
        token_response.raise_for_status()  # Raise an error if the token request fails
        token = token_response.text

        # Step 2: Retrieve the availability zone using the metadata token
        az_response = requests.get(
            "http://169.254.169.254/latest/meta-data/placement/availability-zone",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=2
        )
        az_response.raise_for_status()  # Raise an error if the metadata request fails
        az = az_response.text

        # Step 3: Derive the region from the availability zone (e.g., "us-east-1a" -> "us-east-1")
        region = az[:-1]
    except Exception as e:
        # Log errors and default to "unknown" if metadata retrieval fails
        logger.error(f"Failed to retrieve region or availability zone: {e}")
        az = "unknown"
        region = "unknown"

    # Create the FailureFlag for the health check route
    failure_flag = FailureFlag(
        name="health_check_request",
        labels={
            "path": "/healthz",
            "region": region,
            "availability_zone": az
        },
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()  # Trigger fault injection if applicable

    logger.info(f"[HealthCheck] Region: {region}, AZ: {az}, Active: {active}, Impacted: {impacted}, Experiments: {experiments}")
    return jsonify({
        "status": "healthy",
        "region": region,
        "availability_zone": az,
        "isActive": active,
        "isImpacted": impacted
    }), 200

@app.route("/readiness", methods=["GET"])
def readiness_check():
    """
    Readiness check endpoint for Kubernetes readiness probes.
    Includes fault injection capabilities via FailureFlags.
    """
    failure_flag = FailureFlag(
        name="readiness_check_request",
        labels={"path": "/readiness"},
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()

    logger.info(f"[ReadinessCheck] Active: {active}, Impacted: {impacted}, Experiments: {experiments}")
    return jsonify({"status": "ready", "isActive": active, "isImpacted": impacted}), 200

@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    """
    Lists objects in the specified S3 bucket path.
    Includes fault injection for testing scenarios.
    """
    failure_flag = FailureFlag(
        name="list_s3_bucket_request",
        labels={"path": f"/{path}" if path else "/"},
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()

    logger.info(f"[ListS3Contents] Active: {active}, Impacted: {impacted}, Experiments: {experiments}")

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
    # Run the Flask application
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)

