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
- **Custom Behaviors:** Supports advanced fault injection scenarios.

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

## Fault Injection Examples

---

### **1. Simulate Latency**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/"] }
```

#### Effect:
```json
{
  "latency": {
    "ms": 5000
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Introduces a 5-second delay to simulate network or processing latency.

---

### **2. Inject Random Latency**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/simulate-jitter"] }
```

#### Effect:
```json
{
  "latency": {
    "ms": 2000,
    "jitter": 500
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates random latency between 2 and 2.5 seconds to mimic network jitter.

---

### **3. Inject a Built-in Exception (`ValueError`)**

#### Failure Flag Selector:
```json
{ "method": ["GET"], "path": ["/healthz"] }
```

#### Effect:
```json
{
  "exception": {
    "className": "ValueError",
    "message": "Injected ValueError",
    "module": "builtins"
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates a `ValueError` in the `/healthz` endpoint to test application-level exception handling.

---

### **4. Inject `NoCredentialsError`**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/"] }
```

#### Effect:
```json
{
  "exception": {
    "className": "NoCredentialsError",
    "message": "Simulated missing AWS credentials",
    "module": "botocore.exceptions"
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates missing AWS credentials for S3 operations, testing authentication failure handling.

---

### **5. Inject `ClientError`**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/sub-path"] }
```

#### Effect:
```json
{
  "exception": {
    "className": "ClientError",
    "message": "Simulated S3 client error",
    "module": "botocore.exceptions"
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates an AWS client error during S3 operations to validate error handling.

---

### **6. Combine Latency and Exception**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/sub-path"] }
```

#### Effect:
```json
{
  "latency": {
    "ms": 2000
  },
  "exception": {
    "className": "ClientError",
    "message": "Simulated latency and error",
    "module": "botocore.exceptions"
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates a delay followed by an AWS client error during S3 operations to validate error handling.

---

### **7. Inject `EndpointConnectionError`**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/simulate-blackhole"] }
```

#### Effect:
```json
{
  "exception": {
    "className": "EndpointConnectionError",
    "message": "Simulated endpoint connection error",
    "module": "botocore.exceptions"
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates a network blackhole by injecting an `EndpointConnectionError`.

---

### **8. Simulate a Network Blackhole**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/simulate-blackhole-latency"] }
```

#### Effect:
```json
{
  "latency": {
    "ms": 60000
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates a network blackhole by introducing a 60-second delay, testing timeout behaviors.

---

### **9. Modify Response Data**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/simulate-data-corruption"] }
```

#### Effect:
```json
{
  "data": {
    "CorruptedData": true
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Corrupts the response data returned by the S3 client to test data validation and handling.

---

### **10. Simulate a Custom Application Exception**

#### Failure Flag Selector:
```json
{ "service": "s3", "operation": "list_bucket", "path": ["/simulate-custom-exception"] }
```

#### Effect:
```json
{
  "exception": {
    "className": "CustomAppException",
    "message": "Simulated custom application exception",
    "module": "app.exceptions"
  }
}
```

#### Impact Probability:
Set to `100%` for consistent testing.

**Purpose:** Simulates a custom application-specific exception to test custom error handling.

