# S3 Failure Flags App

This application demonstrates fault injection using Gremlin Failure Flags in a Flask-based S3 file lister.

## Features

- Lists the contents of an S3 bucket.
- Simulates faults such as:
  - AWS S3 exceptions (`NoCredentialsError`, `ClientError`).
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

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies in the virtual environment:

   ```bash
   pip install -r requirements.txt
   ```

3. Set the required environment variables:

   ```bash
   export S3_BUCKET=<YOUR_S3_BUCKET_NAME>
   export FAILURE_FLAGS_ENABLED=true
   ```

4. Run the application:

   ```bash
   python app.py
   ```

5. Open your browser and navigate to:

   ```bash
   http://127.0.0.1:8080
   ```

6. Deactivate the virtual environment when done:

   ```bash
   deactivate
   ```

### Docker Build and Run

1. Build the Docker image:

   ```bash
   docker build -t <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest .
   ```

2. Run the Docker container:

   ```bash
   docker run -e S3_BUCKET=<YOUR_S3_BUCKET_NAME> -e FAILURE_FLAGS_ENABLED=true -p 8080:8080 <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
   ```

3. Access the application at:

   ```bash
   http://localhost:8080
   ```

4. Push the image to a Docker repository (optional):

   ```bash
   docker push <YOUR_DOCKER_REPO>/s3-failure-flags-app:latest
   ```

---

## Deploying to Kubernetes with Gremlin Sidecar

To integrate with Gremlin Failure Flags, add the **Gremlin Sidecar** to your Kubernetes deployment.

### 1. Create a Secret for Gremlin Credentials

Create a Kubernetes secret for your Gremlin Team credentials:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gremlin-team-secret
type: Opaque
data:
  team_id: <BASE64_ENCODED_TEAM_ID>
  team_certificate: <BASE64_ENCODED_TEAM_CERTIFICATE>
  team_private_key: <BASE64_ENCODED_PRIVATE_KEY>
```

Replace `<BASE64_ENCODED_TEAM_ID>`, `<BASE64_ENCODED_TEAM_CERTIFICATE>`, and `<BASE64_ENCODED_PRIVATE_KEY>` with your Base64-encoded credentials. Use the following command to generate Base64-encoded values:

```bash
echo -n "your_value_here" | base64
```

Apply the secret to your cluster:

```bash
kubectl apply -f gremlin-team-secret.yaml
```

### 2. Update Deployment with the Sidecar

Update your `deployment.yaml` to include the Gremlin Sidecar:

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

### Inject `NoCredentialsError`

```json
{
  "name": "list_s3_bucket_no_credentials",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/blue"
  },
  "rate": 1.0,
  "effect": {
    "exception": {
      "type": "NoCredentialsError",
      "message": "Simulated missing AWS credentials"
    }
  }
}
```

### Inject `ClientError`

```json
{
  "name": "list_s3_bucket_client_error",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/green"
  },
  "rate": 1.0,
  "effect": {
    "exception": {
      "type": "ClientError",
      "message": "Simulated S3 client error"
    }
  }
}
```

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
