def new_trace(trigger: str, raw_input: str = "") -> dict:
    """Mulai trace baru untuk satu trigger user."""
    return {
        "trigger": trigger,
        "input": raw_input,
        "steps": [],
        "response_summary": "",
    }


def log_step(trace: dict | None, function_name: str, message: str, data: dict | None = None) -> None:
    """Tambahkan satu langkah proses ke trace."""
    if trace is None:
        return
    trace.setdefault("steps", []).append(
        {
            "function": function_name,
            "message": message,
            "data": data or {},
        }
    )


def finish_trace(trace: dict, response_summary: str) -> dict:
    """Tutup trace dengan ringkasan response."""
    trace["response_summary"] = response_summary
    return trace
