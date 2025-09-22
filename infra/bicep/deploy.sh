#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Uso: $0 <subscription_id> <resource_group> [location]" >&2
  exit 1
fi

SUBSCRIPTION_ID="$1"
RESOURCE_GROUP="$2"
LOCATION="${3:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PARAMS_FILE="${SCRIPT_DIR}/main.parameters.json"
TEMPLATE_FILE="${SCRIPT_DIR}/main.bicep"

az account set --subscription "$SUBSCRIPTION_ID"

if [ -n "$LOCATION" ]; then
  az group create \
    --name "$RESOURCE_GROUP" \
    --location "$LOCATION"
fi

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$TEMPLATE_FILE" \
  --parameters "@${PARAMS_FILE}"

echo "\nDespliegue completado."
