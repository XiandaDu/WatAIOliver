SUB="9d6b57ae-151b-4eef-b090-8511c39e04a2"
LOC="canadacentral"             
BASENAME="oliver"               
RG="rg-${BASENAME}-prod"
ACR="acr${BASENAME}"
ENV="aca-${BASENAME}-prod"     

az account set --subscription "$SUB"

# Resource Group
az group create -n "$RG" -l "$LOC"

# ACR (Container Registry)
# Create User-Assigned Managed Identity for ACR pull
MI_NAME="mi-${BASENAME}-acr-pull"
az identity create -g "$RG" -n "$MI_NAME"


MI_ID=$(az identity show -g "$RG" -n "$MI_NAME" --query principalId -o tsv | tr -d '\r\n')
ACR_ID=$(az acr show -n "$ACR" -g "$RG" --query id -o tsv | tr -d '\r\n')
az role assignment create --assignee "$MI_ID" --role "AcrPull" --scope "$ACR_ID"


MI_RESOURCE_ID=$(az identity show -g "$RG" -n "$MI_NAME" --query id -o tsv | tr -d '\r\n')
az acr create -n "$ACR" -g "$RG" --sku Basic

# Log Analytics (Log/Query)
az monitor log-analytics workspace create -g "$RG" -n "law-${BASENAME}"
LAW_ID=$(az monitor log-analytics workspace show -g "$RG" -n "law-${BASENAME}" --query customerId -o tsv | tr -d '\r\n')
LAW_KEY=$(az monitor log-analytics workspace get-shared-keys -g "$RG" -n "law-${BASENAME}" --query primarySharedKey -o tsv | tr -d '\r\n')

# ACA Environment (Mount Logs)
az containerapp env create -g "$RG" -n "$ENV" -l "$LOC" \
  --logs-workspace-id "$LAW_ID" --logs-workspace-key "$LAW_KEY"

# Placeholder Image (Use a public image for now, create App; CI will push your own image later)
PLACEHOLDER="mcr.microsoft.com/k8se/samples/helloworld:latest"

# 1) RAG Service (Internal Ingress) + Dapr
az containerapp create -g "$RG" -n "oliver-rag-service" --environment "$ENV" \
  --image "$PLACEHOLDER" \
  --target-port 8002 \
  --ingress internal \
  --enable-dapr true --dapr-app-id "oliver-rag-service" --dapr-app-port 8002 \
  --registry-server "${ACR}.azurecr.io" \
  --registry-identity "$MI_RESOURCE_ID"

# 2) Public API Gateway (FastAPI)
az containerapp create -g "$RG" -n "oliver-backend-api" --environment "$ENV" \
  --image "$PLACEHOLDER" \
  --target-port 8000 \
  --ingress external \
  --enable-dapr true --dapr-app-id "oliver-backend-api" --dapr-app-port 8000 \
  --registry-server "${ACR}.azurecr.io" \
  --registry-identity "$MI_RESOURCE_ID"
