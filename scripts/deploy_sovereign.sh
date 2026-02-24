#!/bin/bash
# 🚀 AETHEROS — SOVEREIGN DEPLOYMENT SCRIPT
# ==========================================
# Automates the provisioning of GCP Service Accounts and Firebase Hosting.

echo "🌌 Initializing AetherOS Sovereign Deployment..."

# 1. Project Detection
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: GOOGLE_CLOUD_PROJECT not set. Run 'gcloud config set project [ID]'"
    exit 1
fi

echo "📍 Target Project: $PROJECT_ID"

# 2. Service Account Provisioning
SA_NAME="aether-forge-executor"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe "$SA_EMAIL" > /dev/null 2>&1; then
    echo "🔑 Creating Service Account: $SA_NAME..."
    gcloud iam service-accounts create "$SA_NAME" --display-name="Aether Forge Executor"
else
    echo "✅ Service Account already exists."
fi

# 3. Roles Assignment (Firestore & AI)
echo "🛡️ Assigning Roles..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_EMAIL" --role="roles/datastore.user"
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$SA_EMAIL" --role="roles/aiplatform.user"

# 4. Build Edge Client
echo "🏗️ Building Edge Client..."
cd edge_client && npm install && npm run build && cd ..

# 5. Firebase Deploy
echo "🔥 Deploying to Firebase..."
firebase deploy --only hosting,firestore

echo "✅ AetherOS Sovereign Deployment Complete."
