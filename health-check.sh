#!/bin/bash


set -e

PROJECT_ID="authentication-1a0c4"
SERVICE_NAME="okoa-sem-backend"
REGION="us-central1"

echo "🔍 Running post-deployment health checks..."

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --platform=managed \
    --region="$REGION" \
    --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Could not get service URL"
    exit 1
fi

echo "🌐 Service URL: $SERVICE_URL"

echo "🧪 Testing endpoints..."

echo "Testing /health endpoint..."
if curl -f -s "$SERVICE_URL/health" | jq . >/dev/null 2>&1; then
    echo "✅ Health endpoint: OK"
else
    echo "❌ Health endpoint: FAILED"
fi

echo "Testing root endpoint..."
if curl -f -s "$SERVICE_URL/" | jq . >/dev/null 2>&1; then
    echo "✅ Root endpoint: OK"
else
    echo "❌ Root endpoint: FAILED"
fi

echo "Testing /docs endpoint..."
if curl -f -s "$SERVICE_URL/docs" >/dev/null 2>&1; then
    echo "✅ API docs endpoint: OK"
else
    echo "❌ API docs endpoint: FAILED"
fi

echo "Testing /openapi.json endpoint..."
if curl -f -s "$SERVICE_URL/api/v1/openapi.json" | jq . >/dev/null 2>&1; then
    echo "✅ OpenAPI schema endpoint: OK"
else
    echo "❌ OpenAPI schema endpoint: FAILED"
fi

echo ""
echo "📊 Service Information:"
echo "🌐 Service URL: $SERVICE_URL"
echo "📋 API Documentation: $SERVICE_URL/docs"
echo "🔗 OpenAPI Schema: $SERVICE_URL/api/v1/openapi.json"
echo "❤️ Health Check: $SERVICE_URL/health"

echo ""
echo "🎯 Quick Test Commands:"
echo "curl $SERVICE_URL/health"
echo "curl $SERVICE_URL/"

echo ""
echo "✅ Health check completed!"