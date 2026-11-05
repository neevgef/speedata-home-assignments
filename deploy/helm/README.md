# SkyWatch Helm chart

This chart installs the SkyWatch frontend and backend. The frontend is exposed
through a NodePort Service (port `30080` by default); the backend has an
internal ClusterIP Service on port `8080`. The frontend's `BACKEND_URL` is
configured through a ConfigMap and defaults to the backend Service.

Install or render the chart from this directory:

```sh
helm lint .
helm template skywatch .
helm upgrade --install skywatch .
```

Override image repositories and tags, service settings, replica counts, or
resource requests and limits with a values file or `--set` options. For example:

```sh
helm upgrade --install skywatch . \
  --set frontend.image.tag=<tag> \
  --set backend.image.tag=<tag>
```