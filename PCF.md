# Deploying Flask App and Gremlin Sidecar on Cloud Foundry

## 1. (Optional) Extract the Gremlin Sidecar Binary

1. **Pull** the sidecar image:
   ```bash
   docker pull gremlin/failure-flags-sidecar:latest
   ```
2. **Create** a temporary container:
   ```bash
   docker create --name failure-flags-extract gremlin/failure-flags-sidecar:latest
   ```
3. **Copy** the sidecar binary:
   ```bash
   docker cp failure-flags-extract:/failure-flags-sidecar failure-flags-sidecar
   ```
4. **Remove** the container and **make executable**:
   ```bash
   docker rm failure-flags-extract
   chmod +x failure-flags-sidecar
   ```

## 2. Use `pcf-manifest.yml` with Comments

Below is an example `pcf-manifest.yml` referencing the Python buildpack and Gremlin sidecar. Adjust it as needed, then run `cf push -f pcf-manifest.yml`.

```yaml
applications:
  - name: s3-failure-flags-app            # App name in CF
    memory: 512M                          # Memory for the container
    disk_quota: 1G                        # Disk space for the container
    instances: 1                          # Number of instances

    buildpacks:
      - python_buildpack                  # Use Python buildpack for Flask

    path: .                                # Push contents of current directory

    command: python app.py                # Launch the Flask app

    env:
      S3_BUCKET: "commoncrawl"            # Custom environment variables
      DEBUG_MODE: "false"
      CLOUD: "pcf"
      PORT: "8080"
      AWS_ACCESS_KEY_ID: ((aws_access_key_id))
      AWS_SECRET_ACCESS_KEY: ((aws_secret_access_key))

    sidecars:
      - name: gremlin-sidecar
        process_types: ["web"]            # Attach sidecar to 'web' process
        memory: 256M
        disk_quota: 256M
        command: "./failure-flags-sidecar"  # Run Gremlin sidecar

        env:
          GREMLIN_SIDECAR_ENABLED: "true"
          GREMLIN_SIDECAR_PORT: 5032
          GREMLIN_TEAM_ID: ((gremlin_team_id))
          GREMLIN_TEAM_CERTIFICATE: ((gremlin_team_certificate))
          GREMLIN_TEAM_PRIVATE_KEY: ((gremlin_team_private_key))
          GREMLIN_DEBUG: "true"
          SERVICE_NAME: "s3-failure-flags-app"
```

## 3. Push to Cloud Foundry

1. **Deploy**:
   ```bash
   cf push -f pcf-manifest.yml
   ```
   This installs dependencies (from `requirements.txt`: `flask`, `boto3`, `requests`, `failureflags`) using the Python buildpack and runs both the Flask app and Gremlin sidecar in one container.
```

