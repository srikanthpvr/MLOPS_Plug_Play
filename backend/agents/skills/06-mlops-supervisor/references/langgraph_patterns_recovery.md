# MLOps Supervisor Reference: LangGraph Patterns & Recovery

## 1. Persistent State Checkpointing
In multi-agent MLOps systems, training a model or executing comprehensive test suites can take minutes or hours. If the process crashes or the host reboots, restarting from step 1 wastes time and cloud compute.

### MemorySaver & SqliteSaver Topology:
* Every pipeline run receives a distinct `thread_id` (e.g. `run_20261124_001`).
* Each node mutation commits a new snapshot into the checkpointer state table.
* On resumption or retry, the graph simply queries `app.get_state(config)` and continues from the exact uncommitted node.

---

## 2. Human-in-the-Loop (HITL) Interrupt Protocol
```python
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["packager_deploy"]  # Pauses execution automatically before cloud deployment
)
```

### Protocol:
1. Graph executes: `data_sentinel` $\to$ `training_node` $\to$ `eval_gate` $\to$ `security_audit`.
2. Graph halts before `packager_deploy`. State is preserved in memory/db.
3. FastAPI emits a `AWAITING_APPROVAL` WebSocket event to the React UI.
4. MLOps Engineer reviews the Challenger F1, p95 latency, and security audit in the modal.
5. If the engineer clicks **"Approve"**, the UI calls `POST /api/agents/approve/{run_id}`.
6. The backend executes `app.stream(None, config=config)`, seamlessly completing deployment.
