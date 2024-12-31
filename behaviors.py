import uuid
import logging
from random import random
from failureflags import delayedDataOrError

logger = logging.getLogger(__name__)

def simulate_http_response(ff, experiments):
    """
    Custom behavior to simulate HTTP status codes while chaining with default behaviors.
    """
    impacted = delayedDataOrError(ff, experiments)  # Process the default chain first

    for e in experiments:
        if "effect" in e and "httpStatus" in e["effect"]:
            http_status = e["effect"]["httpStatus"]

            # Extract values from the effect
            status_code = http_status.get("statusCode", 200)
            message = http_status.get("message", f"HTTP {status_code} simulated response")
            retry_after = http_status.get("retryAfter", None)
            request_id = str(uuid.uuid4())  # Generate a unique request ID

            # Create response structure
            response = {
                "status": status_code,
                "headers": {},
                "body": {"message": message}
            }

            # Customize for specific statuses
            if status_code == 429:  # Rate-limiting
                response["headers"]["x-amzn-RequestId"] = request_id
                response["headers"]["x-amz-retry-after"] = str(retry_after or 1)
                response["body"]["retryAfter"] = retry_after or 1
                response["body"]["requestId"] = request_id
                logger.info(f"Simulating AWS throttling: {status_code} Too Many Requests")

            elif status_code == 503:  # Service Unavailable
                response["headers"]["Retry-After"] = str(retry_after or 30)
                logger.info(f"Simulating Service Unavailable: {status_code}")

            logger.info(f"Simulated HTTP status: {status_code} with message: '{message}'")

            return response  # Exit after processing httpStatus effect

    return impacted  # Fallback to the default impact

