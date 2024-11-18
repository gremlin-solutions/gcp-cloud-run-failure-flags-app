# S3 Failure Flags App

This application demonstrates fault injection using Gremlin Failure Flags in a Flask-based S3 file lister.

## Features

- Lists the contents of an S3 bucket.
- Configurable settings via environment variables:
  - **S3 Bucket Name**: Specify the target S3 bucket.
- Includes integration with the Gremlin Failure Flags Sidecar for chaos engineering experiments.
- Simulates faults using Gremlin Failure Flags:
  - **Exception injection**, such as:
    - Application-level exceptions (e.g., `ValueError`, **`CustomAppException`**).
    - AWS S3 exceptions (`NoCredentialsError`, `ClientError`, `EndpointConnectionError`).
  - **Latency injection** using Gremlin's latency effect.
  - **Response modification**: Simulate data corruption by modifying responses from external services.
- **Supports custom behaviors** with proper behavior chain maintenance, enabling advanced fault injection scenarios.

## Prerequisites

- Python 3.9+
- Docker
- Kubernetes
- AWS credentials configured to access the target S3 bucket (for `commoncrawl`, no credentials are needed for public access).
- A Gremlin account with Failure Flags enabled.

## Setup Instructions

### Clone the Repository

```bash
git clone git@github.com:jsabo/s3-failure-flags-app.git
cd s3-failure-flags-app
```

### Local Development

1. **Create and activate a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies in the virtual environment:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set the required environment variable:**

   ```bash
   export S3_BUCKET=commoncrawl
   ```

   **Environment Variable Explained:**

   - `S3_BUCKET`: Specifies the name of the S3 bucket to access. Default is `commoncrawl`, a publicly accessible bucket.

   **Note:** The `commoncrawl` bucket is a public bucket provided by [Common Crawl](https://commoncrawl.org/the-data/get-started/). It contains a vast repository of web crawl data that is publicly accessible.

4. **Run the application:**

   ```bash
   python app.py
   ```

5. **Open your browser and navigate to:**

   ```
   http://127.0.0.1:8080
   ```

6. **Deactivate the virtual environment when done:**

   ```bash
   deactivate
   ```

### Docker Build and Run

1. **Build the Docker image:**

   ```bash
   docker build -t <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -e S3_BUCKET=commoncrawl -p 8080:8080 <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
   ```

3. **Access the application at:**

   ```
   http://localhost:8080
   ```

4. **Push the image to a Docker repository (optional):**

   ```bash
   docker push <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
   ```

---

## Deploying to Kubernetes with Gremlin Sidecar

To integrate with Gremlin Failure Flags, add the **Gremlin Sidecar** to your Kubernetes deployment. You can authenticate the sidecar using either certificates or a shared secret.

### 1. Create a Secret for Gremlin Credentials

#### Method 1: Using Certificates

Create a Kubernetes secret for your Gremlin Team credentials (Certificates):

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

Replace `<BASE64_ENCODED_TEAM_ID>`, `<BASE64_ENCODED_TEAM_CERTIFICATE>`, and `<BASE64_ENCODED_TEAM_PRIVATE_KEY>` with your Base64-encoded credentials. Use the following command to generate Base64-encoded values:

```bash
echo -n "your_value_here" | base64
```

#### Method 2: Using Shared Secret

Create a Kubernetes secret for your Gremlin Team credentials (Shared Secret):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gremlin-team-secret
type: Opaque
data:
  GREMLIN_TEAM_ID: <BASE64_ENCODED_TEAM_ID>
  GREMLIN_TEAM_SECRET: <BASE64_ENCODED_TEAM_SECRET>
```

Replace `<BASE64_ENCODED_TEAM_ID>` and `<BASE64_ENCODED_TEAM_SECRET>` with your Base64-encoded team ID and shared secret.

Apply the secret to your cluster:

```bash
kubectl apply -f gremlin-team-secret.yaml
```

### 2. Update Deployment with the Sidecar

Update your `deployment.yaml` to include the Gremlin Sidecar. Below is an example:

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
```

### 3. Apply the Deployment

Deploy the updated configuration to Kubernetes:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 4. Verify the Deployment

Check that both the application container and the Gremlin Sidecar are running:

```bash
kubectl get pods
```

View the logs of the Gremlin Sidecar to ensure it is connected:

```bash
kubectl logs <POD_NAME> -c gremlin-sidecar
```

### 5. Run Experiments

- Log in to the **Gremlin UI**.
- Navigate to **Failure Flags** → **Services** to see your application.
- Start creating and running experiments.

---

## Fault Injection Examples

Use the Gremlin console, API, or CLI to configure fault injection experiments targeting the application.

### Note on Response Validation

- The application **validates** all responses from external services to ensure robustness against unexpected or corrupted data.
- When injecting faults like modified responses using Gremlin Failure Flags, the application will handle them through its standard validation logic.
- This approach allows you to simulate real-world scenarios where external services might return invalid data.

### Inject a Built-in Exception (`ValueError`) (Simulate Application Error)

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

**Explanation**: Simulates an application-level error by injecting a `ValueError`. This tests how your application handles internal exceptions.

### Inject `CustomAppException` (Simulate Custom Application Error)

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

**Explanation**: Simulates a custom application exception. Since `CustomAppException` is defined within the application code, a custom behavior is used to raise it. This tests the application's ability to handle application-specific errors.

### Inject `NoCredentialsError` (Simulate Missing AWS Credentials)

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

**Explanation**: Simulates missing AWS credentials to test authentication failure handling. Note that since the `commoncrawl` bucket is publicly accessible, this exception will not occur under normal circumstances unless explicitly injected.

### Inject `ClientError` (Simulate AWS Service Error)

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

**Explanation**: Simulates an AWS service error to test how your application handles service exceptions.

### Inject `EndpointConnectionError` (Simulate Network Blackhole)

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

**Explanation**: Simulates a network blackhole to test network failure handling.

### Simulate Latency (Simulate Network Delays)

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

**Explanation**: Introduces a 5-second delay to simulate network latency or processing delays.

### Modify Response Data (Simulate Data Corruption)

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

**Explanation**: Modifies the response data from the S3 client to simulate data corruption. The application will detect the corrupted data through its validation logic and handle it appropriately.

---

## License

This project is licensed under the Apache License 2.0. See the [`LICENSE`](LICENSE) file for details.
