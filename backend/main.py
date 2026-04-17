from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import subprocess
import json
import os
import uuid
import sys
import asyncio
import threading
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
REPORT_SCRIPT = os.path.join(SCRIPT_DIR, "cli_handler.py")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "reports")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Stores report_id -> nro_informe for download filename
REPORT_META = {}

print(f"[Backend] Script: {REPORT_SCRIPT}")
print(f"[Backend] Reports dir: {OUTPUT_DIR}")


class GenerateRequest(BaseModel):
    api_key: str
    report_data: dict
    nro_informe: str = "[COMPLETAR]"
    institucion: List[str] = [
        "Area de Inteligencia e Integridad",
        "Instituto de Investigacion Cientifica",
        "Universidad de Lima"
    ]


# ═══════════════════════════════════════════════════════════════════════════
#  WEBSOCKET — Real-time data collection
# ═══════════════════════════════════════════════════════════════════════════
@app.websocket("/ws/collect")
async def ws_collect(websocket: WebSocket):
    await websocket.accept()
    print("\n[WS] Client connected")
    process = None

    try:
        # 1. Receive params from client
        raw = await websocket.receive_text()
        params = json.loads(raw)
        params["mode"] = "collect"
        print(f"[WS] Collecting: eissn={params.get('eissn')}")

        # 2. Start subprocess
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONPATH"] = ROOT_DIR

        process = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: subprocess.Popen(
                [sys.executable, "-u", REPORT_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                bufsize=0,
            )
        )

        # Write params and close stdin
        process.stdin.write(json.dumps(params).encode("utf-8"))
        process.stdin.close()

        # 3. Read stdout line by line and send each as a WS message
        def read_lines(proc):
            """Generator that yields lines from subprocess stdout."""
            for raw_line in proc.stdout:
                try:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                except:
                    line = raw_line.decode("latin-1", errors="replace").strip()
                if line:
                    yield line

        loop = asyncio.get_event_loop()

        # Use a thread to read from subprocess (blocking IO) and push to asyncio queue
        queue = asyncio.Queue()

        def reader_thread():
            try:
                for line in read_lines(process):
                    loop.call_soon_threadsafe(queue.put_nowait, line)
            except Exception as e:
                loop.call_soon_threadsafe(queue.put_nowait, f"__ERROR__:{e}")
            finally:
                process.wait()
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        threading.Thread(target=reader_thread, daemon=True).start()

        # 4. Consume queue and send each message over WebSocket
        async def listen_for_disconnect():
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                pass
            except Exception:
                pass

        disconnect_task = asyncio.create_task(listen_for_disconnect())

        while True:
            get_task = asyncio.create_task(queue.get())
            done, pending = await asyncio.wait(
                [get_task, disconnect_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            if disconnect_task in done:
                get_task.cancel()
                print("[WS] Client disconnected. Aborting collection.")
                break

            line = await get_task
            if line is None:
                disconnect_task.cancel()
                break

            print(f"[Script] {line}", flush=True)

            try:
                if line.startswith("DATA:"):
                    data = json.loads(line[5:])
                    msg = {"type": "data", "key": data.get("_key", "unknown"), "content": data}
                elif line.startswith("STEP:"):
                    msg = {"type": "step", "content": line[5:]}
                elif line.startswith("INFO:"):
                    msg = {"type": "info", "content": line[5:]}
                elif line.startswith("WARN:"):
                    msg = {"type": "warn", "content": line[5:]}
                elif line.startswith("COLLECT_DONE:"):
                    data = json.loads(line[13:])
                    msg = {"type": "collect_done", "content": data}
                elif line.startswith("__ERROR__:"):
                    msg = {"type": "error", "content": line[10:]}
                else:
                    msg = {"type": "log", "content": line[:200]}

                await websocket.send_json(msg)
            except Exception as send_err:
                print(f"[WS] Send error: {send_err}")
                break

        # 5. Check exit code
        if process.returncode != 0:
            stderr_out = process.stderr.read().decode("utf-8", errors="replace")
            print(f"[WS] Script error: {stderr_out[:500]}")
            await websocket.send_json({"type": "error", "content": stderr_out[:500]})
        else:
            print("[WS] Collection completed successfully")
            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS] Exception: {e}")
        try:
            await websocket.send_json({"type": "error", "content": str(e)})
        except:
            pass
    finally:
        if process and process.poll() is None:
            print("[WS] Terminating lingering subprocess...")
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
        try:
            await websocket.close()
        except:
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  POST — Generate Word from reviewed data
# ═══════════════════════════════════════════════════════════════════════════
@app.post("/generate-docx")
async def generate_docx(request: GenerateRequest):
    report_id = str(uuid.uuid4())
    output_path = os.path.join(OUTPUT_DIR, f"informe_{report_id}.docx")
    print(f"\n[Backend] === GENERATE-DOCX request ===")
    print(f"[Backend] report_id={report_id}")

    params = {
        "mode": "generate",
        "api_key": request.api_key,
        "report_data": request.report_data,
        "nro_informe": request.nro_informe,
        "institucion": request.institucion,
        "output_file": output_path,
    }

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = ROOT_DIR

    try:
        process = subprocess.Popen(
            [sys.executable, "-u", REPORT_SCRIPT],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        stdout_raw, stderr_raw = process.communicate(input=json.dumps(params).encode("utf-8"))
        stdout = stdout_raw.decode("utf-8", errors="replace")
        stderr = stderr_raw.decode("utf-8", errors="replace")

        for line in stdout.splitlines():
            if line.strip():
                print(f"[Script] {line.strip()}", flush=True)

        if process.returncode != 0:
            print(f"[Backend] Script error: {stderr[:500]}")
            raise HTTPException(status_code=500, detail=f"Error: {stderr[:500]}")

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Output file was not created.")

        print(f"[Backend] Word file created at {output_path}")
        REPORT_META[report_id] = request.nro_informe
        return {"report_id": report_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Backend] Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-docx/{report_id}")
async def download_report(report_id: str):
    path = os.path.join(OUTPUT_DIR, f"informe_{report_id}.docx")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Report not found")
    print(f"[Backend] Downloading report {report_id}")
    nro = REPORT_META.get(report_id, report_id)
    safe_nro = nro.replace('/', '-').replace('\\', '-')
    return FileResponse(
        path,
        filename=f"Informe N° IDIC-IQInteg-R-{safe_nro}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


if __name__ == "__main__":
    import uvicorn
    print("[Backend] Starting server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
