## Deploy to Cloud Run

### Instructions to Create Secrets

1. **Create Secrets**:
   Use the following commands to create secrets in **Google Secret Manager**:
   ```bash
   gcloud secrets create gremlin-team-id --replication-policy="automatic"
   gcloud secrets create gremlin-team-certificate --replication-policy="automatic"
   gcloud secrets create gremlin-team-private-key --replication-policy="automatic"
   gcloud secrets create aws-access-key-id --replication-policy="automatic"
   gcloud secrets create aws-secret-access-key --replication-policy="automatic"
   ```

2. **Store Values**:
   Add your values to the secrets:
   ```bash
   echo -n "<YOUR_TEAM_ID>" | gcloud secrets versions add gremlin-team-id --data-file=-
   gcloud secrets versions add gremlin-team-certificate --data-file=path/to/cert.pem
   gcloud secrets versions add gremlin-team-private-key --data-file=path/to/key.pem
   echo -n "<YOUR_AWS_ACCESS_KEY_ID>" | gcloud secrets versions add aws-access-key-id --data-file=-
   echo -n "<YOUR_AWS_SECRET_ACCESS_KEY>" | gcloud secrets versions add aws-secret-access-key --data-file=-
   ```

   Replace:
   - `<YOUR_TEAM_ID>` with your Gremlin Team ID.
   - `path/to/cert.pem` and `path/to/key.pem` with the paths to your Gremlin team certificate and private key files.
   - `<YOUR_AWS_ACCESS_KEY_ID>` and `<YOUR_AWS_SECRET_ACCESS_KEY>` with your AWS credentials.

3. **Grant Access to Secrets**:
   Assign the necessary permissions to the Cloud Run service account:
   ```bash
   SERVICE_ACCOUNT="<PROJECT_NUMBER>-compute@developer.gserviceaccount.com" # Replace with your project number

   # Grant access to Gremlin secrets
   gcloud secrets add-iam-policy-binding gremlin-team-id \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"

   gcloud secrets add-iam-policy-binding gremlin-team-certificate \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"

   gcloud secrets add-iam-policy-binding gremlin-team-private-key \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"

   # Grant access to AWS credentials
   gcloud secrets add-iam-policy-binding aws-access-key-id \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"

   gcloud secrets add-iam-policy-binding aws-secret-access-key \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/secretmanager.secretAccessor"
   ```

---

### Deploy Your Application

1. **Create a Deployment YAML File**:
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
             image: 'jsabo/s3-failure-flags-app:latest'
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

2. **Deploy to Cloud Run**:
   Deploy the service using the YAML file:
   ```bash
   gcloud run services replace cloudrun-service.yaml
   ```

3. **Verify Deployment**:
   Confirm that the service is running:
   ```bash
   gcloud run services describe s3-failure-flags-app --format="yaml(status.conditions)"
   ```

4. **View Logs**:
   Check the logs to ensure the service is working correctly:
   ```bash
   gcloud logging read 'resource.labels.service_name="s3-failure-flags-app"' --limit=100 --freshness=2m
   ```

5. **Tail Logs**:
   Tail the logs to ensure the service is working correctly:
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

6. **Grant Cloud Run Invocation Permissions**:
   Make the Cloud Run service publicly accessible by granting the `roles/run.invoker` role to `allUsers`. This step allows anyone to invoke the service endpoint:
   ```bash
   gcloud run services add-iam-policy-binding s3-failure-flags-app \
     --region=us-east1 \
     --member="allUsers" \
     --role="roles/run.invoker"
   ```

   **Note**: This command makes your Cloud Run service accessible to anyone with the service URL. Ensure this is acceptable for your use case.

### Reference Links
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Deploying to Cloud Run with YAML](https://cloud.google.com/run/docs/deploying#yaml)
- [Managing Cloud Run Secrets](https://cloud.google.com/run/docs/configuring/secrets)
- [Gremlin Documentation](https://www.gremlin.com/docs/)

