SUB="9d6b57ae-151b-4eef-b090-8511c39e04a2"
LOC="canadacentral"             
BASENAME="oliver"               
RG="rg-${BASENAME}-prod"
ACR="acr${BASENAME}"
ENV="aca-${BASENAME}-prod"     

echo "Logging into ACR"
az acr login --name $ACR

echo "Building backend image"
cd backend && docker build -t ${ACR}.azurecr.io/oliver-backend-api:latest . && cd ..
cd rag_service && docker build -t ${ACR}.azurecr.io/oliver-rag-service:latest . && cd ..

docker push ${ACR}.azurecr.io/oliver-backend-api:latest

az containerapp update -g "$RG" -n "oliver-backend-api" --image "${ACR}.azurecr.io/oliver-backend-api:latest"
az containerapp update -g "$RG" -n "oliver-rag-service" --image "${ACR}.azurecr.io/oliver-rag-service:latest"