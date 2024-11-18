# S3 Failure Flags App

This application demonstrates fault injection using Gremlin Failure Flags in a Flask-based S3 file lister.

## Features

- Lists the contents of an S3 bucket.
- Simulates faults such as:
  - AWS S3 exceptions (`NoCredentialsError`, `ClientError`, `EndpointConnectionError`).
  - Configurable latency-based failures using Gremlin's latency effect.
- Configurable via environment variables.
- Includes integration with the Gremlin Failure Flags Sidecar for advanced chaos engineering experiments.

## Prerequisites

- Python 3.9+
- Docker
- Kubernetes
- AWS credentials configured to access the target S3 bucket.
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

3. **Set the required environment variables:**

   ```bash
   export S3_BUCKET=<YOUR_S3_BUCKET_NAME>
   export FAILURE_FLAGS_ENABLED=true
   ```

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
   docker run -e S3_BUCKET=<YOUR_S3_BUCKET_NAME> -e FAILURE_FLAGS_ENABLED=true -p 8080:8080 <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
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

Replace `<BASE64_ENCODED_TEAM_ID>` and `<BASE64_ENCODED_TEAM_SECRET>` with your Base64-encoded team ID and shared secret. Use the following command to generate Base64-encoded values:

```bash
echo -n "your_value_here" | base64
```

Apply the secret to your cluster:

```bash
kubectl apply -f gremlin-team-secret.yaml
```

### 2. Update Deployment with the Sidecar

Update your `deployment.yaml` to include the Gremlin Sidecar. Below are examples for both authentication methods.

#### Example Deployment with Certificates

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
            - name: FAILURE_FLAGS_ENABLED
              value: "true"
            - name: S3_BUCKET
              value: "<YOUR_S3_BUCKET_NAME>"
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

#### Example Deployment with Shared Secret

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
            - name: FAILURE_FLAGS_ENABLED
              value: "true"
            - name: S3_BUCKET
              value: "<YOUR_S3_BUCKET_NAME>"
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
                  key: GREMLIN_TEAM_ID
            - name: GREMLIN_TEAM_SECRET
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-secret
                  key: GREMLIN_TEAM_SECRET
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

### Note on Exception Types

- To inject built-in exceptions like `ValueError`, specify the `exception` as a string.
- To inject custom exceptions, specify the `exception` as an object with `module`, `className`, and `message`.

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

**Explanation**: Injecting `NoCredentialsError` simulates a scenario where the application lacks the necessary AWS credentials to access the S3 bucket. This can occur in real life if credentials are misconfigured, expired, or not provided at all. Testing this helps ensure your application gracefully handles authentication failures and provides meaningful error messages to users.

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

**Explanation**: Injecting `ClientError` simulates an error response from the AWS S3 service, such as invalid parameters, access denied, or resource not found. This is useful for testing how your application handles various AWS service errors, ensuring robust error handling and improving resilience against issues like permission changes or resource unavailability.

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

**Explanation**: Injecting `EndpointConnectionError` simulates a network blackhole by causing the application to experience a connection failure when attempting to reach the S3 endpoint. This mimics real-world network issues such as outages, DNS failures, or misconfigured endpoints, allowing you to test your application's ability to handle network disruptions gracefully.

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

**Explanation**: Injecting a `ValueError` simulates an application-level error, such as invalid data processing or unexpected input values. This helps test your application's error-handling mechanisms for internal logic errors, ensuring that such exceptions are caught and managed appropriately without causing crashes or undefined behavior.

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

**Explanation**: The latency effect introduces a delay of 5 seconds (`5000 ms`), simulating network latency or processing delays. This allows you to test how your application behaves under slow network conditions, helping you identify performance bottlenecks and improve user experience during high-latency scenarios.

---

## License

This project is licensed under the Apache License 2.0. See the [`LICENSE`](LICENSE) file for details.
