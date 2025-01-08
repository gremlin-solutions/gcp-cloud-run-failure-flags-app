docker build --platform linux/amd64 -t jsabo/s3-failure-flags-app:latest .
docker push jsabo/s3-failure-flags-app:latest
kubectl rollout restart deployment s3-failure-flags-app
gcloud run services replace cloudrun-service.yaml
gcloud run deploy s3-failure-flags-app --image jsabo/s3-failure-flags-app:latest

