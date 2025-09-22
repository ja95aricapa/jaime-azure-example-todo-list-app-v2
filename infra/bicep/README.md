# Infraestructura Azure (Bicep)

Este directorio contiene la definición IaC para desplegar la aplicación todo list en Azure.

## Recursos que se aprovisionan

- **Cosmos DB (SQL API)** con una base de datos `todoapp` y contenedores `users` (partición `/email`) y `tasks` (partición `/userId`) con autoscale habilitado.
- **Storage account** dedicado a las Azure Functions (incluye cola/blob y configuración TLS).
- **Plan de consumo y Function App** (runtime Python) con variables de entorno para Cosmos y JWT.
- **Application Insights** enlazado a la Function App y como sink de diagnóstico para API Management.
- **API Management** con operaciones que redirigen a los endpoints de la Function App (`/tasks`, `/user/*`), un named value con la Function Key, una política que la inyecta automáticamente en el backend y la publicación en el producto `starter` para usar claves de suscripción.
- **Storage account** para el frontend con sitio estático habilitado.
- **Perfil y Endpoint de Azure CDN** (opcional) que sirven el sitio estático desde la cuenta de almacenamiento del frontend.
- Configuración opcional de autenticación con Entra ID (si se proporciona `aadClientId`).

## Preparación

1. **Autenticación Azure CLI**
   ```bash
   az login
   az account set --subscription <SUBSCRIPTION_ID>
   ```
2. **Editar parámetros**
   Actualiza `main.parameters.json` con:
   - `namePrefix`: prefijo corto y único (se usa en los nombres de recursos).
   - `location`: región Azure (p.ej. `eastus`).
   - `jwtSecret`: valor seguro usado por el backend para firmar tokens.
   - Datos de contacto de API Management.
   - `allowedCorsOrigins`: lista blanca de orígenes autorizados para el backend (añade aquí tu dominio del frontend y/o `https://localhost:3000`).
   - `cosmosMaxAutoscaleThroughput`: RU máximas (mínimo 4000) para Cosmos autoscale.
   - Opcionalmente ajusta `apiManagementSkuName`, `apiManagementSkuCapacity`, etc.
   Si usarás autenticación Entra ID deja preparado un App Registration y añade `aadClientId` mediante `--parameters aadClientId=<GUID>` durante el despliegue.

## Despliegue

Puedes usar el script de conveniencia:
```bash
cd infra/bicep
chmod +x deploy.sh
./deploy.sh <SUBSCRIPTION_ID> <RESOURCE_GROUP> <LOCATION>
```
- El parámetro `LOCATION` es opcional; si se omite, el script asume que el grupo ya existe.
- El script usa `main.parameters.json`. Para valores distintos, puedes pasar parámetros adicionales con `az deployment group create`.

Ejemplo manual:
```bash
az deployment group create \
  --resource-group <RG_NAME> \
  --template-file infra/bicep/main.bicep \
  --parameters namePrefix=todoapp location=eastus jwtSecret="$(openssl rand -base64 32)" \
  --parameters apiManagementPublisherEmail=admin@example.com apiManagementPublisherName="Todo Team"
```

## Post-deploy

1. **Publicar Azure Functions**
   ```bash
   cd backend/azure_functions
   func azure functionapp publish <FUNCTION_APP_NAME> --python
   ```
2. **Configurar CORS / claves**
   - El parámetro `allowedCorsOrigins` controla los orígenes permitidos. Puedes actualizarlo y reprovisionar o ejecutar `az functionapp cors add` para cambios puntuales.
   - El despliegue expone la salida `functionHostDefaultKey` (marcada como secreta) para que puedas poblar `REACT_APP_API_KEY` en el frontend o crear suscripciones en API Management.
3. **Construir y subir el frontend**
   ```bash
   cd frontend
   npm install
   npm run build
   az storage blob upload-batch \
     --account-name <FRONTEND_STORAGE_NAME> \
     --destination "\$web" \
     --source build \
     --overwrite true
   ```
   Si activaste CDN, purga la caché tras subir cambios:
   ```bash
   az cdn endpoint purge \
     --profile-name <CDN_PROFILE_NAME> \
     --resource-group <RG_NAME> \
     --name <CDN_ENDPOINT_NAME> \
     --content-paths "/*"
   ```
4. **Actualizar variables de entorno adicionales**
   - `COSMOS_VERIFY` se define como `true` por defecto.
   - Ajusta `REACT_APP_API_BASE` (APIM gateway), `REACT_APP_API_KEY` (clave de suscripción de APIM o Function Key) y, si usas otro header como `Ocp-Apim-Subscription-Key`, configura `REACT_APP_API_KEY_HEADER`.

## Autenticación con Entra ID

Si aportas `aadClientId`, la Function App exige login Entra ID. Pasos sugeridos:
1. Crea una app registration (web) con redirect URI `https://<FUNCTION_APP_HOST>.azurewebsites.net/.auth/login/aad/callback`.
2. Copia el `Application (client) ID` y úsalo como parámetro (`--parameters aadClientId=<GUID>`).
3. Ajusta el frontend para usar MSAL y solicitar tokens hacia API Management/Gateway.

## Salidas principales

Tras el despliegue, revisa las salidas (`az deployment group create ... --query properties.outputs`). Se devuelven nombres/urls de Function App, Cosmos, API Management, endpoints del frontend/CDN y la `functionHostDefaultKey` (marcada como secreta).
