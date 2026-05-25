# AION OS — systemd deployment

Sovereign persistence for the M7 Ultra reference deployment. Both services run on boot, restart on failure, and depend on the local Ollama service for inference.

## Install

```bash
sudo cp deploy/systemd/aion-api.service /etc/systemd/system/
sudo cp deploy/systemd/aion-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now aion-api aion-web
```

## Verify

```bash
systemctl status aion-api aion-web --no-pager
curl -s http://localhost:8000/health
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5173/dashboard
```

## Assumptions

- Repo at `/home/echoblue/echoworks-ai`
- Python venv at `.venv/` with `requirements.txt` installed
- Node 20+ with `aion-sveltekit/node_modules/` installed
- Ollama installed (systemd unit `ollama.service` auto-created by `https://ollama.com/install.sh`)

## Provider auto-detection

`aionos.core.reasoning_engine` probes `localhost:11434` (Ollama) and `localhost:1234` (LM Studio) at startup. No env var change needed once Ollama is running.

Default to Independence. 🏛️
