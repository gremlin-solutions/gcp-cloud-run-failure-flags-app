## Deploy to Cloud Run

#### Instructions to Create Secrets and Store Base64 Encoded Values

1. **Base64 Encode Values**:
   ```bash
   TEAM_ID="<YOUR_TEAM_ID>"
   BASE64_TEAM_ID=$(echo -n "$TEAM_ID" | base64)
   BASE64_CERT=$(cat path/to/cert.pem | base64 | tr -d '\n')
   BASE64_PRIV_KEY=$(cat path/to/key.pem | base64 | tr -d '\n')
   ```

2. **Create Secrets**:
   ```bash
   gcloud secrets create gremlin-team-id --replication-policy="automatic"
   gcloud secrets create gremlin-team-certificate --replication-policy="automatic"
   gcloud secrets create gremlin-team-private-key --replication-policy="automatic"
   ```

3. **Store Base64 Encoded Values**:
   ```bash
   echo -n "$BASE64_TEAM_ID" | gcloud secrets versions add gremlin-team-id --data-file=-
   echo -n "$BASE64_CERT" | gcloud secrets versions add gremlin-team-certificate --data-file=-
   echo -n "$BASE64_PRIV_KEY" | gcloud secrets versions add gremlin-team-private-key --data-file=-
   ```

4. **Grant Access to Secrets**:
   ```bash
   SERVICE_ACCOUNT="<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" # Replace with your service account

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

## Reference

- https://cloud.google.com/resource-manager/docs/creating-managing-projects#identifying_projects
- https://cloud.google.com/sdk/docs/install
- https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service
- https://cloud.google.com/run/docs/container-contract
- https://cloud.google.com/run/docs/deploying#yaml
- https://cloud.google.com/run/docs/configuring/billing-settings#choosing
