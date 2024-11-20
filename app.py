import os
import boto3
import logging
from flask import Flask, render_template, jsonify, abort

# Import the FailureFlags SDK
# This SDK enables fault injection experiments to test application-level reliability.
from failureflags import FailureFlag

# Import specific exceptions for error handling with AWS S3
from botocore.exceptions import NoCredentialsError, ClientError, EndpointConnectionError

# Configure logging
# Set the logging level to INFO to log runtime information and fault injection details.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
# Retrieve the S3 bucket name from the environment or use a default value.
S3_BUCKET = os.getenv("S3_BUCKET", "commoncrawl")

# Configure Flask application settings using environment variables.
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
PORT = int(os.getenv("PORT", 8080))

# Initialize Flask App
# This Flask application will serve as the API endpoint for liveness checks, readiness checks, and S3 operations.
app = Flask(__name__)


@app.route("/healthz", methods=["GET"])
def health_check():
    """
    Health check endpoint for Kubernetes liveness probes and external monitoring.
    Uses FailureFlags to simulate fault injection and validate service resilience.
    """
    try:
        # Create and invoke a FailureFlag for the health check operation.
        # - Name: Uniquely identifies this fault injection point.
        # - Labels: Metadata for targeting experiments in the monitoring service.
        # - Debug: Enables detailed logging for fault injection experiments.
        failure_flag = FailureFlag(
            name="health_check_request",
            labels={"service": "monitoring", "operation": "liveness_check"},
            debug=True
        )
        active, impacted, experiments = failure_flag.invoke()

        # Log details of active experiments and their impact, if any.
        if active:
            logger.info(f"Active experiments for health check: {experiments}")
        if impacted:
            logger.warning("Health check impacted by fault injection")

        # Return a success response indicating the service is healthy.
        return jsonify({"status": "healthy", "isActive": active, "isImpacted": impacted}), 200

    except Exception as e:
        # Log the error and return an unhealthy response with a 500 status code.
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/readiness", methods=["GET"])
def readiness_check():
    """
    Readiness check endpoint for Kubernetes readiness probes.
    Simulates fault injection using FailureFlags and returns appropriate HTTP status codes.
    """
    try:
        # Create and invoke a FailureFlag for the readiness check operation.
        # - Name: Uniquely identifies this fault injection point for readiness checks.
        # - Labels: Metadata to help target specific experiments for readiness checks.
        failure_flag = FailureFlag(
            name="readiness_check_request",
            labels={"service": "monitoring", "operation": "readiness_check"},
            debug=True
        )
        active, impacted, experiments = failure_flag.invoke()

        # Log fault injection details if active.
        if active:
            logger.info(f"Active experiments for readiness check: {experiments}")
        if impacted:
            logger.warning("Readiness check impacted by fault injection")

        # Return a success response indicating the service is ready.
        return jsonify({"status": "ready", "isActive": active, "isImpacted": impacted}), 200

    except Exception as e:
        # Log the error and return a "not ready" response with a 503 status code.
        logger.error(f"Readiness check failed: {e}")
        return jsonify({"status": "not ready", "error": str(e)}), 503


@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    """
    List the contents of the specified S3 bucket path.
    This route supports optional paths to list objects in specific S3 prefixes.
    Uses FailureFlags to inject faults and validate application resilience.
    """
    try:
        # Create and invoke a FailureFlag for the S3 listing operation.
        # - Name: Uniquely identifies this fault injection point for S3 operations.
        # - Labels: Metadata to help target specific experiments for S3 listing.
        failure_flag = FailureFlag(
            name="list_s3_bucket_request",
            labels={"service": "s3", "operation": "list_bucket", "path": path},
            debug=True
        )
        active, impacted, experiments = failure_flag.invoke()

        # Log details of active experiments and their impact, if any.
        if active:
            logger.info(f"Active experiments for S3 listing: {experiments}")
        if impacted:
            logger.warning("S3 listing impacted by fault injection")

        # Perform the S3 operation to list objects and directories under the given path.
        s3_client = boto3.client("s3")
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=path, Delimiter="/")

        # Validate the response format to ensure it is a dictionary.
        if not isinstance(response, dict):
            raise ValueError("Invalid response format from S3")

        # Simulate data corruption injected by fault experiments.
        if response.get("CorruptedData"):
            raise ValueError("Received simulated corrupted data")

        # Extract directories and files from the S3 response.
        directories = response.get("CommonPrefixes", [])
        files = response.get("Contents", [])

        # Handle the case where no objects or directories are found.
        if not directories and not files:
            logger.info(f"No objects found in the specified path: {path}")
            return render_template(
                "index.html",
                bucket=S3_BUCKET,
                path=path,
                objects=[],
                message="No objects found in this path."
            )

        # Combine directories and files into a single list for rendering in the HTML template.
        items = [{"Key": d.get("Prefix", "Unknown"), "Size": "Directory"} for d in directories] + \
                [{"Key": f.get("Key", "Unknown"), "Size": f"{f.get('Size', 'Unknown')} bytes"} for f in files]

        return render_template("index.html", bucket=S3_BUCKET, path=path, objects=items)

    # Handle specific S3 exceptions.
    except s3_client.exceptions.NoSuchBucket as e:
        logger.error(f"Bucket not found: {e}")
        abort(404, description="Bucket not found")

    # Handle AWS connection or credential errors.
    except (NoCredentialsError, EndpointConnectionError) as e:
        logger.error(f"AWS connection or credentials error: {e}")
        return jsonify({"error": "AWS connection or credentials error"}), 503

    # Handle generic client errors from AWS.
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"ClientError occurred: {error_code} - {error_message}")
        return jsonify({"error": f"Client error: {error_message}"}), 400

    # Handle validation errors or data corruption.
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({"error": str(e)}), 500

    # Handle unexpected exceptions and log the error.
    except Exception as e:
        logger.error(f"Error listing bucket contents: {e}")
        return jsonify({"error": "Failed to list bucket contents"}), 500


# Start the Flask application
if __name__ == "__main__":
    # Run the Flask application on the specified port and debug mode.
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)

