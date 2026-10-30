from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings
from .services import fetch_pokemon, PokemonAPIError
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

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
        pokemon = fetch_pokemon(name)
        return JsonResponse({"ok": True, "pokemon": pokemon})
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=404)
    except PokemonAPIError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=502)

_pytest_run_lock = threading.Lock()

@require_POST
def run_tests_api(request):
    if not settings.DEBUG:
        return JsonResponse({"ok": False, "error": "The interactive test runner is local-development only."}, status=403)
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request body."}, status=400)
    suites = {
        "all": ["pokemon/tests"],
        "unit": ["pokemon/tests/test_utils.py", "pokemon/tests/test_validation.py"],
        "api": ["pokemon/tests/test_api.py", "pokemon/tests/test_http_methods.py"],
        "mocks": ["pokemon/tests/test_services.py"],
    }
    suite = payload.get("suite", "all")
    if suite not in suites:
        return JsonResponse({"ok": False, "error": "Unknown test suite."}, status=400)
    if not _pytest_run_lock.acquire(blocking=False):
        return JsonResponse({"ok": False, "error": "A test run is already in progress."}, status=409)
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="poketest-coverage-") as temp_dir:
            report_path = str(Path(temp_dir) / "coverage.json")
            command = [sys.executable, "-m", "pytest", *suites[suite], "-q", "--tb=short",
                       "--cov=pokemon", f"--cov-report=json:{report_path}", "--cov-report=term"]
            try:
                result = subprocess.run(command, cwd=Path(settings.BASE_DIR), capture_output=True,
                                        text=True, timeout=90, shell=False)
            except subprocess.TimeoutExpired as exc:
                partial = exc.stdout or ""
                if isinstance(partial, bytes):
                    partial = partial.decode("utf-8", errors="replace")
                return JsonResponse({"ok": False, "timed_out": True, "output": str(partial) + "\nTest run exceeded 90 seconds.",
                                     "duration": round(time.perf_counter() - started, 2)}, status=408)
            output = (result.stdout + "\n" + result.stderr).strip()
            coverage = None
            try:
                with open(report_path, encoding="utf-8") as report_file:
                    coverage = round(json.load(report_file)["totals"]["percent_covered"], 1)
            except (OSError, KeyError, TypeError, json.JSONDecodeError):
                pass
            summary = {}
            for key, pattern in {"passed": r"(\d+) passed", "failed": r"(\d+) failed",
                                 "errors": r"(\d+) error", "skipped": r"(\d+) skipped"}.items():
                match = re.search(pattern, output)
                summary[key] = int(match.group(1)) if match else 0
            return JsonResponse({"ok": result.returncode == 0, "exit_code": result.returncode,
                                 "suite": suite, "duration": round(time.perf_counter() - started, 2),
                                 "coverage": coverage, "summary": summary, "output": output[-18000:]})
    finally:
        _pytest_run_lock.release()
