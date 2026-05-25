import json
import requests

r = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "qwen2.5:7b-instruct",
        "prompt": (
            'Tools available: [{"name":"kb_search","purpose":"Search firm policy"}]\n'
            "Question: What is our data retention policy?\n"
            'Respond ONLY with JSON of form {"tool":"<name>","args":{...}}'
        ),
        "system": "You are a tool-calling agent. Respond only with JSON.",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
    },
    timeout=60,
)
print("STATUS:", r.status_code)
data = r.json()
print("KEYS:", list(data.keys()))
print("RAW response field:", repr(data.get("response")))
print("DURATION (ns):", data.get("total_duration"))
