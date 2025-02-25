# Deploying s3-failure-flags-app to Azure Container Apps

This guide explains how to deploy the s3-failure-flags-app (with a Gremlin Failure Flags sidecar) to Azure Container Apps using a YAML configuration file and the Azure CLI. Follow these instructions to create required secrets, deploy the container app, and monitor its performance.

---

## Prerequisites

1. **Azure CLI**  
   Ensure you have the latest Azure CLI installed.  
   [Install or upgrade Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli)

2. **Azure Subscription & Resource Group**  
   You need an active Azure subscription and a resource group where the container app and its managed environment will be deployed.

3. **Secrets Setup**  
   The configuration uses secrets for the Gremlin sidecar credentials. You can create these secrets using the CLI or via the Azure portal. For example, to create secrets via the CLI:
   ```bash
   az containerapp secret set --name s3-failure-flags-app \
     --resource-group myResourceGroup \
     --secrets gremlin-team-id=<team_id_value> \
               gremlin-team-certificate=<team_certificate_value> \
               gremlin-team-private-key=<team_private_key_value>
   ```
   Replace `<team_id_value>`, `<team_certificate_value>`, and `<team_private_key_value>` with your actual credentials.

---

## YAML Configuration

Save the following YAML as `containerapp.yaml`. Update the placeholders (such as the `environmentId` and secret values) with your actual settings.

```yaml
name: s3-failure-flags-app
location: eastus
properties:
  # The managed environment ID for your Container Apps environment.
  environmentId: /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.App/managedEnvironments/<env-name>
  configuration:
    ingress:
      external: true
      targetPort: 8080
    secrets:
      # Define secrets for the Gremlin sidecar credentials.
      - name: gremlin-team-id
        value: <team_id_value>
      - name: gremlin-team-certificate
        value: <team_certificate_value>
      - name: gremlin-team-private-key
        value: <team_private_key_value>
  template:
    # Set the scaling to exactly 4 replicas.
    scale:
      minReplicas: 4
      maxReplicas: 4
    containers:
      - name: app-container
        image: jsabo/s3-failure-flags-app:latest
        resources:
          cpu: 0.5    # Adjust as needed.
          memory: 1Gi # Adjust as needed.
        env:
          - name: S3_BUCKET
            value: "commoncrawl"
          - name: CLOUD
            value: "azure"
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
          cpu: 0.25    # Adjust as needed.
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

---

## Deployment Steps

### 1. Create a Resource Group and Container Apps Environment

Run the following commands (adjust region and names as needed):

```bash
az group create --name myResourceGroup --location eastus

az containerapp env create --name myContainerAppEnv --resource-group myResourceGroup --location eastus
```

### 2. Deploy the Container App

Deploy your app using the YAML configuration:

```bash
az containerapp create --resource-group myResourceGroup --yaml containerapp.yaml
```

### 3. Retrieve the Application FQDN

Once deployment completes, get the Fully Qualified Domain Name (FQDN) for testing:

```bash
az containerapp show --name s3-failure-flags-app --resource-group myResourceGroup --query properties.configuration.ingress.fqdn --output tsv
```

---

## Monitoring Your Application

### View Logs

Stream logs (from both the app container and sidecar) to your terminal:

```bash
az containerapp logs show --resource-group myResourceGroup --name s3-failure-flags-app --follow
```

### Check Deployment Revisions

List revisions to verify the deployment status:

```bash
az containerapp revision list --resource-group myResourceGroup --name s3-failure-flags-app --output table
```

---

## Additional References

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps)
- [Manage Secrets in Azure Container Apps](https://learn.microsoft.com/azure/container-apps/secret-management)
- [Azure CLI Container Apps Commands](https://learn.microsoft.com/cli/azure/containerapp)
- [Configure a sidecar container for custom container in Azure App Service](https://learn.microsoft.com/en-us/azure/app-service/tutorial-custom-container-sidecar) 
