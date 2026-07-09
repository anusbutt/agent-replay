"""record_state_change() — records a state_change step (per docs/DATA_CONTRACT.md
payload shape). Never raises into host code (constitution V).
"""


def record_state_change(from_state: str, to_state: str, trigger: str) -> None:
    try:
        import agentreplay

        state = agentreplay._state
        if state is None:
            return  # no active run — stay invisible

        payload = {"from_state": from_state, "to_state": to_state, "trigger": trigger}
        state.buffer.add_step("state_change", payload, payload)
        if state.buffer.pending_count() >= agentreplay.AUTO_FLUSH_THRESHOLD:
            agentreplay.flush()
    except Exception as exc:  # noqa: BLE001 — recording must never raise into host code
        try:
            import agentreplay

            agentreplay._logger.warning("agentreplay: failed to record state_change: %s", exc)
        except Exception:  # noqa: BLE001
            pass
