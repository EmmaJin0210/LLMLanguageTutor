# LLM Tutor

## Repository Structure

- **`LanguageTutor_v1/`**
  - **`core/`**  
    Core system functionality, including generation engines, model wrappers, and difficulty control modules.
  - **`appstuff/`**  
    Supporting assets and modules for the web interface.
  - **`db/`**  
    Language data and corpora, including vocabulary lists and training resources.
  - **`app.py` & `app_terminal.py`**  
    Main web application and a terminal version for running local experiments or debugging.

- **`eval/`**  
  Evaluation pipeline scripts, including automatic metric evaluation and user study analysis.


## Adding a Custom Controlled-Generation Engine
### 1) Add your engine

Create a file:

```
LanguageTutor_v1/core/engines/<your_engine>.py
```

Minimal template:

```python
from typing import List, Dict, Optional, Any

class MyEngine:
    """Implement a controlled-generation method."""
    def __init__(self, **kwargs):
        # Optional: receive shared resources (e.g., llm_fn, vocab, configs)
        self.kwargs = kwargs

    def generate(
        self,
        history: List[Dict[str, str]],   # [{"role":"user|assistant","content":"..."}]
        target_level: str,               # e.g., "N5", "A1"
        control_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Return a single tutor reply string
        last_user = next((m["content"] for m in reversed(history) if m.get("role")=="user"), "")
        return f"[MyEngine @ {target_level}] {last_user}"
```

### 2) Run with your engine

```bash
python LanguageTutor_v1/app_terminal.py \
  --engine <your_engine>:MyEngine \
  --level N5
```

### 3) Engine contract

Your class must implement:

```python
def generate(self, history: List[dict], target_level: str, control_params: dict) -> str
```

- `history`: full conversation history (role/content)
- `target_level`: desired difficulty (e.g., "N5" / "A1")
- `control_params`: optional method-specific knobs (e.g., `{"lambda": 0.8}`)

`__init__(**kwargs)` may accept shared resources if provided by the caller (e.g., `llm_fn`, vocab/TMR helpers).

