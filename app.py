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
S3_BUCKET = os.getenv('S3_BUCKET', 'commoncrawl')

# Initialize Flask App
app = Flask(__name__)

# Configure S3 Client
s3_client = boto3.client('s3')

# Define a custom exception
class CustomAppException(Exception):
    """Custom exception for application-specific errors."""
    pass

# Custom behavior function
#def custom_behavior(failure_flag, experiments):
#    for experiment in experiments:
#        if 'modify_response' in experiment['effect']:
#            return {'CorruptedData': True}
#        elif 'exception' in experiment['effect'] and experiment['effect']['exception'] == 'CustomAppException':
#            raise CustomAppException("Simulated custom application exception")

def customBehavior(ff, experiments):
    logger.debug(experiments)
    return defaultBehavior(ff, experiments)

@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    """
    List the contents of the specified S3 bucket path.
    """
    # Create and invoke the FailureFlag
    failure_flag = FailureFlag(
        name="list_s3_bucket",
        labels={"path": path},
        behavior=custom_behavior,  # Use custom behavior
        debug=True
    )
    failure_flag.invoke()

    try:
        # Perform the S3 operation
        response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=path, Delimiter='/')

        # Validate the response
        if not isinstance(response, dict):
            raise ValueError("Invalid response format from S3")

        # Check for corrupted data
        if response.get('CorruptedData'):
            raise ValueError("Received corrupted data from S3")

        # Extract directories and files
        directories = response.get("CommonPrefixes", [])
        files = response.get("Contents", [])

        # Check if both directories and files are empty
        if not directories and not files:
            logger.info("No objects found in the specified path.")
            return render_template(
                "index.html",
                bucket=S3_BUCKET,
                path=path,
                objects=[],
                message="No objects found in this path."
            )

        # Combine directories and files into a single list
        items = []
        for directory in directories:
            items.append({"Key": directory.get("Prefix", "Unknown"), "Size": "Directory"})
        for file in files:
            items.append({"Key": file.get("Key", "Unknown"), "Size": f"{file.get('Size', 'Unknown')} bytes"})

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
    except CustomAppException as e:
        logger.error(f"CustomAppException: {e}")
        return jsonify({"error": str(e)}), 500
    except ValueError as e:
        logger.error(f"ValueError: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Error listing bucket contents: {e}")
        return jsonify({"error": "Failed to list bucket contents"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

