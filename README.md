# OpenArms

An open-source implementation of Hugging Face Hub with Git LFS support, web UI, and full SDK compatibility.

## Features

- 🎯 **Model & Dataset Registry** - Discover and share models and datasets
- 🔐 **User Authentication** - Secure user accounts and access control
- 📦 **Git LFS Storage** - Efficient large file handling
- 🎨 **Web Interface** - Similar to Hugging Face Hub
- 🐍 **Python SDK** - Full compatibility with Hugging Face libraries
- 🔍 **Search & Discovery** - Find models and datasets easily
- 📊 **Metadata Management** - Tags, descriptions, and version control

## Architecture

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Storage**: Git LFS + S3-compatible storage
- **Authentication**: JWT

### Frontend
- **Framework**: React 18 + TypeScript
- **UI Library**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL (or SQLite for development)
- Git LFS

### Backend Setup

```bash
cd backend
pip install -e ".[dev]"
export DATABASE_URL="sqlite:///./armswideopen.db"
uvicorn armswideopen.main:app --reload
```

API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

UI will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Key Endpoints

### Users
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - Login user
- `GET /api/v1/users/{username}` - Get user profile

### Models
- `GET /api/v1/models` - List public models
- `GET /api/v1/models/{model_id}` - Get model details
- `POST /api/v1/models` - Create new model (requires auth)
- `PUT /api/v1/models/{model_id}` - Update model (requires auth)
- `DELETE /api/v1/models/{model_id}` - Delete model (requires auth)

### Datasets
- `GET /api/v1/datasets` - List public datasets
- `GET /api/v1/datasets/{dataset_id}` - Get dataset details
- `POST /api/v1/datasets` - Create new dataset (requires auth)
- `PUT /api/v1/datasets/{dataset_id}` - Update dataset (requires auth)
- `DELETE /api/v1/datasets/{dataset_id}` - Delete dataset (requires auth)

## Development

### Running Tests

```bash
cd backend
pytest
```

Transformers end-to-end test against a running OpenArms backend:

```bash
pip install -e ".[dev]"
OPENARMS_ENDPOINT=http://localhost:8000 pytest -q tests/test_transformers_openarms_e2e.py
```

## Python SDK and CLI

The repository now includes a Python SDK and CLI compatibility layer.

### SDK example

```python
from armswideopen import HfApi, hf_hub_download

api = HfApi(endpoint="http://localhost:8000")
api.login("alice", "password123")
api.create_repo("alice/my-model")
api.upload_file(
    repo_id="alice/my-model",
    path_or_fileobj="model.bin",
    path_in_repo="model.bin",
)
local_path = hf_hub_download("alice/my-model", "model.bin", endpoint="http://localhost:8000")
print(local_path)
```

### CLI example

```bash
armswideopen --endpoint http://localhost:8000 login alice password123
armswideopen --endpoint http://localhost:8000 whoami
armswideopen --endpoint http://localhost:8000 list-models --search my-model
armswideopen --endpoint http://localhost:8000 create-model alice/my-model
armswideopen --endpoint http://localhost:8000 upload-file alice/my-model ./model.bin
armswideopen --endpoint http://localhost:8000 download-file alice/my-model model.bin --revision main
```

### Code Quality

```bash
# Format code
black armswideopen/

# Lint
ruff check armswideopen/

# Type checking
mypy armswideopen/
```

## Deployment

### Docker

```bash
docker-compose up -d
```

See `docker-compose.yml` for configuration details.

### Kubernetes

Production deployment manifests are under `k8s/`.

Key resources included:
- Namespace, ConfigMap, Secret
- PostgreSQL Deployment/Service/PVC
- Backend Deployment/Service/PVC
- Frontend Deployment/Service
- NGINX Ingress

Build and push images (example):

```bash
docker build -f backend/Dockerfile -t ghcr.io/your-org/armswideopen-backend:latest .
docker build -f frontend/Dockerfile -t ghcr.io/your-org/armswideopen-frontend:latest .
docker push ghcr.io/your-org/armswideopen-backend:latest
docker push ghcr.io/your-org/armswideopen-frontend:latest
```

Update image names in:
- `k8s/backend.yaml`
- `k8s/frontend.yaml`

Apply manifests:

```bash
kubectl apply -k k8s
```

Set your host and TLS secret:
- Update `armswideopen.example.com` in `k8s/ingress.yaml`
- Create `armswideopen-tls` in namespace `armswideopen`

Recommended production hardening:
- Replace placeholder secrets in `k8s/secret.yaml`
- Use managed PostgreSQL instead of in-cluster Postgres for HA
- Configure object storage for LFS payloads
- See `k8s/runbook.md` for deployment and operations procedures
- Monitoring manifest: `k8s/monitoring.yaml`
- Backup automation manifest: `k8s/backup-cronjob.yaml`
- Secret manager integration manifest: `k8s/secret-provider-class.yaml`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT

## Resources

- [Hugging Face Hub Documentation](https://huggingface.co/docs/hub)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)

## Roadmap

- [x] Basic API structure
- [x] User authentication
- [x] Model/Dataset registry
- [ ] Git LFS integration
- [ ] File upload/download
- [ ] Web UI components
- [ ] Python SDK
- [ ] CLI tools
- [ ] Search indexing
- [ ] Caching layer
- [ ] Rate limiting
