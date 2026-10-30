import hmac
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from .services import fetch_pokemon, PokemonAPIError

TEST_SUITES = {
    "all": ["pokemon/tests"],
    "unit": ["pokemon/tests/test_utils.py", "pokemon/tests/test_validation.py"],
    "api": ["pokemon/tests/test_api.py", "pokemon/tests/test_http_methods.py", "pokemon/tests/test_runner.py"],
    "mocks": ["pokemon/tests/test_services.py"],
}
PYTEST_LOCK = threading.Lock()

def home(request):
    return render(request, "pokemon/home.html")

def learn(request):
    return render(request, "pokemon/learn.html")

def lab(request):
    return render(request, "pokemon/lab.html")

def coverage_page(request):
    return render(request, "pokemon/coverage.html")

@require_GET
def pokemon_api(request, name):
    try:
        return JsonResponse({"ok": True, "pokemon": fetch_pokemon(name)})
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=404)
    except PokemonAPIError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=502)

def _parse_pytest_summary(output):
    summary = {}
    patterns = {
        "passed": r"(\\d+) passed",
        "failed": r"(\\d+) failed",
        "errors": r"(\\d+) error",
        "skipped": r"(\\d+) skipped",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        summary[key] = int(match.group(1)) if match else 0
    return summary

def _execute_pytest(suite):
    if not PYTEST_LOCK.acquire(blocking=False):
        return JsonResponse({"ok": False, "error": "Another test run is already in progress. Try again shortly."}, status=409)

    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="poketest-coverage-") as temp_dir:
            report_path = str(Path(temp_dir) / "coverage.json")
            command = [
                sys.executable, "-m", "pytest", *TEST_SUITES[suite],
                "-q", "--tb=short", "--cov=pokemon",
                f"--cov-report=json:{report_path}", "--cov-report=term-missing",
            ]
            try:
                completed = subprocess.run(
                    command,
                    cwd=Path(settings.BASE_DIR),
                    capture_output=True,
                    text=True,
                    timeout=60,
                    shell=False,
                )
            except subprocess.TimeoutExpired as exc:
                partial = exc.stdout or ""
                if isinstance(partial, bytes):
                    partial = partial.decode("utf-8", errors="replace")
                return JsonResponse({
                    "ok": False,
                    "timed_out": True,
                    "duration": round(time.perf_counter() - started, 2),
                    "output": str(partial) + "\\nTest execution exceeded the 60-second limit.",
                }, status=408)
            except OSError as exc:
                return JsonResponse({"ok": False, "error": f"Could not start pytest: {exc}"}, status=500)

            output = (completed.stdout + "\\n" + completed.stderr).strip()
            coverage = None
            try:
                with open(report_path, encoding="utf-8") as report_file:
                    coverage = round(json.load(report_file)["totals"]["percent_covered"], 1)
            except (OSError, KeyError, TypeError, json.JSONDecodeError):
                pass

            return JsonResponse({
                "ok": completed.returncode == 0,
                "suite": suite,
                "exit_code": completed.returncode,
                "duration": round(time.perf_counter() - started, 2),
                "coverage": coverage,
                "summary": _parse_pytest_summary(output),
                "output": output[-18000:],
            })
    finally:
        PYTEST_LOCK.release()

@require_POST
def run_tests_api(request):
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request body."}, status=400)

    suite = payload.get("suite", "all")
    if suite not in TEST_SUITES:
        return JsonResponse({"ok": False, "error": "Unknown test suite."}, status=400)

    # In production, require a private access code stored only in the host's environment.
    if not settings.DEBUG:
        import os
        expected_code = os.environ.get("POKETEST_RUNNER_ACCESS_CODE", "").strip()
        supplied_code = payload.get("access_code", "")
        if not expected_code:
            return JsonResponse({
                "ok": False,
                "error": "The online runner is not configured yet. Add POKETEST_RUNNER_ACCESS_CODE in Render."
            }, status=503)
        if not isinstance(supplied_code, str) or not hmac.compare_digest(supplied_code, expected_code):
            return JsonResponse({"ok": False, "error": "Incorrect trainer access code."}, status=403)

        now = time.time()
        previous = request.session.get("poketest_last_run", 0)
        if now - previous < 30:
            return JsonResponse({"ok": False, "error": "Please wait 30 seconds between test runs."}, status=429)
        request.session["poketest_last_run"] = now

    return _execute_pytest(suite)
