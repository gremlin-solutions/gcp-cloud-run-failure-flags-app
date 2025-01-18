# Deploying a Flask App and the Gremlin Sidecar on Cloud Foundry

## 1. Download and Extract the Gremlin Sidecar Binary

1. **Pull** the sidecar image (adjust for your architecture if necessary):
   ```bash
   # Default (pulls the appropriate image for your platform if available)
   docker pull gremlin/failure-flags-sidecar:latest

   # Alternatively, specify architecture:
   docker pull --platform=linux/amd64 gremlin/failure-flags-sidecar:latest
   docker pull --platform=linux/arm64 gremlin/failure-flags-sidecar:latest
   ```

2. **Create** a temporary container:
   ```bash
   docker create --name failure-flags-extract gremlin/failure-flags-sidecar:latest
   ```

3. **Copy** the sidecar binary from the container:
   ```bash
   docker cp failure-flags-extract:/failure-flags-sidecar failure-flags-sidecar
   ```

4. **Remove** the container and **make the binary executable**:
   ```bash
   docker rm failure-flags-extract
   chmod +x failure-flags-sidecar
   ```

## 2. Configure `pcf-manifest.yml`

Below is an example `pcf-manifest.yml` for deploying your Flask app with the Python buildpack, plus the Gremlin sidecar. Adjust memory, paths, and environment variables as needed:

```yaml
---
applications:
  - name: s3-failure-flags-app            # App name in CF
    memory: 512M                          # Memory for the container
    disk_quota: 1G                        # Disk space for the container
    instances: 1                          # Number of instances

    buildpacks:
      - python_buildpack                  # Use Python buildpack for Flask

    path: .                               # Push contents of current directory

    command: null                         # Let the buildpack detect and use your Procfile

    env:
      S3_BUCKET: "commoncrawl"            # Custom environment variables
      DEBUG_MODE: "false"
      CLOUD: "pcf"
      AWS_ACCESS_KEY_ID: ((aws_access_key_id))
      AWS_SECRET_ACCESS_KEY: ((aws_secret_access_key))
      FAILURE_FLAGS_ENABLED: "true"
      GREMLIN_SIDECAR_ENABLED: "true"
      GREMLIN_TEAM_ID: ((gremlin_team_id))
      GREMLIN_TEAM_CERTIFICATE: ((gremlin_team_certificate))
      GREMLIN_TEAM_PRIVATE_KEY: ((gremlin_team_private_key))
      GREMLIN_DEBUG: "true"
      SERVICE_NAME: "s3-failure-flags-app"

    sidecars:
      - name: gremlin-sidecar
        process_types: ["web"]            # Attach sidecar to 'web' process
        memory: 256M
        disk_quota: 256M
        command: "./failure-flags-sidecar"  # Run Gremlin sidecar
```

## 3. Push to Cloud Foundry

From your project directory:
```bash
cf push -f pcf-manifest.yml
```

- The Python buildpack installs dependencies (from `requirements.txt`: `flask`, `boto3`, `requests`, `failureflags`).
- Both the Flask app and the Gremlin sidecar run in the same container, allowing local communication (`localhost:5032`).

