# OpenArms Kubernetes Runbook

## Prerequisites
- Kubernetes cluster with NGINX ingress controller
- TLS certificate secret created in `armswideopen` namespace
- Container images pushed and tags updated in manifests
- (Optional) Prometheus Operator installed for `ServiceMonitor`
- (Optional) Secrets Store CSI driver installed for `SecretProviderClass`

## Deploy
```bash
kubectl apply -k k8s
kubectl -n armswideopen get pods,svc,ingress
```

## Verify health
```bash
kubectl -n armswideopen get deploy
kubectl -n armswideopen rollout status deploy/armswideopen-backend
kubectl -n armswideopen rollout status deploy/armswideopen-frontend
kubectl -n armswideopen port-forward svc/armswideopen-backend 8000:8000
curl -f http://localhost:8000/health
```

## Monitoring
- `k8s/monitoring.yaml` defines a `ServiceMonitor` for backend health endpoint.
- Ensure your Prometheus stack watches the `armswideopen` namespace.

## Backup automation
- `k8s/backup-cronjob.yaml` provides daily PostgreSQL dump job.
- Dumps stored in `postgres-backup-pvc`; set cluster snapshots/object offload for retention.

## Secret manager integration
- `k8s/secret-provider-class.yaml` provides AWS Secrets Manager example via CSI.
- Backend mounts CSI secrets at `/mnt/secrets-store`.
- Replace object name/paths with your secret schema.

## Common operations
- Restart backend:
```bash
kubectl -n armswideopen rollout restart deploy/armswideopen-backend
```
- Tail backend logs:
```bash
kubectl -n armswideopen logs deploy/armswideopen-backend -f
```
- Scale frontend:
```bash
kubectl -n armswideopen scale deploy/armswideopen-frontend --replicas=3
```

## Security checklist
- Replace placeholder secrets in `k8s/secret.yaml`
- Restrict ingress hosts and CORS in `k8s/configmap.yaml`
- Add network policies and pod security standards as cluster policy
