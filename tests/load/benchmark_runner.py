"""
Standalone Concurrency Benchmark Runner using concurrent.futures
Simulates high concurrent client load without requiring extra external CLI tools.
Measures:
- Total requests
- Concurrency levels (10, 50, 100, 250, 500, 1000 requests)
- Errors & Exceptions
- Latency (p50, p95, p99, min, max, avg)
- Requests per second (RPS)
"""
import time
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

BASE_URL = "http://127.0.0.1:8000"

TEST_PAYLOADS = [
    {"message": "hello"},
    {"message": "what can you do?"},
    {"message": "সর্বশেষ নোটিশ দেখান"},
    {"message": "Recent notices"},
    {"message": "অনার্স ভর্তি তথ্য"},
    {"message": "NU-2026-000001"}
]

def make_request(idx: int) -> tuple[bool, float, int]:
    payload = TEST_PAYLOADS[idx % len(TEST_PAYLOADS)]
    data_bytes = json.dumps(payload).encode("utf-8")
    simulated_ip = f"192.168.{(idx // 250) + 1}.{(idx % 250) + 1}"
    req = urllib.request.Request(
        f"{BASE_URL}/api/v1/chat",
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Forwarded-For": simulated_ip
        }
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            dur = (time.perf_counter() - t0) * 1000.0
            return (True, dur, resp.status)
    except Exception as e:
        dur = (time.perf_counter() - t0) * 1000.0
        return (False, dur, getattr(e, "code", 500))

def run_concurrency_tier(concurrency: int, total_requests: int) -> dict:
    print(f"\n--- Running Concurrency Tier: {concurrency} workers ({total_requests} requests) ---")
    t_start = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, i) for i in range(total_requests)]
        for f in as_completed(futures):
            results.append(f.result())
    t_total = time.perf_counter() - t_start

    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]
    durations = [r[1] for r in successes]

    rps = len(results) / t_total if t_total > 0 else 0
    p50 = statistics.median(durations) if durations else 0
    p95 = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else (max(durations) if durations else 0)
    p99 = statistics.quantiles(durations, n=100)[98] if len(durations) >= 100 else (max(durations) if durations else 0)

    summary = {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "success_count": len(successes),
        "failure_count": len(failures),
        "error_rate_pct": (len(failures) / total_requests) * 100.0,
        "total_duration_sec": round(t_total, 2),
        "rps": round(rps, 2),
        "avg_ms": round(statistics.mean(durations), 2) if durations else 0,
        "p50_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(p99, 2)
    }
    print(f"Result: {summary['rps']} req/s | Success: {summary['success_count']}/{total_requests} | p50: {summary['p50_ms']}ms | p95: {summary['p95_ms']}ms")
    return summary

if __name__ == "__main__":
    tiers = [
        (10, 100),
        (50, 250),
        (100, 500),
        (250, 1000),
        (500, 1000),
        (1000, 1000)
    ]
    report = []
    for conc, tot in tiers:
        res = run_concurrency_tier(conc, tot)
        report.append(res)

    with open("tests/load/benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print("\nBenchmark successfully saved to tests/load/benchmark_results.json!")