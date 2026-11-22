"""DisputeGuard — Production Deployment Live Diagnostic Verifier.

Queries the live Vercel frontend and Render backend endpoints, evaluates CORS
preflight and simple requests, and documents response latencies and payloads.
"""

import json
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def perform_probe(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 35.0,
) -> Dict[str, Any]:
    """Execute an HTTP request and measure latency and header details."""
    if headers is None:
        headers = {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = "DisputeGuard-Diagnostic/2.0"

    req = urllib.request.Request(url, headers=headers, method=method)
    start_time = time.perf_counter()
    result = {
        "url": url,
        "method": method,
        "request_headers": headers,
        "status_code": None,
        "latency_ms": None,
        "response_headers": {},
        "body_preview": None,
        "json_body": None,
        "error": None,
        "success": False,
    }
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            latency = (time.perf_counter() - start_time) * 1000
            result["status_code"] = response.status
            result["latency_ms"] = round(latency, 2)
            result["response_headers"] = dict(response.headers)
            body = response.read().decode("utf-8", errors="replace")
            result["body_preview"] = body[:400]
            try:
                result["json_body"] = json.loads(body)
            except Exception:
                pass
            result["success"] = True
    except urllib.error.HTTPError as e:
        latency = (time.perf_counter() - start_time) * 1000
        result["status_code"] = e.code
        result["latency_ms"] = round(latency, 2)
        result["response_headers"] = dict(e.headers)
        body = e.read().decode("utf-8", errors="replace")
        result["body_preview"] = body[:400]
        try:
            result["json_body"] = json.loads(body)
        except Exception:
            pass
        result["error"] = f"HTTPError: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        latency = (time.perf_counter() - start_time) * 1000
        result["latency_ms"] = round(latency, 2)
        result["error"] = f"URLError: {e.reason}"
    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000
        result["latency_ms"] = round(latency, 2)
        result["error"] = f"{type(e).__name__}: {str(e)}"

    return result


def main():
    fe_url = "https://razorpay-ai-risk-manager.vercel.app"
    be_url = "https://disputeguard-backend.onrender.com"

    print("=" * 75)
    print("DISPUTEGUARD LIVE DEPLOYMENT DIAGNOSTIC SUITE")
    print(f"Frontend URL : {fe_url}")
    print(f"Backend URL  : {be_url}")
    print("=" * 75)

    checks = []

    # 1. Frontend Root Availability
    print("\n[1] Querying Frontend Root Availability...")
    fe_root = perform_probe(fe_url)
    print(f"    Status: {fe_root['status_code']} | Latency: {fe_root['latency_ms']}ms | Success: {fe_root['success']}")
    checks.append(("Frontend Root URL", fe_root))

    # 2. Backend Root (/)
    print("\n[2] Querying Backend Root (/)...")
    be_root = perform_probe(f"{be_url}/")
    print(f"    Status: {be_root['status_code']} | Latency: {be_root['latency_ms']}ms | Success: {be_root['success']}")
    if be_root["json_body"]:
        print(f"    Payload: {be_root['json_body']}")
    checks.append(("Backend Root (/)", be_root))

    # 3. Backend Health (/health)
    print("\n[3] Querying Backend Health (/health)...")
    be_health = perform_probe(f"{be_url}/health")
    print(f"    Status: {be_health['status_code']} | Latency: {be_health['latency_ms']}ms | Success: {be_health['success']}")
    if be_health["json_body"]:
        print(f"    Payload: {be_health['json_body']}")
    checks.append(("Backend Health (/health)", be_health))

    # 4. Backend Cases (/cases)
    print("\n[4] Querying Backend Cases (/cases)...")
    be_cases = perform_probe(f"{be_url}/cases")
    print(f"    Status: {be_cases['status_code']} | Latency: {be_cases['latency_ms']}ms | Success: {be_cases['success']}")
    if be_cases["json_body"]:
        cases = be_cases["json_body"].get("cases", [])
        print(f"    Cases count: {len(cases)}")
        if cases:
            print(f"    Case 0: ID={cases[0].get('id')}, Amount={cases[0].get('amount')} {cases[0].get('currency')}, Reason={cases[0].get('reason')}")
    checks.append(("Backend Cases (/cases)", be_cases))

    # 5. Backend Specific Case (/cases/DSP-2026-0001)
    print("\n[5] Querying Backend Specific Case (/cases/DSP-2026-0001)...")
    be_case_detail = perform_probe(f"{be_url}/cases/DSP-2026-0001")
    print(f"    Status: {be_case_detail['status_code']} | Latency: {be_case_detail['latency_ms']}ms | Success: {be_case_detail['success']}")
    if be_case_detail["json_body"]:
        c_obj = be_case_detail["json_body"].get("case", {})
        docs = be_case_detail["json_body"].get("evidence_documents", [])
        print(f"    Dispute: ID={c_obj.get('id')}, Customer={c_obj.get('customer_name')}, Docs Attached={len(docs)}")
    checks.append(("Backend Specific Case (/cases/DSP-2026-0001)", be_case_detail))

    # 6. Backend CORS Preflight (OPTIONS /cases from Vercel Origin)
    print("\n[6] Querying CORS Preflight (OPTIONS /cases) from Origin: " + fe_url)
    cors_preflight = perform_probe(
        f"{be_url}/cases",
        method="OPTIONS",
        headers={
            "Origin": fe_url,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    print(f"    Status: {cors_preflight['status_code']} | Latency: {cors_preflight['latency_ms']}ms")
    preflight_origin = cors_preflight["response_headers"].get("access-control-allow-origin")
    preflight_methods = cors_preflight["response_headers"].get("access-control-allow-methods")
    preflight_cred = cors_preflight["response_headers"].get("access-control-allow-credentials")
    print(f"    Access-Control-Allow-Origin: {preflight_origin}")
    print(f"    Access-Control-Allow-Methods: {preflight_methods}")
    print(f"    Access-Control-Allow-Credentials: {preflight_cred}")
    checks.append(("CORS Preflight (OPTIONS /cases)", cors_preflight))

    # 7. Backend CORS Actual GET (/health from Vercel Origin)
    print("\n[7] Querying CORS Actual GET (/health) from Origin: " + fe_url)
    cors_health = perform_probe(
        f"{be_url}/health",
        method="GET",
        headers={"Origin": fe_url},
    )
    print(f"    Status: {cors_health['status_code']} | Latency: {cors_health['latency_ms']}ms")
    health_origin = cors_health["response_headers"].get("access-control-allow-origin")
    health_cred = cors_health["response_headers"].get("access-control-allow-credentials")
    print(f"    Access-Control-Allow-Origin: {health_origin}")
    print(f"    Access-Control-Allow-Credentials: {health_cred}")
    checks.append(("CORS Actual GET (/health)", cors_health))

    # 8. Backend CORS Actual GET (/cases from Vercel Origin)
    print("\n[8] Querying CORS Actual GET (/cases) from Origin: " + fe_url)
    cors_cases = perform_probe(
        f"{be_url}/cases",
        method="GET",
        headers={"Origin": fe_url},
    )
    print(f"    Status: {cors_cases['status_code']} | Latency: {cors_cases['latency_ms']}ms")
    cases_origin = cors_cases["response_headers"].get("access-control-allow-origin")
    cases_cred = cors_cases["response_headers"].get("access-control-allow-credentials")
    print(f"    Access-Control-Allow-Origin: {cases_origin}")
    print(f"    Access-Control-Allow-Credentials: {cases_cred}")
    checks.append(("CORS Actual GET (/cases)", cors_cases))

    # 9. Backend CORS Rejection Test for Unauthorized Origin
    untrusted = "https://malicious-fraud-app.example.com"
    print("\n[9] Querying CORS Security for Unauthorized Origin: " + untrusted)
    cors_untrusted = perform_probe(
        f"{be_url}/health",
        method="OPTIONS",
        headers={
            "Origin": untrusted,
            "Access-Control-Request-Method": "GET",
        },
    )
    untrusted_origin_resp = cors_untrusted["response_headers"].get("access-control-allow-origin")
    is_blocked = (untrusted_origin_resp is None or untrusted_origin_resp != untrusted)
    print(f"    Status: {cors_untrusted['status_code']} | Latency: {cors_untrusted['latency_ms']}ms")
    print(f"    Access-Control-Allow-Origin returned: {untrusted_origin_resp}")
    print(f"    Origin Correctly Rejected: {is_blocked}")
    checks.append(("CORS Unauthorized Origin Rejection", cors_untrusted))

    # Write results
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frontend_target": fe_url,
        "backend_target": be_url,
        "results": [
            {
                "check": name,
                "url": c["url"],
                "method": c["method"],
                "status_code": c["status_code"],
                "latency_ms": c["latency_ms"],
                "success": c["success"],
                "cors_allow_origin": c["response_headers"].get("access-control-allow-origin"),
                "cors_allow_credentials": c["response_headers"].get("access-control-allow-credentials"),
                "cors_allow_methods": c["response_headers"].get("access-control-allow-methods"),
                "content_type": c["response_headers"].get("content-type"),
                "server": c["response_headers"].get("server") or c["response_headers"].get("Server"),
                "error": c["error"],
                "body_preview": c["body_preview"],
            }
            for name, c in checks
        ],
    }

    with open("diagnostic_results.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 75)
    print("DIAGNOSTIC SUITE RUN COMPLETE. Exported to diagnostic_results.json")
    print("=" * 75)


if __name__ == "__main__":
    main()
