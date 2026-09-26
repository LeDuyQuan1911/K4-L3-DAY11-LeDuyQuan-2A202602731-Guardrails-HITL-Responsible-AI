"""
VinBank AI Guardrails & Red-Team Demo Server
Provides interactive UI and REST APIs for demonstration and evaluation.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure repo root and src/ are in sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
OUTPUTS_DIR = REPO_ROOT / "outputs"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import guardrail logic
from guardrails.input_guardrails import detect_injection, topic_filter
from guardrails.output_guardrails import content_filter
from assignment.pipeline import is_egress_allowed
from assignment.rate_limiter import RateLimitPlugin
from core.config import ALLOWED_TOPICS, BLOCKED_TOPICS, DEMO_SECRETS

app = FastAPI(title="VinBank AI Guardrails Demo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo rate limiter instance
live_rate_limiter = RateLimitPlugin(max_requests=5, window_seconds=30)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _read_json(filename: str):
    path = OUTPUTS_DIR / filename
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": str(e)}


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.is_file():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_file)


@app.get("/api/overview")
async def get_overview():
    results = _read_json("results.json")
    attacks = _read_json("attack_results.json")
    grade = _read_json("grade_report.json")
    metrics = _read_json("metrics.json")
    audit = _read_json("audit_log.json")

    return {
        "status": "active",
        "has_results": results is not None,
        "has_attacks": attacks is not None,
        "has_grade": grade is not None,
        "technical_failure": grade.get("technical_failure", False) if grade else False,
        "summary": {
            "safe_queries": len(results.get("safe_queries", [])) if results else 0,
            "attack_queries": len(results.get("attack_queries", [])) if results else 0,
            "edge_cases": len(results.get("edge_cases", [])) if results else 0,
            "audit_logs_count": len(audit) if isinstance(audit, list) else 0,
            "rate_limit_stats": results.get("rate_limit", {}) if results else {},
            "red_team_stats": (attacks.get("summary", {}) if attacks else {}),
        },
        "allowed_topics": ALLOWED_TOPICS,
        "blocked_topics": BLOCKED_TOPICS,
        "protected_secrets": DEMO_SECRETS,
    }


@app.get("/api/results")
async def get_results():
    data = _read_json("results.json")
    if not data:
        raise HTTPException(status_code=404, detail="results.json not found")
    return data


@app.get("/api/attacks")
async def get_attacks():
    combined = _read_json("attack_results.json")
    unsafe = _read_json("unsafe_attack_result.json")
    guards = _read_json("guards_attack_result.json")
    return {
        "combined": combined,
        "unsafe": unsafe,
        "guards": guards,
    }


@app.get("/api/audit")
async def get_audit():
    data = _read_json("audit_log.json")
    if data is None:
        raise HTTPException(status_code=404, detail="audit_log.json not found")
    return data


@app.get("/api/metrics")
async def get_metrics():
    data = _read_json("metrics.json")
    if data is None:
        raise HTTPException(status_code=404, detail="metrics.json not found")
    return data


@app.get("/api/grade")
async def get_grade():
    grade = _read_json("grade_report.json")
    lab_report_path = OUTPUTS_DIR / "lab_report.md"
    report_md = ""
    if lab_report_path.is_file():
        report_md = lab_report_path.read_text(encoding="utf-8")
    return {
        "report": grade,
        "markdown": report_md,
    }


class LiveTestRequest(BaseModel):
    prompt: str
    destination: Optional[str] = "https://api.vinbank.example/v1/transfers"
    user_id: Optional[str] = "demo_user"


@app.post("/api/live-test")
async def live_test(req: LiveTestRequest):
    prompt = req.prompt.strip()

    # 1. Injection test
    injection_status = detect_injection(prompt)

    # 2. Topic filter test
    topic_status = topic_filter(prompt)

    # 3. Simulate bot response
    if injection_status == "BLOCK":
        simulated_response = (
            "Yêu cầu của bạn bị từ chối do vi phạm chính sách an toàn bảo mật của VinBank. "
            "Trợ lý ảo chỉ có thể giải đáp các nghiệp vụ ngân hàng hợp lệ."
        )
        layer_blocked = "Input Injection Filter"
    elif topic_status == "BLOCK":
        simulated_response = (
            "Tôi là trợ lý ảo của Ngân hàng VinBank và chỉ có thể hỗ trợ các nghiệp vụ ngân hàng."
        )
        layer_blocked = "Topic Filter"
    else:
        # Allowed banking query simulation
        simulated_response = (
            f"Cảm ơn quý khách đã liên hệ Ngân hàng VinBank. Về câu hỏi: '{prompt}', "
            "lãi suất tiền gửi tiết kiệm kỳ hạn 12 tháng hiện tại là 4.25%/năm. "
            "Tổng đài CSKH: 0901234567 hoặc email: support@vinbank.com."
        )
        layer_blocked = None

    # 4. Output filter
    output_analysis = content_filter(simulated_response)

    # 5. Egress policy check
    egress_allowed = is_egress_allowed(req.destination or "", prompt)

    return {
        "input": prompt,
        "injection_detection": {
            "status": injection_status,
            "verdict": "BLOCKED" if injection_status == "BLOCK" else "PASSED",
        },
        "topic_filter": {
            "status": topic_status,
            "verdict": "BLOCKED" if topic_status == "BLOCK" else "PASSED",
        },
        "overall_input_decision": (
            "BLOCKED" if (injection_status == "BLOCK" or topic_status == "BLOCK") else "ALLOWED"
        ),
        "blocking_layer": layer_blocked,
        "raw_response": simulated_response,
        "output_guardrail": {
            "safe": output_analysis["safe"],
            "issues_detected": output_analysis["issues"],
            "final_redacted_response": output_analysis["redacted"],
        },
        "egress_check": {
            "destination": req.destination,
            "allowed": egress_allowed,
            "reason": (
                "Tên miền hợp lệ nằm trong allowlist của VinBank (HTTPS) và dữ liệu an toàn"
                if egress_allowed
                else "Bị từ chối: Tên miền không được cấp phép hoặc payload chứa dữ liệu nhạy cảm"
            ),
        },
    }


class RateLimitTestRequest(BaseModel):
    user_id: str = "spammer_demo"
    request_count: int = 8


@app.post("/api/rate-limit-test")
async def test_rate_limit(req: RateLimitTestRequest):
    limiter = RateLimitPlugin(max_requests=5, window_seconds=20)

    class _MockCtx:
        def __init__(self, uid):
            self.user_id = uid

    class _MockContent:
        def __init__(self, text):
            self.parts = [type("Part", (), {"text": text})()]

    results = []
    for i in range(1, req.request_count + 1):
        res = await limiter.on_user_message_callback(
            invocation_context=_MockCtx(req.user_id),
            user_message=_MockContent(f"Query #{i}"),
        )
        blocked = res is not None
        results.append(
            {
                "request_num": i,
                "blocked": blocked,
                "message": (
                    "Vượt quá giới hạn tần suất cho phép (Tối đa 5 requests / 20s)."
                    if blocked
                    else "ĐƯỢC PHÉP chuyển tới LLM xử lý"
                ),
            }
        )

    return {
        "user_id": req.user_id,
        "max_requests": 5,
        "window_seconds": 20,
        "total_sent": req.request_count,
        "passed": sum(1 for r in results if not r["blocked"]),
        "blocked": sum(1 for r in results if r["blocked"]),
        "details": results,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_demo.app:app", host="127.0.0.1", port=8000, reload=True)
