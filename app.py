import os
import boto3
import logging
from flask import Flask, jsonify, render_template

# Import the FailureFlags SDK
from failureflags import FailureFlag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment Variables
S3_BUCKET = os.getenv("S3_BUCKET", "commoncrawl")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
PORT = int(os.getenv("PORT", 8080))

# Initialize Flask App
app = Flask(__name__)

@app.route("/healthz", methods=["GET"])
def health_check():
    failure_flag = FailureFlag(
        name="health_check_request",
        labels={"service": "monitoring", "operation": "liveness_check"},
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()
    return jsonify({"status": "healthy", "isActive": active, "isImpacted": impacted}), 200


@app.route("/readiness", methods=["GET"])
def readiness_check():
    failure_flag = FailureFlag(
        name="readiness_check_request",
        labels={"service": "monitoring", "operation": "readiness_check"},
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()
    return jsonify({"status": "ready", "isActive": active, "isImpacted": impacted}), 200


@app.route("/")
@app.route("/<path:path>")
def list_s3_contents(path=""):
    failure_flag = FailureFlag(
        name="list_s3_bucket_request",
        labels={"service": "s3", "operation": "list_bucket", "path": path},
        debug=True
    )
    active, impacted, experiments = failure_flag.invoke()

    s3_client = boto3.client("s3")
    response = s3_client.list_objects_v2(Bucket=S3_BUCKET, Prefix=path, Delimiter="/")

    if not isinstance(response, dict):
        raise ValueError("Invalid response format from S3")

    directories = response.get("CommonPrefixes", [])
    files = response.get("Contents", [])

    if not directories and not files:
        logger.info(f"No objects found in the specified path: {path}")
        return render_template(
            "index.html",
            bucket=S3_BUCKET,
            path=path,
            objects=[],
            message="No objects found in this path."
        )

    items = [{"Key": d.get("Prefix", "Unknown"), "Size": "Directory"} for d in directories] + \
            [{"Key": f.get("Key", "Unknown"), "Size": f"{f.get('Size', 'Unknown')} bytes"} for f in files]

    return render_template("index.html", bucket=S3_BUCKET, path=path, objects=items)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG_MODE)

