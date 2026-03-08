#!/bin/bash
# setup-iam.sh — Configure IAM for Cloud Run service-to-service auth
#
# This grants the orchestrator's service account permission to invoke
# the specialist agent services. Run once after first deploy.
#
# Usage: ./setup-iam.sh

set -euo pipefail

PROJECT="${GOOGLE_CLOUD_PROJECT:-gcloud-hackathon-9er4rb4nr0k7a}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

# The default compute service account used by Cloud Run
SA="${PROJECT_NUMBER:-$(gcloud projects describe ${PROJECT} --format='value(projectNumber)')}"-compute@developer.gserviceaccount.com

echo "Project: ${PROJECT}"
echo "Region:  ${REGION}"
echo "SA:      ${SA}"
echo ""

# Enable required APIs
echo "==> Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  iamcredentials.googleapis.com \
  --project="${PROJECT}"

# Grant the orchestrator SA permission to invoke each specialist service
SERVICES=("filament-screen-analyst" "filament-workspace-agent" "filament-nudge-composer")

for SVC in "${SERVICES[@]}"; do
  echo "==> Granting invoker role on ${SVC} to ${SA}..."
  gcloud run services add-iam-policy-binding "${SVC}" \
    --project="${PROJECT}" \
    --region="${REGION}" \
    --member="serviceAccount:${SA}" \
    --role="roles/run.invoker" \
    2>/dev/null || echo "   (service not deployed yet — run deploy.sh first)"
done

# Grant Cloud Build SA permissions to deploy
CB_SA="${PROJECT_NUMBER:-$(gcloud projects describe ${PROJECT} --format='value(projectNumber)')}@cloudbuild.gserviceaccount.com"
echo ""
echo "==> Granting Cloud Build deploy permissions..."
gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/run.admin" \
  --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding "${PROJECT}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None 2>/dev/null || true

echo ""
echo "Done. IAM configured for service-to-service auth."
echo ""
echo "To lock down services (disable public access on specialists):"
echo "  gcloud run services remove-iam-policy-binding filament-screen-analyst \\"
echo "    --region=${REGION} --member=allUsers --role=roles/run.invoker"
echo "  (repeat for workspace-agent and nudge-composer)"
