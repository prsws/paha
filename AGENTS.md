# Pepa Arm Home Agent Instructions

## Identity

Pepa Arm Home Agent (PAHA) is the sensory arm of the Pepa octopus — a self-hosted cognitive infrastructure for aging-in-place at Casa Delta. Pepa follows a Supervisor-Worker agent harness pattern; the octopus metaphor maps the Head (supervisory orchestration), the Arms (semi-autonomous agents), and the Beak (underlying infrastructure). PAHA is one arm. This repo is a fork of Anton Radlein's `hass-agent-llm`, adapted as a Home Assistant (HA) custom component installed via HACS.

PAHA is a **constrained semantic translator**. Its job is to map open, code-switched (English/Spanish/Spanglish) utterances to one of four outputs:

- A validated HA action call (query or execute)
- A clarifying question
- An escalation to the orchestration head
- A no-op

PAHA is **not** a chatbot, reasoner, knowledge source, or memory store.

Those responsibilities belong to other Pepa arms.

---

## Architecture

### Execution Stack

```
Utterance → Preprocessor → LLM → NeMo Guardrails → HA Service Call → Response
```

- **Preprocessor** (`helpers.py`): Deterministic. Rapidfuzz fuzzy matching (75% threshold) + Spanish/Spanglish Unicode regex + domain-to-service mapping. On a hit, emits directly. LLM and NeMo are not invoked.
- **LLM** (`agent/core.py`, `agent/llm.py`): Proposes a structured action — a tool call or clarification request. Does not execute. Current candidate: `qwen2.5:3b` via Ollama.
- **NeMo Guardrails** (`tool_handler.py`): Validates LLM proposals against behavioral policy. Sits between LLM proposal and HA dispatch. Not invoked on preprocessor hits.
- **HA** (`tools/ha_control.py`, `tools/ha_query.py`): Executes validated service calls via the HA API.
- **Response**: Returns to originating channel via the HA Assist pipeline.

### ReAct Loop & Latency Tiers

PAHA resolves through up to three tiers, taking the lowest that succeeds:

| Tier | Path | Applies when |
| --- | --- | --- |
| 1 | Preprocessor hit | Canned phrase, fuzzy match above threshold |
| 2 | Single ReAct step | Preprocessor miss, confident single-action intent |
| 3 | ReAct iteration | Tier-2 observation contradicts goal, or multi-action intent |

After Tier 3 fails within the cycle cap, PAHA escalates or returns a clarification.

System prompt bias: one confident shot or punt — not exploration.

### Channel Discrimination

Discriminated by `device_id` in `conversation_session.py`:

- `device_id` non-null → voice satellite (Wyoming STT/TTS on mmm4)
- `device_id` null → chat (HA conversation UI)

Channel determines output modality and influences response brevity.

---

## Component Map

| File | PAHA Role |
| --- | --- |
| `helpers.py` | Rapidfuzz preprocessor + Spanglish normalization (to be added) |
| `agent/core.py` | ReAct loop — inherited, tune for single-shot bias |
| `agent/llm.py` | LLM interface — retarget to qwen2.5:3b via Ollama |
| `tool_handler.py` | NeMo Guardrails hook at tool validation (to be added) |
| `tools/ha_control.py` | Primary execution tool — inherited |
| `tools/ha_query.py` | Primary query tool — inherited |
| `tools/registry.py` | Tool registry — find_skills() plugs in here (backlog) |
| `conversation.py` | Main handler — adapt for PAHA response shaping |
| `conversation_session.py` | Session management + device_id channel discrimination |
| `context_manager.py` | Context assembly — tune for entity scoping |
| `context_optimizer.py` | Token reduction — critical, do not remove or simplify |
| `vector_db_manager.py` | ChromaDB interface — retained as sleep-cycle consolidation feeder |
| `memory_manager.py` | Working memory write path — retained |
| `agent/memory_extraction.py` | Memory extraction — retained |
| `agent_prompts/` | Replace entirely with PAHA system prompt |
| `tools/external_llm.py` | Escalation path to orchestration head — retain, retarget |
| `tools/custom.py` | Deferred |

---

## Inherited vs To Be Added

### Inherited from upstream (do not break)

- HA Assist pipeline integration
- ReAct loop with internal → external LLM escalation
- HA aliases and labels as entity resolution affordances
- ChromaDB-backed conversation memory (working memory + nightly consolidation feeder)

### To be added in this fork

- Rapidfuzz preprocessor with Spanglish normalization (`helpers.py`)
- NeMo Guardrails hook at tool validation layer (`tool_handler.py`)
- Channel discrimination via `device_id` (`conversation_session.py`)
- Curated entity list injected at loop start (device/entity preprocessor)
- `find_skills(topic)` lazy skill loader — backlog, not current sprint

### Deferred

- MCP support surface — until autonomous arm operation is stable

---

## Non-Goals

The agent must never:

- Generate long-form prose responses
- Perform multi-step planning or agentic deliberation
- Consolidate long-term memory
- Synthesize knowledge from documents
- Run inference for any other Pepa arm
- Author or modify NeMo behavioral policy
- Bypass NeMo on LLM-proposed actions
- Improvise when uncertain — punt instead

---

## Verification Workflow

Order: `Lint → Typecheck → Test`

### 1. Lint & Format

- **Check**:
    - `black --check custom_components/ tests/`
    - `isort --check custom_components/ tests/`
    - `flake8 custom_components/ tests/`
- **Fix**:
    - `black custom_components/ tests/`
    - `isort custom_components/ tests/`

### 2. Typecheck

- `mypy .`

### 3. Testing

- **Unit**: `pytest tests/unit/ -v`
- **Mocked integration**: `pytest tests/integration/ -v --ignore=tests/integration/test_real_*.py`
- **Real integration**: Requires `.env.test` (copy from `.env.test.example`). Run `test_real_*.py` only when fully configured.

---

## Conventions

- **Style**: Line length 100. Black + isort enforced.
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- **Tests**: All unit and mocked integration tests must pass before PR. New code requires tests.
- **Runtime**: Python 3.13/3.14, Home Assistant 2026.3.1+.
