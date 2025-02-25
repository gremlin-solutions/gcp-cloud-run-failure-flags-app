Replace the placeholders (such as the environmentId and secret values) with your actual settings.

```yaml
name: s3-failure-flags-app
location: eastus
properties:
  # The managed environment ID for your Container Apps environment
  environmentId: /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.App/managedEnvironments/<env-name>
  configuration:
    ingress:
      external: true
      targetPort: 8080
    secrets:
      # Define secrets for the Gremlin sidecar credentials
      - name: gremlin-team-id
        value: <team_id_value>
      - name: gremlin-team-certificate
        value: <team_certificate_value>
      - name: gremlin-team-private-key
        value: <team_private_key_value>
  template:
    # Set the scaling to exactly 4 replicas
    scale:
      minReplicas: 4
      maxReplicas: 4
    containers:
      - name: app-container
        image: jsabo/s3-failure-flags-app:latest
        resources:
          cpu: 0.5    # Adjust as needed
          memory: 1Gi # Adjust as needed
        env:
          - name: S3_BUCKET
            value: "commoncrawl"
          - name: CLOUD
            value: "aws"
          - name: FAILURE_FLAGS_ENABLED
            value: "true"
        probes:
          readiness:
            httpGet:
              path: /readiness
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 2
          liveness:
            httpGet:
              path: /liveness
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 2
      - name: gremlin-sidecar
        image: gremlin/failure-flags-sidecar:latest
        resources:
          cpu: 0.25    # Adjust as needed
          memory: 512Mi
        env:
          - name: GREMLIN_SIDECAR_ENABLED
            value: "true"
          - name: GREMLIN_TEAM_ID
            secretRef: gremlin-team-id
          - name: GREMLIN_TEAM_CERTIFICATE
            secretRef: gremlin-team-certificate
          - name: GREMLIN_TEAM_PRIVATE_KEY
            secretRef: gremlin-team-private-key
          - name: GREMLIN_DEBUG
            value: "true"
          - name: SERVICE_NAME
            value: "s3-failure-flags-app"
```

### Deployment and Monitoring Using the Azure CLI

Once you’ve saved this YAML configuration (for example, as `containerapp.yaml`), you can deploy and monitor your app with the following Azure CLI commands:

1. **Create a Resource Group and Environment (if not already created):**

  az group create --name myResourceGroup --location eastus

  az containerapp env create --name myContainerAppEnv --resource-group myResourceGroup --location eastus

2. **Deploy the Container App:**

  az containerapp create --resource-group myResourceGroup --yaml containerapp.yaml

3. **Retrieve the FQDN for testing:**

  az containerapp show --name s3-failure-flags-app --resource-group myResourceGroup --query properties.configuration.ingress.fqdn --output tsv

4. **Stream Logs for Monitoring:**

  az containerapp logs show --resource-group myResourceGroup --name s3-failure-flags-app --follow
