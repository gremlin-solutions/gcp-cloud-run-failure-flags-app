# S3 Failure Flags App

This application demonstrates fault injection using Gremlin Failure Flags in a Flask-based S3 file lister.

## Features

- Lists the contents of an S3 bucket.
- Simulates faults such as:
  - AWS S3 exceptions (`NoCredentialsError`, `ClientError`).
  - Configurable latency-based failures using Gremlin's latency effect.
- Configurable via environment variables.

## Prerequisites

- Python 3.9+
- Docker
- Kubernetes
- AWS credentials configured to access the target S3 bucket.

## Setup Instructions

### Clone the Repository

```
git clone https://github.com/jsabo/s3-failure-flags-app.git
cd s3-failure-flags-app
```

### Local Development

1. Create and activate a virtual environment:

```
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies in the virtual environment:

```
pip install -r requirements.txt
```

3. Set the required environment variables:

```
export S3_BUCKET=your-bucket-name
export FAILURE_FLAGS_ENABLED=true
```

4. Run the application:

```
python app.py
```

5. Open your browser and navigate to:

```
http://127.0.0.1:5000
```

6. Deactivate the virtual environment when done:

```
deactivate
```

### Docker Build and Run

1. Build the Docker image:

```
docker build -t your-docker-repo/s3-failure-flags-app:latest .
```

2. Run the Docker container:

```
docker run -e S3_BUCKET=your-bucket-name -e FAILURE_FLAGS_ENABLED=true -p 5000:5000 your-docker-repo/s3-failure-flags-app:latest
```

3. Access the application at:

```
http://localhost:5000
```

4. Push the image to a Docker repository:

```
docker push your-docker-repo/s3-failure-flags-app:latest
```

### Kubernetes Deployment

1. Deploy the application to Kubernetes:

```
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

2. Find the external IP address of the service:

```
kubectl get services
```

3. Access the application at the external IP.

## Fault Injection Examples

Use the Gremlin console, API, or CLI to configure fault injection experiments targeting the application.

### Inject `NoCredentialsError`

```
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

```
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

### Simulate Blackhole Using Latency Effect

```
{
  "name": "list_s3_bucket_blackhole",
  "labels": {
    "service": "s3",
    "operation": "list_bucket",
    "path": "/blackhole"
  },
  "rate": 1.0,
  "effect": {
    "latency": {
      "ms": 3600000
    }
  }
}
```

**Explanation:** The latency effect introduces a delay of 1 hour (`3600000 ms`), effectively simulating a blackhole by making the application unresponsive.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

