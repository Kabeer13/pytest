import hmac, io, json, os, re, subprocess, sys, tempfile, threading, time, uuid, zipfile
from pathlib import Path
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from .services import fetch_pokemon, PokemonAPIError

REPO = "Kabeer13/pytest"
WORKFLOW = "pytest-remote.yml"
GH_API = "https://api.github.com"
SUITES = {
    "all": ["pokemon/tests"],
    "unit": ["pokemon/tests/test_utils.py", "pokemon/tests/test_validation.py"],
    "api": ["pokemon/tests/test_api.py", "pokemon/tests/test_http_methods.py", "pokemon/tests/test_runner.py"],
    "mocks": ["pokemon/tests/test_services.py"],
}
LOCAL_LOCK = threading.Lock()

def home(request): return render(request, "pokemon/home.html")
def learn(request): return render(request, "pokemon/learn.html")
def lab(request): return render(request, "pokemon/lab.html")
def coverage_page(request): return render(request, "pokemon/coverage.html")

@require_GET
def pokemon_api(request, name):
    try:
        return JsonResponse({"ok": True, "pokemon": fetch_pokemon(name)})
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=404)
    except PokemonAPIError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=502)

def _summary(output):
    result = {}
    for key, pattern in {"passed": r"(\d+) passed", "failed": r"(\d+) failed",
                         "errors": r"(\d+) error", "skipped": r"(\d+) skipped"}.items():
        match = re.search(pattern, output)
        result[key] = int(match.group(1)) if match else 0
    return result

def _local_run(suite):
    if not LOCAL_LOCK.acquire(blocking=False):
        return JsonResponse({"ok": False, "error": "A test run is already in progress."}, status=409)
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            report = str(Path(tmp) / "coverage.json")
            cmd = [sys.executable, "-m", "pytest", *SUITES[suite], "-q", "--tb=short",
                   "--cov=pokemon", f"--cov-report=json:{report}", "--cov-report=term"]
            try:
                proc = subprocess.run(cmd, cwd=settings.BASE_DIR, capture_output=True,
                                      text=True, timeout=90, shell=False)
            except subprocess.TimeoutExpired:
                return JsonResponse({"ok": False, "timed_out": True, "error": "Tests exceeded 90 seconds."}, status=408)
            output = (proc.stdout + "\n" + proc.stderr).strip()
            coverage = None
            try: coverage = round(json.loads(Path(report).read_text())["totals"]["percent_covered"], 1)
            except (OSError, KeyError, TypeError, json.JSONDecodeError): pass
            return JsonResponse({"ok": proc.returncode == 0, "mode": "local", "exit_code": proc.returncode,
                "suite": suite, "duration": round(time.perf_counter()-started, 2), "coverage": coverage,
                "summary": _summary(output), "output": output[-18000:]})
    finally:
        LOCAL_LOCK.release()

def _gh_headers():
    token = os.environ.get("GITHUB_ACTIONS_TOKEN", "").strip()
    if not token: return None
    return {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"}

@require_POST
def run_tests_api(request):
    try: payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request body."}, status=400)
    suite = payload.get("suite", "all")
    if suite not in SUITES:
        return JsonResponse({"ok": False, "error": "Unknown test suite."}, status=400)
    if settings.DEBUG:
        return _local_run(suite)

    expected = os.environ.get("POKETEST_RUNNER_ACCESS_CODE", "").strip()
    supplied = payload.get("access_code", "")
    if not expected:
        return JsonResponse({"ok": False, "error": "Online runner is not configured. Add its secrets in Render."}, status=503)
    if not isinstance(supplied, str) or not hmac.compare_digest(supplied, expected):
        return JsonResponse({"ok": False, "error": "Incorrect trainer access code."}, status=403)
    headers = _gh_headers()
    if not headers:
        return JsonResponse({"ok": False, "error": "Missing GITHUB_ACTIONS_TOKEN in Render."}, status=503)
    now = time.time()
    if now - request.session.get("poketest_last_dispatch", 0) < 30:
        return JsonResponse({"ok": False, "error": "Please wait 30 seconds between test runs."}, status=429)
    request_id = uuid.uuid4().hex
    url = f"{GH_API}/repos/{REPO}/actions/workflows/{WORKFLOW}/dispatches"
    try:
        response = requests.post(url, headers=headers,
            json={"ref": "main", "inputs": {"suite": suite, "request_id": request_id}}, timeout=15)
    except requests.RequestException:
        return JsonResponse({"ok": False, "error": "Could not contact GitHub Actions."}, status=502)
    if response.status_code != 204:
        return JsonResponse({"ok": False,
            "error": "GitHub rejected the run. Check token Actions read/write access and enable Actions in the repository.",
            "github_status": response.status_code}, status=502)
    request.session["poketest_last_dispatch"] = now
    request.session["poketest_run_id"] = request_id
    request.session["poketest_run_suite"] = suite
    return JsonResponse({"ok": True, "remote": True, "request_id": request_id, "status": "queued", "suite": suite}, status=202)

@require_GET
def run_tests_status_api(request, request_id):
    if request.session.get("poketest_run_id") != request_id:
        return JsonResponse({"ok": False, "error": "This run does not belong to this browser session."}, status=403)
    headers = _gh_headers()
    if not headers:
        return JsonResponse({"ok": False, "error": "GitHub Actions token is missing."}, status=503)
    suite = request.session.get("poketest_run_suite", "all")
    url = f"{GH_API}/repos/{REPO}/actions/workflows/{WORKFLOW}/runs"
    try:
        response = requests.get(url, headers=headers,
            params={"event": "workflow_dispatch", "branch": "main", "per_page": 20}, timeout=15)
        response.raise_for_status()
        runs = response.json().get("workflow_runs", [])
    except (requests.RequestException, ValueError):
        return JsonResponse({"ok": False, "error": "Could not retrieve GitHub Actions status."}, status=502)
    run = next((item for item in runs if request_id in str(item.get("display_title", "")) or
                request_id in str(item.get("name", ""))), None)
    if not run:
        return JsonResponse({"ok": True, "status": "queued", "suite": suite, "message": "Waiting for GitHub Actions…"})
    status = run.get("status", "queued")
    data = {"ok": True, "status": status, "suite": suite, "run_url": run.get("html_url")}
    if status != "completed": return JsonResponse(data)
    data["conclusion"] = run.get("conclusion")
    data["passed_run"] = run.get("conclusion") == "success"
    try:
        aurl = f"{GH_API}/repos/{REPO}/actions/runs/{run['id']}/artifacts"
        ar = requests.get(aurl, headers=headers, timeout=15)
        ar.raise_for_status()
        artifact = next((a for a in ar.json().get("artifacts", [])
                         if a.get("name") == f"poketest-results-{request_id}"), None)
        if artifact:
            zr = requests.get(artifact["archive_download_url"], headers=headers, timeout=30)
            zr.raise_for_status()
            if len(zr.content) <= 8 * 1024 * 1024:
                with zipfile.ZipFile(io.BytesIO(zr.content)) as zf:
                    names = {Path(n).name: n for n in zf.namelist()}
                    if "pytest-output.txt" in names:
                        data["output"] = zf.read(names["pytest-output.txt"]).decode("utf-8", errors="replace")[-18000:]
                    if "result.json" in names:
                        result = json.loads(zf.read(names["result.json"]).decode("utf-8"))
                        for key in ("summary", "coverage", "duration", "exit_code"):
                            data[key] = result.get(key)
    except (requests.RequestException, ValueError, KeyError, zipfile.BadZipFile):
        data["output"] = "Run finished, but the report artifact could not be retrieved. Open GitHub Actions to inspect logs."
    return JsonResponse(data)
