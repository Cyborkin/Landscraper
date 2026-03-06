Loaded cached credentials.
I will start by exploring the codebase to understand the existing project structure and any dependencies already defined in `pyproject.toml`.
For a multi-agent system like Landscraper, a custom `StateGraph` is superior to `create_react_agent` because it provides the explicit control needed to manage a complex, multi-phase lifecycle and dynamic delegation.

### 1. The State Schema (`TypedDict`)

In a delegating orchestrator pattern, your state should act as a **shared context window** that is both structured (for logic) and unstructured (for LLM reasoning history).

```python
import operator
from typing import Annotated, List, Dict, Any, Optional, TypedDict, Union
from langchain_core.messages import BaseMessage

class Lead(TypedDict):
    id: str
    source_id: str
    title: str
    location: str
    details: Dict[str, Any]
    confidence_score: float

class LandscraperState(TypedDict):
    # LLM conversation history (standard LangGraph practice)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Domain-specific state
    current_phase: str  # e.g., "discovery", "collection", "consensus"
    active_sources: List[Dict[str, Any]]
    raw_leads: Annotated[List[Lead], operator.add]
    validated_leads: List[Lead]
    
    # Strategy & Metrics
    iteration_count: int
    optimization_metrics: Dict[str, float]
    
    # Errors/Wait states
    error: Optional[str]
```

### 2. The Orchestrator Graph Definition

To handle the **dynamic delegation** to collection agents (the number of which varies by source), use LangGraph's `Send` API. This is the "map-reduce" pattern for agents.

```python
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send

# --- Node Functions ---

def orchestrator_node(state: LandscraperState):
    """
    Analyzes the current state and determines which phase to enter.
    Returns the next phase and optional instructions in messages.
    """
    # Logic to decide if we need more discovery or can move to collection
    if not state.get("active_sources"):
        return {"current_phase": "discovery"}
    return {"current_phase": "collection"}

def discovery_agent(state: LandscraperState):
    """Finds new OSINT sources for developments."""
    # Logic: Search Google/RSS/Public Records
    new_sources = [{"id": "src_1", "type": "rss", "url": "..."}] 
    return {"active_sources": new_sources}

def collection_specialist(source_data: Dict[str, Any]):
    """
    A worker node that processes a SINGLE source. 
    This is called dynamically for each source in state['active_sources'].
    """
    # Logic: Playwright/httpx scraping
    # returns a partial state update (list of leads)
    return {"raw_leads": [{"id": "lead_a", "source_id": source_data["id"], ...}]}

def consensus_layer(state: LandscraperState):
    """Validates and de-duplicates raw leads."""
    # Deduplication and scoring logic
    return {"validated_leads": state["raw_leads"], "current_phase": "delivery"}

# --- Routing Logic ---

def route_after_orchestrator(state: LandscraperState):
    if state["current_phase"] == "discovery":
        return "discovery_agent"
    elif state["current_phase"] == "collection":
        # DYNAMIC DELEGATION: Create a 'Send' for every active source
        return [Send("collection_specialist", source) for source in state["active_sources"]]
    return END

# --- Graph Assembly ---

workflow = StateGraph(LandscraperState)

workflow.add_node("orchestrator", orchestrator_node)
workflow.add_node("discovery_agent", discovery_agent)
workflow.add_node("collection_specialist", collection_specialist)
workflow.add_node("consensus", consensus_layer)

workflow.add_edge(START, "orchestrator")
workflow.add_conditional_edges(
    "orchestrator",
    route_after_orchestrator,
    {
        "discovery_agent": "discovery_agent",
        "collection_specialist": "collection_specialist",
        END: END
    }
)
workflow.add_edge("discovery_agent", "orchestrator")
workflow.add_edge("collection_specialist", "consensus")
workflow.add_edge("consensus", END)

app = workflow.compile()
```

### Answers to your specific questions:

1.  **Custom StateGraph vs. `create_react_agent`:** Use **Custom StateGraph**. It allows you to model the "weekly cycle" as a finite state machine, which is much more robust than a single LLM loop.
2.  **Schema Structuring:** Use a hybrid schema (as shown above). `Annotated[List, operator.add]` for things you want to **append** to (messages, raw leads) and standard types for things you want to **overwrite** (current_phase, validated_leads).
3.  **One Big Graph vs. Separate:** Use **one big graph with Subgraphs**. This allows you to use `Checkpointers` (e.g., `SqliteSaver`) to pause/resume the entire weekly cycle if a scraping node fails. Separate graphs via DB are harder to debug and lose the benefit of LangGraph's built-in travel/replaying features.
4.  **Nodes vs. Conditional Edges:** Use **Nodes for Phases**. Each phase should be a node (or subgraph). Use **Conditional Edges** for the "Router" logic that determines if a phase is complete or needs re-iteration.
5.  **Dynamic Delegation:** Use the `Send` object (demonstrated in `route_after_orchestrator`). This allows the Orchestrator to spawn N parallel `collection_specialist` nodes based on the `active_sources` list discovered in the previous step.

### LangGraph 0.2+ Gotchas:
-   **Immutable State:** Remember that state updates in nodes are *merged*, not replaced (unless specified). If you return `{"leads": [1]}`, and the state already had `{"leads": [2]}`, the result depends on whether you used `operator.add` in the `TypedDict`.
-   **Checkpointer Requirements:** For the system to survive restarts (essential for weekly cycles), you must compile with a `checkpointer`.
-   **Recursion Limit:** For complex multi-agent loops, you might need to increase the `recursion_limit` (default is 25) in your `app.invoke()` or `app.stream()` calls.
-   **The `Send` API:** When using `Send`, the target node (`collection_specialist`) receives ONLY the specific item passed in `Send`, not the full `LandscraperState`. It then returns a dictionary that is merged back into the main state.
