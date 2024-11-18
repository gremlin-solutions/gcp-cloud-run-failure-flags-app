import os
import boto3
from flask import Flask, render_template, jsonify
from failureflags import FailureFlag
import logging
from botocore.exceptions import NoCredentialsError, ClientError, EndpointConnectionError

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

@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    """
    List the top-level contents of the specified S3 bucket path.
    """
    # Create a FailureFlag for the given path
    failure_flag = FailureFlag(
        name="list_s3_bucket",
        labels={"service": "s3", "operation": "list_bucket", "path": path},
        debug=True  # Use default behavior
    )

    # Invoke the failure flag
    active, impacted, experiments = failure_flag.invoke()

    # Proceed with normal execution; default behavior handles exceptions and latency
    try:
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=path, Delimiter='/')

        # Directories and files at the current path
        directories = response.get("CommonPrefixes", [])
        files = response.get("Contents", [])

        # Combine directories and files into a single list
        items = []
        for directory in directories:
            items.append({"Key": directory["Prefix"], "Size": "Directory"})
        for file in files:
            items.append({"Key": file["Key"], "Size": f"{file['Size']} bytes"})

        return render_template("index.html", bucket=S3_BUCKET, path=path, objects=items)
    except s3_client.exceptions.NoSuchBucket as e:
        logger.error(f"Bucket not found: {e}")
        return jsonify({"error": "Bucket not found"}), 404
    except NoCredentialsError as e:
        logger.error(f"NoCredentialsError: {e}")
        return jsonify({"error": "No credentials error"}), 401
    except EndpointConnectionError as e:
        logger.error(f"EndpointConnectionError: {e}")
        return jsonify({"error": "Unable to connect to the endpoint"}), 503
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"ClientError occurred: {error_code} - {error_message}")
        return jsonify({"error": f"Client error: {error_message}"}), 400
    except Exception as e:
        logger.error(f"Error listing bucket contents: {e}")
        return jsonify({"error": "Failed to list bucket contents"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

