# Terminal 1 — Base de datos (Cosmos DB Emulator en Docker)

```bash
# (opcional) limpia si quedó un contenedor previo
docker rm -f cosmos-emulator 2>/dev/null || true

# baja/actualiza la imagen (si no la tienes)
docker pull mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest

# ejecuta el emulador
docker run --name cosmos-emulator \
  -e AZURE_COSMOS_EMULATOR_PARTITION_COUNT=2 \
  -e AZURE_COSMOS_EMULATOR_ENABLE_DATA_PERSISTENCE=true \
  -e AZURE_COSMOS_EMULATOR_ACCEPT_LICENSE=Y \
  -e AZURE_COSMOS_EMULATOR_IP_ADDRESS_OVERRIDE=127.0.0.1 \
  -p 8081:8081 -p 10250-10255:10250-10255 \
  mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
```

> Déjalo corriendo aquí. Cuando veas `Started` ya está OK.

---

# Terminal 2 — Backend (Azure Functions en Python)

```bash
# entra al proyecto del backend
cd backend/azure_functions


python3.12 -m venv .venv
source .venv/bin/activate

# asegúrate de tener el local.settings.json correcto (con COSMOS_VERIFY=false)
# instala dependencias en .python_packages (lo que usa Functions)
pip install --upgrade pip
pip install -r requirements.txt -t .python_packages/lib/site-packages

# arranca las Functions
func start --verbose
```

> Deberías ver los endpoints tipo `http://localhost:7071/api/...`

---

# Terminal 3 — Frontend (React)

```bash
cd frontend

# instala dependencias
npm install

# (ya tienes .env.local apuntando al backend: http://localhost:7071/api)
npm start
```

> Quedará en `http://localhost:3000`

---

# Terminal 4 — Git (flujo de trabajo sugerido)

```bash
# desde la raíz del repo
cd ~/P/jaime-azure-example-todo-list-app-v2

# crea rama de trabajo
git checkout -b feat/pruebas-locales

# (trabajas, editas archivos…)
git status
git add -A
git commit -m "chore: setup local run (cosmos emulator + functions + react)"

# empuja la rama
git push -u origin feat/pruebas-locales
```

---

## Smoke test rápido (opcional, en un 5to shell o cualquiera)

Crea usuario, loguéate y lista tareas para validar el backend:

```bash
# crea usuario
curl -sS -X POST http://localhost:7071/api/user/register \
  -H "Content-Type: application/json" \
  -d '{"email":"a@a.com","password":"123","name":"Alice"}' | jq

# login -> guarda token en variable
TOKEN=$(curl -sS -X POST http://localhost:7071/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"a@a.com","password":"123"}' | jq -r .token)

# crea una tarea
curl -sS -X POST http://localhost:7071/api/tasks \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"title":"Probar Cosmos","status":"pending"}' | jq

# lista tareas
curl -sS -X GET http://localhost:7071/api/tasks \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Cómo parar todo

- **DB**: `Ctrl+C` en la Terminal 1 y, si quieres borrar: `docker rm -f cosmos-emulator`
- **Backend**: `Ctrl+C` en la Terminal 2
- **Frontend**: `Ctrl+C` en la Terminal 3
