# Zombie Server Problem - Diagnosis and Resolution Log

**Date:** 2025-06-14
**Agent:** Kor'tana

## Objective
Diagnose the root cause of the recurring 'zombie server' problem (ConnectionResetError / NewConnectionError when `autonomous_goal_processor.py` tries to connect to the server at `http://127.0.0.1:8000`) and implement a permanent software solution to make the verification and launch process more resilient.

## Phase 1: Diagnosis

### 1.1. Log Review (`autonomous_processing.log`)
- **Findings:** Numerous `NewConnectionError` messages ([WinError 10061] No connection could be made because the target machine actively refused it) logged by `KortanaAutonomous` (likely `autonomous_goal_processor.py`) when attempting to connect to `http://127.0.0.1:8000/goals/`.
- **Timestamp:** Consistently on 2025-06-13 between 22:55 and 2025-06-14 00:08+.
- **Indication:** Server at `127.0.0.1:8000` was not running or not listening.

### 1.2. Log Review (`logs/awakening.log`)
- **Findings:** File was empty. No information regarding server startup success or failure.

### 1.3. Client Script Review (`scripts/autonomous_goal_processor.py`)
- **Connection Logic:** Uses `requests.get`, `requests.patch`, `requests.post` to `BASE_URL = "http://127.0.0.1:8000"`.
- **Error Handling:** Connection errors are caught, logged, and the script retries after a delay. This explains repeated client-side errors but not the server unavailability.
- **Note:** Task mentioned `ConnectionResetError`, logs show `NewConnectionError`. The latter is more indicative of the server process not being up or not listening.

### 1.4. Server Startup Script Review (`scripts/start_backend.py`)
- **Command:** `uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload`.
- **Health Check:** Basic `check_server_status()` pings `/docs` after `time.sleep(5)`.
- **Potential Weakness:** If server fails to start quickly or crashes, this check might not be sufficient. No explicit capture of Uvicorn's stdout/stderr for startup errors.

### 1.5. Secondary Server Script Review (`scripts/start_server.py`)
- **Details:** Runs Uvicorn on port 8001. Unlikely related to the issue on port 8000.

### 1.6. FastAPI App Review (`src/kortana/main.py`)
- **Setup:** Standard FastAPI application.
- **Lifespan Manager:** Starts/stops an "autonomous scheduler." Issues here could prevent FastAPI app from starting correctly.

### 1.7. Diagnostic Conclusion (Initial)
- The primary issue is the server at `127.0.0.1:8000` not being reliably available when `autonomous_goal_processor.py` starts.
- Possible causes:
    1.  **Server Startup Failure:** `src.kortana.main:app` (Uvicorn target) has internal errors preventing successful startup (e.g., issues in lifespan events, config, DB connection).
    2.  **Race Condition:** `autonomous_goal_processor.py` starts before `start_backend.py` fully initializes the server.
    3.  **Server Crash Post-Startup:** Server starts then crashes silently (from the client's perspective).

## Phase 2: Solution Design & Planning

**Goal:** Enhance the resilience of the server launch and client interaction.

**Strategy:** Improve server startup script robustness, implement better client-side server readiness checks, and ensure clear logging for startup/runtime issues.

### 2.1. Enhancements for Server Startup Script (`scripts/start_backend.py`)

1.  **Capture Uvicorn Output:**
    *   Modify `subprocess.Popen` to redirect Uvicorn's `stdout` and `stderr` to a dedicated log file (e.g., `logs/uvicorn_server.log`). This will help diagnose Uvicorn startup issues or runtime errors within the FastAPI application itself.
2.  **Improved Health Check Mechanism (`check_server_status()`):**
    *   **Target Endpoint:** Change the health check target from `/docs` to the more specific `/health` endpoint.
    *   **Retry Loop:** Implement a loop that retries the health check for a defined duration (e.g., 30-60 seconds) with a short delay between retries (e.g., 3-5 seconds).
    *   **Logging:** Log each health check attempt and its outcome.
    *   **Success Criteria:** Consider the server truly ready only after a successful response from `/health`.
3.  **Clear Exit Status:**
    *   Ensure `start_backend.py` exits with a status code 0 if the server starts successfully and is healthy, and a non-zero status code (e.g., 1) if it fails to start or the health check fails after all retries. This allows other scripts or processes to reliably determine if the server launch was successful.

### 2.2. Enhancements for Client Scripts (e.g., `scripts/autonomous_goal_processor.py`)

1.  **Initial Server Readiness Check:**
    *   Before entering its main processing loop, the client script should perform its own check for server availability (similar to the enhanced `check_server_status()` in `start_backend.py`).
    *   If the server is not available after a reasonable number of retries (e.g., 3-5 attempts over 15-30 seconds), the client should log a critical error and potentially exit or enter a much longer sleep/alert state, rather than continuously flooding logs with connection errors.
2.  **Refined Retry Logic (Optional - Lower Priority):**
    *   Consider if the existing retry logic within `requests` calls (or the custom retry loop in the client) needs adjustment (e.g., exponential backoff, maximum number of retries before a longer pause).

### 2.3. Orchestration & Process Management

1.  **Sequential Startup:**
    *   If not already in place, ensure a clear mechanism or wrapper script enforces that `autonomous_goal_processor.py` (and other critical clients) only attempt to start *after* `start_backend.py` has successfully completed and confirmed the server is healthy.
    *   This could involve `start_backend.py` creating a success flag file upon healthy startup, which other scripts check for.

### 2.4. Logging for this Task

*   All implementation steps, code changes, and verification results for this "zombie server" fix will be logged in this document (`ZOMBIE_SERVER_FIX_LOG.md`).

## Phase 3: Implementation

### 3.1. Client-Side Server Readiness Check (`scripts/autonomous_goal_processor.py`)

**Date:** 2025-06-14
**Status:** ✅ COMPLETED

**Changes Made:**

1. **Added Server Readiness Check Function:**
   - Created `check_server_readiness()` function with configurable retry logic
   - Default configuration: 10 retries with 3-second delays (total 30 seconds)
   - Targets `/health` endpoint for server health verification
   - Provides detailed logging for each attempt and outcome

2. **Integrated Check into Main Loop:**
   - Modified `run_autonomous_loop()` to call server readiness check before starting autonomous processing
   - If server is not available, the script logs a critical error and exits gracefully
   - Provides clear user guidance on how to start the server

**Implementation Details:**
- The readiness check runs synchronously before starting the async main loop
- Uses proper error handling for connection errors, timeouts, and unexpected exceptions
- Provides progressive feedback during retry attempts
- Clear success/failure messaging

**Code Changes:**
```python
def check_server_readiness(max_retries=10, retry_delay=3):
    # Server readiness check with retry logic and detailed logging
    # Returns True if server is ready, False otherwise

async def run_autonomous_loop(self):
    # Added server readiness check before main processing loop
    if not check_server_readiness():
        # Critical error logging and graceful exit
```

**Expected Behavior:**
- Before entering autonomous processing, the client verifies server availability
- Eliminates the "zombie server" problem by preventing client startup when server is down
- Reduces log noise from repeated connection failures
- Provides clear user feedback on server status

### 3.2. Next Steps

**Pending Tasks:**
1. **Test the Implementation:**
   - Verify server readiness check works when server is running
   - Verify graceful exit when server is not available
   - Confirm no more connection error spam in logs

2. **Clean Up Lint Issues:**
   - Remove unused variables identified during implementation
   - Address any remaining code quality issues

**Future Enhancements (Optional):**
- Consider adding a "wait for server" mode instead of immediate exit
- Add configuration file for retry parameters
- Implement exponential backoff for retry delays

## Phase 4: Verification

*(To be filled in after testing)*
