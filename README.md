# S3 Failure Flags App

## Overview

The S3 Failure Flags App demonstrates fault injection using Gremlin Failure Flags in a Flask-based S3 file lister. It is designed to validate application resilience by simulating various fault scenarios, including network delays, application exceptions, and response modifications. This app is ideal for developers, DevOps engineers, and Site Reliability Engineers (SREs) testing cloud-native applications.

## Features

- **S3 Bucket Interaction:**

  - Lists and navigates the contents of an S3 bucket.
  - Supports both public and private buckets.

- **Fault Injection via Gremlin Failure Flags:**

  - Simulates latency, exceptions, network errors, and response modifications.
  - Combine multiple fault types for complex scenarios.

- **Kubernetes-Ready:**

  - Deploys with Gremlin Sidecar for seamless integration.
  - Includes health and readiness probes.

## Prerequisites

| Requirement         | Details                          |
| ------------------- | -------------------------------- |
| **Python**          | Version 3.9 or higher            |
| **Docker**          | Installed and configured         |
| **Kubernetes**      | Cluster with `kubectl` access    |
| **AWS Credentials** | For accessing private S3 buckets |
| **Gremlin Account** | With Failure Flags enabled       |

## Getting Started

### Clone the Repository

```bash
git clone git@github.com:jsabo/s3-failure-flags-app.git
cd s3-failure-flags-app
```

### Local Development

1. **Create and Activate Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Environment Variables:**

   ```bash
   export S3_BUCKET=commoncrawl
   export FAILURE_FLAGS_ENABLED=true
   ```

   | Variable                | Description                          | Default Value |
   | ----------------------- | ------------------------------------ | ------------- |
   | `S3_BUCKET`             | S3 bucket to access                  | `commoncrawl` |
   | `FAILURE_FLAGS_ENABLED` | Enable fault injection functionality | `true`        |

4. **Run the Application:**

   ```bash
   python app.py
   ```

5. **Access the Application:**

   Open your browser and navigate to:

   ```
   http://127.0.0.1:8080
   ```

### Docker Setup

1. **Build the Docker Image:**

   ```bash
   docker build --platform linux/amd64 -t <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest .
   ```

2. **Push to Docker Repository:**

   ```bash
   docker push <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
   ```

## Kubernetes Deployment

### Create Gremlin Secret

1. **Base64 Encode Credentials:**

   ```bash
   TEAM_ID="<YOUR_TEAM_ID>"
   BASE64_TEAM_ID=$(echo -n "$TEAM_ID" | base64)
   BASE64_CERT=$(cat path/to/cert.pem | base64 | tr -d '\n')
   BASE64_PRIV_KEY=$(cat path/to/key.pem | base64 | tr -d '\n')
   ```

2. **Update Secret Template:**

Replace placeholders in `gremlin-team-secret-template.yaml` and apply:

   ```bash
   sed -e "s|<BASE64_ENCODED_TEAM_ID>|$BASE64_TEAM_ID|g" \
       -e "s|<BASE64_ENCODED_TEAM_CERTIFICATE>|$BASE64_CERT|g" \
       -e "s|<BASE64_ENCODED_TEAM_PRIVATE_KEY>|$BASE64_PRIV_KEY|g" \
       gremlin-team-secret-template.yaml > gremlin-team-secret.yaml
   
   kubectl apply -f gremlin-team-secret.yaml
   ```

### Deploy Application

1. **Apply Kubernetes Resources:**

   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   kubectl apply -f ingress.yaml
   ```

2. **Verify Deployment:**

   ```bash
   kubectl get pods
   ```

## Fault Injection Examples

| Fault Type              | Name                                | Selector                                                        | Effect Example                                                                                                                                          |
| ----------------------- | ----------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Network Latency         | Simulate Latency                    | `{ "path": ["/latency-test"] }`                                 | `{ "latency": { "ms": 5000 } }`                                                                                                                         |
| Network Latency         | Inject Random Latency               | `{ "path": ["/simulate-jitter"] }`                              | `{ "latency": { "ms": 2000, "jitter": 500 } }`                                                                                                          |
| Application Error       | Inject Built-in Exception           | `{ "path": ["/inject-exception"] }`                             | `{ "exception": { "className": "ValueError", "message": "Injected ValueError", "module": "builtins" } }`                                                |
| Network Error           | Simulate Timeout on Socket          | `{ "path": ["/"] }`                                             | `{ "exception": { "className": "timeout", "message": "Socket operation timed out", "module": "socket" } }`                                              |
| Network Error           | Simulate Connection Error           | `{ "path": ["/simulate-blackhole"] }`                           | `{ "exception": { "className": "S3TransferFailedError", "message": "Simulated connection error during S3 transfer", "module": "boto3.exceptions" } }`   |
| Combined Faults         | Simulate Latency with Validation Error | `{ "path": ["/inject-latency-exception"] }`                    | `{ "latency": { "ms": 2000 }, "exception": { "className": "ValidationError", "message": "Simulated latency and validation error", "module": "botocore.exceptions" } }` |
| Application Error       | Inject Custom Application Exception | `{ "path": ["/inject-custom-exception"] }`                      | `{ "exception": { "className": "CustomAppException", "message": "Custom application exception", "module": "__main__" } }`                               |
| Data Integrity          | Simulate Corrupted Response Data    | `{ "path": ["/simulate-data-corruption"] }`                     | `{ "data": { "CorruptedData": true } }`                                                                                                                 |
| Availability Zone Fault | Simulate AZ-Specific Latency        | `{ "path": ["/liveness"], "availability_zone": ["us-east-1a"] }` | `{ "latency": { "ms": 60000 } }`                                                                                                                        |
| Region Fault            | Simulate Region-Specific Latency    | `{ "path": ["/liveness"], "region": ["us-east-1"] }`             | `{ "latency": { "ms": 60000 } }`                                                                                                                        |
| Service Degradation     | Simulate Readiness Probe Latency    | `{ "path": ["/readiness"] }`                                    | `{ "latency": { "ms": 60000 } }`                                                                                                                        |
| **Custom Behavior**: Modify HTTP Response | Simulate AWS Rate Limiting (429)    | `{ "path": ["/simulate-http-response"] }`                       | `{ "httpStatus": { "statusCode": 429, "message": "Too Many Requests", "retryAfter": 5 } }`                                                              |
| **Custom Behavior**: Modify HTTP Response | Simulate Service Unavailability (503) | `{ "path": ["/simulate-http-response"] }`                       | `{ "httpStatus": { "statusCode": 503, "message": "Service Unavailable", "retryAfter": 30 } }`                                                           |

## Troubleshooting

- **Application Logs:**

  ```bash
  kubectl logs -l app=s3-failure-flags-app -c app-container
  ```

- **Sidecar Logs:**

  ```bash
  kubectl logs -l app=s3-failure-flags-app -c gremlin-sidecar
  ```

- **Common Issues:**

  - Missing AWS credentials: Ensure `~/.aws/credentials` is configured.
  - Sidecar errors: Verify secret values are correctly encoded.

