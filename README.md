# SafeSip-AI-Lab

AI-assisted research platform for drink spiking detection and beverage safety analysis.

## Goals

- collect literature
- analyze detection methods
- build drug knowledge base
- assist experimental design

## Current Progress

- [x] FastAPI project initialization
- [x] PubMed literature search API
- [x] Basic diagnostics and health checks
- [ ] AI-based method extraction
- [ ] Detection benchmark pipeline

## Run Locally

```powershell
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Open:

- App: http://127.0.0.1:8001
- API docs: http://127.0.0.1:8001/docs
- App health: http://127.0.0.1:8001/health
- PubMed health: http://127.0.0.1:8001/api/pubmed-health

## Troubleshooting

If the page opens but PubMed search fails:

1. Open `/api/pubmed-health` to check whether the backend can reach PubMed.
2. Check the uvicorn terminal logs for `request_id`, `pubmed.*.connection_failed`, `pubmed.*.timeout`, or `pubmed.*.http_error`.
3. If you see `pubmed_connection_failed` or `WinError 10013`, check local firewall, proxy, VPN, network policy, or run the app from a terminal that is allowed to access the network.
4. Use the `Request ID` shown in the browser to find the matching backend log lines.
