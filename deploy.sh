#!/bin/bash
set -e

PROJECT_ID="authentication-1a0c4"
SERVICE_NAME="okoa-sem-backend"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Starting deployment to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Service: $SERVICE_NAME"
echo "Region: $REGION"

echo "🔑 Setting up Google Cloud project..."
gcloud config set project "$PROJECT_ID"

echo "⚙️ Enabling required Google Cloud APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com

echo "🐳 Building Docker image..."
docker build -t "$IMAGE_NAME:latest" .

echo "📤 Pushing image to Google Container Registry..."
docker push "$IMAGE_NAME:latest"

echo "🔐 Setting up Secret Manager permissions..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SERVICE_ACCOUNT="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

echo "Service Account: $SERVICE_ACCOUNT"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Permissions granted successfully!"

echo "🌐 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_NAME:latest" \
    --platform=managed \
    --region="$REGION" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=2Gi \
    --cpu=2 \
    --concurrency=100 \
    --max-instances=10 \
    --min-instances=0 \
    --timeout=300 \
    --set-env-vars="ALGORITHM=HS256" \
    --set-secrets="POSTGRES_SERVER=postgres-server:latest,POSTGRES_USER=postgres-user:latest,POSTGRES_PASSWORD=postgres-password:latest,POSTGRES_DB=postgres-db:latest,REDIS_URL=redis-url:latest,SECRET_KEY=secret-key:latest,YOUTUBE_API_KEY=youtube-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,BACKEND_CORS_ORIGINS=backend-cors-origins:latest"

echo "🔗 Getting service URL..."
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --format="value(status.url)")

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📋 API Documentation: $SERVICE_URL/docs"
echo "❤️ Health Check: $SERVICE_URL/health"
echo ""

echo "🧪 Testing deployment..."
if curl -f "$SERVICE_URL/health" >/dev/null 2>&1; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    exit 1
fi

echo "🎉 Deployment completed successfully!"
echo "Your FastAPI backend is now live at: $SERVICE_URL"