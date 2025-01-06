docker build --platform linux/amd64 -t jsabo/s3-failure-flags-app:latest .
docker push jsabo/s3-failure-flags-app:latest
kubectl rollout restart deployment s3-failure-flags-app
