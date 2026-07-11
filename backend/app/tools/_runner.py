import asyncio
import time
from typing import Optional
from .base import ToolResult, ToolCategory


def _make_result(
    tool_name: str,
    category: ToolCategory,
    status: str,
    raw_data: Optional[dict] = None,
    normalized: Optional[list] = None,
    error: Optional[str] = None,
    duration_ms: int = 0,
) -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        category=category,
        status=status,
        raw_data=raw_data or {},
        normalized=normalized or [],
        error=error,
        duration_ms=duration_ms,
    )


async def run_cli(
    tool_name: str,
    category: ToolCategory,
    args: list[str],
    timeout: int = 60,
) -> ToolResult:
    start = time.monotonic()
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            elapsed = int((time.monotonic() - start) * 1000)
            return _make_result(tool_name, category, "error", error="Timed out", duration_ms=elapsed)

        elapsed = int((time.monotonic() - start) * 1000)
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")

        if proc.returncode != 0:
            return _make_result(
                tool_name, category, "error",
                raw_data={"stdout": stdout_str, "stderr": stderr_str, "returncode": proc.returncode},
                error=stderr_str[:500] or f"Exit code {proc.returncode}",
                duration_ms=elapsed,
            )

        return _make_result(
            tool_name, category, "success",
            raw_data={"stdout": stdout_str, "stderr": stderr_str},
            duration_ms=elapsed,
        )
    except FileNotFoundError:
        elapsed = int((time.monotonic() - start) * 1000)
        return _make_result(
            tool_name, category, "error",
            error=f"'{args[0]}' not found. Install it first.",
            duration_ms=elapsed,
        )
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return _make_result(tool_name, category, "error", error=str(e), duration_ms=elapsed)
