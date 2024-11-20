### PCF Manifest for the Deployment

To adapt the Kubernetes deployment to work in Pivotal Cloud Foundry (PCF) while preserving sidecar functionality, we use PCF's sidecar feature introduced in Cloud Foundry Application Runtime v3.

#### Manifest Example:

```yaml
---
applications:
  - name: s3-failure-flags-app
    memory: 1G
    disk_quota: 1G
    instances: 1
    docker:
      image: jsabo/s3-failure-flags-app:latest
    env:
      S3_BUCKET: "commoncrawl"
      FAILURE_FLAGS_ENABLED: "true"
    sidecars:
      - name: gremlin-sidecar
        command: null
        memory: 512M
        disk_quota: 512M
        docker:
          image: gremlin/failure-flags-sidecar:latest
        env:
          GREMLIN_SIDECAR_ENABLED: "true"
          GREMLIN_TEAM_ID: ((gremlin_team_id))
          GREMLIN_TEAM_CERTIFICATE: ((gremlin_team_certificate))
          GREMLIN_TEAM_PRIVATE_KEY: ((gremlin_team_private_key))
          GREMLIN_DEBUG: "true"
          SERVICE_NAME: "s3-failure-flags-app"
          REGION: "us-east-2"
```

### Key Details

1. **Application Configuration:**
   - The primary app container (`app-container`) is represented in the `docker` field of the `applications` section.
   - Environmental variables are provided, including the secrets.

2. **Sidecar:**
   - The sidecar is declared under the `sidecars` field.
   - It uses the Gremlin sidecar image with memory and disk quotas defined.
   - Environment variables for the sidecar match the original Kubernetes deployment.

3. **Secret Management:**
   - Secrets like `GREMLIN_TEAM_ID` are specified as placeholders `((...))`. These should be managed via the PCF CredHub or environment variables in your deployment pipeline.

### Steps to Deploy

1. Prepare the manifest file (`manifest.yml`) with the configuration provided above.
2. Deploy the application using the `cf push` command:
   ```bash
   cf push -f manifest.yml
   ```
3. Validate that the sidecar is running alongside the application:
   - Use `cf ssh` to inspect running processes.
   - Check logs to confirm both the main app and sidecar are operational.

### Additional Notes

- Ensure that the PCF environment supports sidecars (Cloud Foundry Application Runtime v3 or later).
- Manage secrets securely using CredHub or another secrets management solution integrated with PCF.
- Allocate sufficient memory and disk quotas to the application and sidecar to avoid resource contention.

### Reference

- https://github.com/cloudfoundry-samples/capi-sidecar-samples
- http://v3-apidocs.cloudfoundry.org/version/release-candidate/#sidecars
