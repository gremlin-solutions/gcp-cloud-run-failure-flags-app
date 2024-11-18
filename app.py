import os
import boto3
from flask import Flask, render_template, jsonify
from failureflags import FailureFlag, defaultBehavior
import logging
from botocore.exceptions import NoCredentialsError, ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
S3_BUCKET = os.getenv('S3_BUCKET', 'default-bucket-name')
FAILURE_FLAGS_ENABLED = os.getenv('FAILURE_FLAGS_ENABLED', 'false').lower() == 'true'

# Initialize Flask App
app = Flask(__name__)

# Configure S3 Client
s3_client = boto3.client('s3')


# Define custom behavior
def custom_behavior(ff, experiments):
    """
    Custom behavior to handle specific failure cases.
    Simulates S3 boto exceptions.
    """
    for experiment in experiments:
        effect = experiment.get("effect", {})

        # Handle custom S3 boto exceptions
        if "exception" in effect:
            exception_type = effect["exception"].get("type", "ClientError")
            message = effect["exception"].get("message", "Injected S3 Exception")
            
            if exception_type == "NoCredentialsError":
                logger.error("Injecting NoCredentialsError")
                raise NoCredentialsError(message)
            elif exception_type == "ClientError":
                logger.error("Injecting ClientError")
                raise ClientError(
                    error_response={"Error": {"Code": "InjectedClientError", "Message": message}},
                    operation_name="ListObjectsV2",
                )
            else:
                logger.error(f"Unknown exception type: {exception_type}")
                raise Exception(message)

    return defaultBehavior(ff, experiments)


@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    """
    List the contents of the specified S3 bucket path.
    The FailureFlag is used to inject faults for the given path, including S3 boto exceptions.
    """
    # Create a FailureFlag for the given path
    failure_flag = FailureFlag(
        name="list_s3_bucket",
        labels={"service": "s3", "operation": "list_bucket", "path": path},
        debug=True,
        behavior=custom_behavior,
    )

    # Invoke the failure flag
    active, impacted, experiments = failure_flag.invoke()

    # Attempt to list objects in the specified path
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=path)
        objects = response.get("Contents", [])
        return render_template("index.html", bucket=S3_BUCKET, path=path, objects=objects)
    except s3_client.exceptions.NoSuchBucket as e:
        logger.error(f"Bucket not found: {e}")
        return jsonify({"error": "Bucket not found"}), 404
    except NoCredentialsError as e:
        logger.error(f"Injected NoCredentialsError: {e}")
        return jsonify({"error": "No credentials error"}), 401
    except ClientError as e:
        logger.error(f"Injected ClientError: {e}")
        return jsonify({"error": "S3 Client error"}), 400
    except Exception as e:
        logger.error(f"Error listing bucket contents: {e}")
        return jsonify({"error": "Failed to list bucket contents"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

