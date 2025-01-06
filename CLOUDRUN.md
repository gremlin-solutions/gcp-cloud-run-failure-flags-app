## Deploy to Cloud Run

### Instructions to Create Secrets and Store Base64 Encoded Values

1. **Base64 Encode Values**:
   Prepare your values for storage in Google Secret Manager by encoding them as Base64:
   ```bash
   TEAM_ID="<YOUR_TEAM_ID>"
   BASE64_TEAM_ID=$(echo -n "$TEAM_ID" | base64)
   BASE64_CERT=$(cat path/to/cert.pem | base64 | tr -d '\n')
   BASE64_PRIV_KEY=$(cat path/to/key.pem | base64 | tr -d '\n')
   ```
   - Replace `<YOUR_TEAM_ID>` with your Gremlin Team ID.
   - Replace `path/to/cert.pem` and `path/to/key.pem` with the paths to your certificate and private key files, respectively.

2. **Create Secrets**:
   Use `gcloud` commands to create secrets in Secret Manager:
   ```bash
   gcloud secrets create gremlin-team-id --replication-policy="automatic"
   gcloud secrets create gremlin-team-certificate --replication-policy="automatic"
   gcloud secrets create gremlin-team-private-key --replication-policy="automatic"
   ```
   These commands create separate secrets for your Team ID, certificate, and private key with automatic replication.

3. **Store Base64 Encoded Values**:
   Add the Base64-encoded values to the created secrets:
   ```bash
   echo -n "$BASE64_TEAM_ID" | gcloud secrets versions add gremlin-team-id --data-file=-
   echo -n "$BASE64_CERT" | gcloud secrets versions add gremlin-team-certificate --data-file=-
   echo -n "$BASE64_PRIV_KEY" | gcloud secrets versions add gremlin-team-private-key --data-file=-
   ```

4. **Grant Access to Secrets**:
   Grant the service account used by Cloud Run access to the secrets:
   ```bash
   SERVICE_ACCOUNT="<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" # Replace with your project number

   gcloud secrets add-iam-policy-binding gremlin-team-id \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"

   gcloud secrets add-iam-policy-binding gremlin-team-certificate \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"

   gcloud secrets add-iam-policy-binding gremlin-team-private-key \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

   **Note**: 
   - If you're using the default Compute Engine service account (e.g., `<PROJECT_NUMBER>-compute@developer.gserviceaccount.com`), access is not automatically granted. You must explicitly grant the `roles/secretmanager.secretAccessor` role to the account.

### Reference Links

- [Identifying Projects](https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects)
- [Installing Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [Deploying a Service](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service)
- [Container Contract](https://cloud.google.com/run/docs/container-contract)
- [Deploying with YAML](https://cloud.google.com/run/docs/deploying#yaml)
- [Billing Settings](https://cloud.google.com/run/docs/configuring/billing-settings#choosing)

