# S3 Failure Flags App

This application demonstrates fault injection using Gremlin Failure Flags in a Flask-based S3 file lister.

## Features

- **List S3 Bucket Contents:** Displays the contents of a specified S3 bucket.
- **Configurable Settings:** Customize the target S3 bucket via environment variables.
- **Gremlin Integration:** Integrates with the Gremlin Failure Flags Sidecar for chaos engineering experiments.
- **Fault Injection Capabilities:**
  - **Exception Injection:** Simulate application and AWS S3 exceptions.
  - **Latency Injection:** Introduce network delays.
  - **Response Modification:** Corrupt responses from external services.
- **Custom Behaviors:** Supports advanced fault injection scenarios with proper behavior chain maintenance.

## Prerequisites

- **Software:**
  - Python 3.9+
  - Docker
  - Kubernetes
- **Accounts & Credentials:**
  - AWS credentials configured for accessing the target S3 bucket (not required for the public `commoncrawl` bucket).
  - A Gremlin account with Failure Flags enabled.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone git@github.com:jsabo/s3-failure-flags-app.git
cd s3-failure-flags-app
```

### 2. Local Development

#### a. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### b. Install Dependencies

```bash
pip install -r requirements.txt
```

#### c. Configure Environment Variables

```bash
export S3_BUCKET=commoncrawl
export FAILURE_FLAGS_ENABLED=true
```

**Environment Variables:**

- `S3_BUCKET`: Name of the S3 bucket to access (default: `commoncrawl`).
- `FAILURE_FLAGS_ENABLED`: Enable fault injection functionality (`true`).

**Note:** The `commoncrawl` bucket is publicly accessible and does not require AWS credentials.

#### d. Run the Application

```bash
python app.py
```

#### e. Access the Application

Open your browser and navigate to:

```
http://127.0.0.1:8080
```

#### f. Deactivate the Virtual Environment

```bash
deactivate
```

### 3. Docker Build and Push

#### a. Build the Docker Image

```bash
docker build --platform linux/amd64 -t <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest .
```

Replace `<YOUR_DOCKER_REPO>` with your Docker repository path.

#### b. Push the Docker Image to Your Repository

```bash
docker push <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
```

**Security Note:** Ensure your Docker repository is secure and access is restricted to authorized personnel.

---

## Deploying to Kubernetes with Gremlin Sidecar

Integrate Gremlin Failure Flags by adding the **Gremlin Sidecar** to your Kubernetes deployment using certificate-based authentication.

### 1. Create a Secret for Gremlin Credentials

#### a. Download Gremlin Certificate Files

Download the following certificate files from your Gremlin team's configuration:

- **Team ID**
- **Team Certificate (`team-name.pub_cert.pem`)**
- **Team Private Key (`team-name.priv_key.pem`)**

Assume the files are downloaded to `~/Downloads/`:

- `~/Downloads/team-name.pub_cert.pem`
- `~/Downloads/team-name.priv_key.pem`

#### b. Base64 Encode the Credentials

Run the following commands to base64 encode your credentials in a portable manner compatible with both Linux and macOS:

```bash
# Replace with your actual Team ID
TEAM_ID="team-name"
BASE64_TEAM_ID=$(echo -n "$TEAM_ID" | base64)

# Encode the Team Certificate
BASE64_CERT=$(cat ~/Downloads/team-name.pub_cert.pem | base64 | tr -d '\n')

# Encode the Team Private Key
BASE64_PRIV_KEY=$(cat ~/Downloads/team-name.priv_key.pem | base64 | tr -d '\n')
```

**Explanation:**

- `echo -n "$TEAM_ID" | base64`: Encodes the Team ID without adding a newline.
- `cat file | base64 | tr -d '\n'`: Encodes the certificate and private key files and removes any newline characters to ensure the base64 string is on a single line.

#### c. Replace Placeholders in the Secret Template

1. **Create a Secret Template File (`gremlin-team-secret-template.yaml`):**

    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: gremlin-team-secret
    type: Opaque
    data:
      team_id: <BASE64_ENCODED_TEAM_ID>
      team_certificate: <BASE64_ENCODED_TEAM_CERTIFICATE>
      team_private_key: <BASE64_ENCODED_TEAM_PRIVATE_KEY>
    ```

2. **Replace Placeholders Using `sed`:**

    ```bash
    sed -e "s|<BASE64_ENCODED_TEAM_ID>|$BASE64_TEAM_ID|g" \
        -e "s|<BASE64_ENCODED_TEAM_CERTIFICATE>|$BASE64_CERT|g" \
        -e "s|<BASE64_ENCODED_TEAM_PRIVATE_KEY>|$BASE64_PRIV_KEY|g" \
        gremlin-team-secret-template.yaml > gremlin-team-secret.yaml
    ```

**Explanation:**

- The `sed` command replaces the placeholders `<BASE64_ENCODED_TEAM_ID>`, `<BASE64_ENCODED_TEAM_CERTIFICATE>`, and `<BASE64_ENCODED_TEAM_PRIVATE_KEY>` with the actual base64-encoded values.

#### d. Apply the Secret to Kubernetes

```bash
kubectl apply -f gremlin-team-secret.yaml
```

### 2. Update Deployment with the Sidecar

Modify your `deployment.yaml` to include the Gremlin Sidecar:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: s3-failure-flags-app
  labels:
    app: s3-failure-flags-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: s3-failure-flags-app
  template:
    metadata:
      labels:
        app: s3-failure-flags-app
    spec:
      containers:
        - name: app-container
          image: <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
          ports:
            - containerPort: 8080
          env:
            - name: S3_BUCKET
              value: "commoncrawl"
            - name: FAILURE_FLAGS_ENABLED
              value: "true"
        - name: gremlin-sidecar
          image: gremlin/failure-flags-sidecar:latest
          imagePullPolicy: Always
          env:
            - name: GREMLIN_SIDECAR_ENABLED
              value: "true"
            - name: GREMLIN_TEAM_ID
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-secret
                  key: team_id
            - name: GREMLIN_TEAM_CERTIFICATE
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-secret
                  key: team_certificate
            - name: GREMLIN_TEAM_PRIVATE_KEY
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-secret
                  key: team_private_key
            - name: GREMLIN_DEBUG
              value: "true"
            - name: SERVICE_NAME
              value: "s3-failure-flags-app"
            - name: REGION
              value: "us-east-1"
            - name: FAILURE_FLAGS_ENABLED
              value: "true"
```

**Notes:**

- Replace `<YOUR_DOCKER_REPO>` with your Docker repository path.
- Ensure environment variable keys in `secretKeyRef` match those in your Secret.
- **Required Environment Variables for Gremlin Sidecar:**
  - `GREMLIN_SIDECAR_ENABLED`
  - `GREMLIN_TEAM_ID`
  - `GREMLIN_TEAM_CERTIFICATE`
  - `GREMLIN_TEAM_PRIVATE_KEY`
  - `GREMLIN_DEBUG`
  - `SERVICE_NAME`
  - `REGION`
  - `FAILURE_FLAGS_ENABLED`

### 3. Apply the Deployment

Deploy your application and service to Kubernetes:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 4. Verify the Deployment

Ensure both containers are running:

```bash
kubectl get pods
```

Check Gremlin Sidecar logs:

```bash
kubectl logs <POD_NAME> -c gremlin-sidecar
```

*Replace `<POD_NAME>` with the actual name of your pod.*

### 5. Roll Out a New Docker Image

When you push a new image with the `latest` tag, ensure Kubernetes pulls the updated image by restarting the deployment:

```bash
docker build --platform linux/amd64 -t jsabo/s3-failure-flags-app:latest .
#docker build --platform linux/amd64 -t <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest .
docker push jsabo/s3-failure-flags-app:latest
#docker push <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
kubectl rollout restart deployment s3-failure-flags-app
```

### 6. Run Experiments

- **Log in to Gremlin UI.**
- **Navigate to:** `Failure Flags` → `Services`.
- **Select your application and start experiments.**

---

## Fault Injection Examples

Configure fault injection experiments using Gremlin's console, API, or CLI.

### 1. Inject a Built-in Exception (`ValueError`)

```json
{
  "name": "list_s3_bucket_value_error",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-value-error"
  },
  "rate": 1.0,
  "effect": {
    "exception": "This is a custom message"
  }
}
```

**Purpose:** Simulates an application-level `ValueError` to test exception handling.

### 2. Inject `CustomAppException`

```json
{
  "name": "list_s3_bucket_custom_exception",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-custom-exception"
  },
  "rate": 1.0,
  "effect": {
    "exception": "CustomAppException"
  }
}
```

**Purpose:** Simulates a custom application exception to test handling of application-specific errors.

### 3. Inject `NoCredentialsError`

```json
{
  "name": "list_s3_bucket_no_credentials",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-no-credentials"
  },
  "rate": 1.0,
  "effect": {
    "exception": {
      "message": "Simulated missing AWS credentials",
      "module": "botocore.exceptions",
      "className": "NoCredentialsError"
    }
  }
}
```

**Purpose:** Simulates missing AWS credentials to test authentication failure handling.

### 4. Inject `ClientError`

```json
{
  "name": "list_s3_bucket_client_error",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-client-error"
  },
  "rate": 1.0,
  "effect": {
    "exception": {
      "message": "Simulated S3 client error",
      "module": "botocore.exceptions",
      "className": "ClientError"
    }
  }
}
```

**Purpose:** Simulates an AWS service error to test handling of service exceptions.

### 5. Inject `EndpointConnectionError`

```json
{
  "name": "list_s3_bucket_blackhole",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-blackhole"
  },
  "rate": 1.0,
  "effect": {
    "exception": {
      "message": "Simulated endpoint connection error",
      "module": "botocore.exceptions",
      "className": "EndpointConnectionError"
    }
  }
}
```

**Purpose:** Simulates a network blackhole to test network failure handling.

### 6. Simulate Latency

```json
{
  "name": "list_s3_bucket_latency",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-latency"
  },
  "rate": 1.0,
  "effect": {
    "latency": {
      "ms": 5000
    }
  }
}
```

**Purpose:** Introduces a 5-second delay to simulate network latency or processing delays.

**Simulating a Network Blackhole:**

Set latency beyond your application's timeout settings (e.g., 60,000 ms) to simulate a blackhole.

```json
{
  "name": "list_s3_bucket_blackhole_latency",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-blackhole-latency"
  },
  "rate": 1.0,
  "effect": {
    "latency": {
      "ms": 60000
    }
  }
}
```

**Purpose:** Simulates a network blackhole by introducing a 60-second delay.

### 7. Modify Response Data

```json
{
  "name": "list_s3_bucket_data_corruption",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/simulate-data-corruption"
  },
  "rate": 1.0,
  "effect": {
    "modify_response": true
  }
}
```

**Purpose:** Corrupts the response data from the S3 client to test data validation and handling.

**Note on Response Validation**

The application validates all responses from external services to ensure robustness against unexpected or corrupted data. When injecting faults like modified responses using Gremlin Failure Flags, the application will handle them through its standard validation logic. This approach allows you to simulate real-world scenarios where external services might return invalid data.

---

## License

This project is licensed under the Apache License 2.0. See the [`LICENSE`](LICENSE) file for details.
