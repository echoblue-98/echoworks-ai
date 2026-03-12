"""Test optimized LM Studio latency"""
from aionos.api.lmstudio_client import LMStudioClient
import time

client = LMStudioClient()
print('=== LM Studio Latency Test ===')
print(f'Available: {client.is_available}')
print(f'Model: {client.get_loaded_model()}')

if client.is_available:
    content = 'Senior associate accessed 500 client files after giving notice. Bulk download detected.'
    
    print('\n--- TURBO MODE (optimized) ---')
    start = time.perf_counter()
    result = client.analyze(content, max_tokens=256, turbo=True)
    elapsed = (time.perf_counter() - start) * 1000
    print(f'Latency: {elapsed:.0f}ms')
    print(f'Risk Score: {result.get("risk_score", "N/A")}')
    if result.get("error"):
        print(f'Error: {result.get("error")}')
    
    print('\n--- QUICK ANALYZE (ultra-fast) ---')
    start = time.perf_counter()
    result = client.quick_analyze(content)
    elapsed = (time.perf_counter() - start) * 1000
    print(f'Latency: {elapsed:.0f}ms')
    print(f'Risk Score: {result.get("risk_score", "N/A")}')
    if result.get("error"):
        print(f'Error: {result.get("error")}')
else:
    print('\nLM Studio not running - start it with a model loaded')
    print('Recommended models for speed:')
    print('  - Qwen 2.5 1.5B/3B (fastest)')
    print('  - Phi-3 Mini (good balance)')
    print('  - Mistral 7B (quality + speed)')
