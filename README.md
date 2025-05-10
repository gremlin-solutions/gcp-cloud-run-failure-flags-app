# Deploy to Google Cloud Run

This guide covers deploying the **S3 Failure Flags App** to **Google Cloud Run**, including setup and integration with Gremlin Failure Flags.

## Prerequisites

Ensure you have the following configured:

* **Google Cloud CLI (`gcloud`)** installed
* Access to **Google Cloud Secret Manager**
* A Google Cloud Project with billing enabled
* Docker image hosted in a container registry

## Setting up Google Secret Manager

### 1. Create Secrets

Execute the following commands to create secrets for Gremlin and AWS credentials:

```bash
gcloud secrets create gremlin-team-id --replication-policy="automatic"
gcloud secrets create gremlin-team-certificate --replication-policy="automatic"
gcloud secrets create gremlin-team-private-key --replication-policy="automatic"
gcloud secrets create aws-access-key-id --replication-policy="automatic"
gcloud secrets create aws-secret-access-key --replication-policy="automatic"
```

### 2. Store Secret Values

Replace placeholders below with your actual credentials and file paths:

```bash
echo -n "<YOUR_GREMLIN_TEAM_ID>" | gcloud secrets versions add gremlin-team-id --data-file=-
gcloud secrets versions add gremlin-team-certificate --data-file="path/to/cert.pem"
gcloud secrets versions add gremlin-team-private-key --data-file="path/to/key.pem"
echo -n "<YOUR_AWS_ACCESS_KEY_ID>" | gcloud secrets versions add aws-access-key-id --data-file=-
echo -n "<YOUR_AWS_SECRET_ACCESS_KEY>" | gcloud secrets versions add aws-secret-access-key --data-file=-
```

* Replace `<YOUR_GREMLIN_TEAM_ID>` with your Gremlin Team ID.
* Replace `path/to/cert.pem` and `path/to/key.pem` with your certificate and private key file paths.
* Replace AWS placeholders with your AWS credentials.

### 3. Grant Permissions to Secrets

Grant the Cloud Run service account permission to access these secrets:

```bash
SERVICE_ACCOUNT="<PROJECT_NUMBER>-compute@developer.gserviceaccount.com"  # Replace <PROJECT_NUMBER> appropriately

for SECRET in gremlin-team-id gremlin-team-certificate gremlin-team-private-key aws-access-key-id aws-secret-access-key; do
  gcloud secrets add-iam-policy-binding "$SECRET" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Deploying the Application

### 1. Create Cloud Run YAML Configuration

Example `cloudrun-service.yaml`:

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: 's3-failure-flags-app'
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: '1'
        run.googleapis.com/execution-environment: 'gen1'
    spec:
      containers:
        - name: 'app-container'
          image: '<YOUR_DOCKER_REPO>/s3-failure-flags-app:latest'
          ports:
            - containerPort: 8080
          env:
            - name: S3_BUCKET
              value: 'commoncrawl'
            - name: AWS_REGION
              value: 'us-east-1'
            - name: CLOUD
              value: 'gcp'
            - name: FAILURE_FLAGS_ENABLED
              value: 'true'
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-access-key-id
                  key: latest
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-secret-access-key
                  key: latest
        - name: failure-flags-sidecar
          image: gremlin/failure-flags-sidecar:latest
          env:
            - name: GREMLIN_SIDECAR_ENABLED
              value: 'true'
            - name: GREMLIN_TEAM_ID
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-id
                  key: latest
            - name: GREMLIN_TEAM_CERTIFICATE
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-certificate
                  key: latest
            - name: GREMLIN_TEAM_PRIVATE_KEY
              valueFrom:
                secretKeyRef:
                  name: gremlin-team-private-key
                  key: latest
            - name: GREMLIN_DEBUG
              value: 'true'
            - name: SERVICE_NAME
              value: 's3-failure-flags-app'
```

Replace `<YOUR_DOCKER_REPO>` with your Docker repository.

### 2. Deploy Service to Cloud Run

Apply the configuration using:

```bash
gcloud run services replace cloudrun-service.yaml
```

### 3. Verify Deployment

Check deployment status:

```bash
gcloud run services describe s3-failure-flags-app --format="yaml(status.conditions)"
```

## Monitoring and Logs

### View Logs

Retrieve recent logs:

```bash
gcloud logging read 'resource.labels.service_name="s3-failure-flags-app"' --limit=100 --freshness=2m
```

### Tail Logs

Tail logs continuously:

```bash
while true; do
  gcloud logging read \
    'resource.labels.service_name="s3-failure-flags-app" AND labels.container_name="failure-flags-sidecar"' \
    --freshness=2m \
    --limit=100 \
    --format="table(timestamp, severity, textPayload)"
  sleep 5
done
```

## Grant Public Access

To allow public access (optional):

```bash
gcloud run services add-iam-policy-binding s3-failure-flags-app \
  --region=<YOUR_REGION> \
  --member="allUsers" \
  --role="roles/run.invoker"
```

Replace `<YOUR_REGION>` with your Cloud Run deployment region.

**Note**: Public access exposes your service to anyone with the URL.

## Reference Links

* [Google Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
* [Cloud Run YAML Deployment](https://cloud.google.com/run/docs/deploying#yaml)
* [Managing Secrets on Cloud Run](https://cloud.google.com/run/docs/configuring/secrets)
* [Gremlin Documentation](https://www.gremlin.com/docs/)

