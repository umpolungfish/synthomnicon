# Quick Start Guide

Get your first high-performance multi-provider agent running in 5 minutes.

## 1. Setup (1 minute)

We recommend using `uv` for lightning-fast dependency management.

```bash
# Create a virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Set API keys for desired providers
export ANTHROPIC_API_KEY="your-anthropic-key-here"
export GOOGLE_API_KEY="your-google-key-here"
export QWEN_API_KEY="your-qwen-key-here"
export MISTRAL_API_KEY="your-mistral-key-here"
export DEEPSEEK_API_KEY="your-deepseek-key-here"
```

## 2. Create Your First Async Multi-Provider Agent (2 minutes)

Create `my_agent.py`:

```python
from framework import BaseAgent
from typing import Dict, Any, Optional

class MyFirstAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(
            agent_id="my_first_agent",
            name="My First Multi-Provider Agent",
            description="My first agent with multi-LLM support",
            capabilities=["research", "analysis"],
            config=config
        )

    async def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raw = await self.call_llm(
            prompt=f"Task: {task}",
            max_tokens=self.config.get("max_tokens", 2000),
            temperature=0.7
        )
        # Strip markdown blocks, reasoning tags, and formatting noise
        response_text = self.clean_response(raw)

        return {
            "status": "success",
            "findings": response_text,
            "metadata": {
                "task": task,
                "provider": self.config.get("provider", "anthropic")
            }
        }
```

## 3. Run It with Different Providers (1 minute)

Create `run.py`:

```python
import asyncio
from my_agent import MyFirstAgent
from synthomnicon.provider_config import build_agent_config

async def main():
    # Use config-driven defaults (model=None uses provider default)
    config = build_agent_config(provider="anthropic", model=None)

    agent = MyFirstAgent(config)
    result = await agent.run("Explain what multi-agent systems are in 3 bullet points")

    print(f"Using provider: {result['metadata']['provider']}")
    print(result["findings"])

if __name__ == "__main__":
    asyncio.run(main())
```

```bash
python run.py
```

## 4. Autonomous Tool Use (1 minute)

AjintK supports an autonomous "Thinking/Acting" loop. The agent calls tools, gets results, and iterates until it reaches a final answer.

```python
from framework import BaseAgent, ToolDefinitions

class ToolAgent(BaseAgent):
    def get_tools(self):
        return [
            ToolDefinitions.run_command(),
            ToolDefinitions.file_write(),
            ToolDefinitions.list_directory(),
        ]

    async def run(self, task: str, context=None):
        findings = await self.execute_with_tools(task)
        return {"status": "success", "findings": findings}
```

## 5. Pipeline Presets

Define named multi-stage workflows once and invoke them by name:

```python
import asyncio
from framework import AgentOrchestrator
from my_agent import MyFirstAgent
from synthomnicon.provider_config import build_agent_config

async def main():
    # Use config-driven defaults
    config = build_agent_config(provider="anthropic", model=None)

    orchestrator = AgentOrchestrator({"max_concurrent_agents": 5})
    orchestrator.register_agent("researcher", MyFirstAgent(config))
    orchestrator.register_agent("analyst",    MyFirstAgent(config))
    orchestrator.register_agent("reporter",   MyFirstAgent(config))

    # Register named presets
    orchestrator.register_preset("full",  ["researcher", "analyst", "reporter"])
    orchestrator.register_preset("quick", ["researcher", "reporter"])

    # Run the "full" preset — each stage sees ALL prior outputs
    result = await orchestrator.run_preset("full", task="Analyze AI agent frameworks")

    print(f"Status: {result['status']}")
    print(f"Stages completed: {result['stages_completed']}")
    for stage in result["pipeline_results"]:
        print(f"  Stage {stage['stage']} ({stage['agent_id']}): {stage['result']['status']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## 6. Parallel Swarms

```python
import asyncio
from framework import AgentOrchestrator
from my_agent import MyFirstAgent

async def run_swarm():
    orchestrator = AgentOrchestrator({"max_concurrent_agents": 10})

    orchestrator.register_agent("researcher", MyFirstAgent({"provider": "anthropic"}))
    orchestrator.register_agent("analyst",    MyFirstAgent({"provider": "google", "model": "gemini-pro"}))

    # All agents execute in parallel with asyncio
    result = await orchestrator.run_swarm(task="Research AI safety")
    print(f"Completed: {result['successful']} agents")

if __name__ == "__main__":
    asyncio.run(run_swarm())
```

## 7. Dynamic Tool Registration

Register custom tools at runtime — no subclassing required:

```python
from framework import global_registry, BaseAgent, ToolDefinitions

# Register a domain-specific tool once
async def handle_json_diff(tool_input):
    import json
    a = json.loads(tool_input["a"])
    b = json.loads(tool_input["b"])
    keys_only_in_a = set(a) - set(b)
    keys_only_in_b = set(b) - set(a)
    return {"only_in_a": list(keys_only_in_a), "only_in_b": list(keys_only_in_b)}

global_registry.register(
    name="json_diff",
    handler=handle_json_diff,
    description="Compare two JSON objects and return differing keys",
    input_schema={
        "type": "object",
        "properties": {
            "a": {"type": "string", "description": "First JSON string"},
            "b": {"type": "string", "description": "Second JSON string"},
        },
        "required": ["a", "b"]
    }
)

# Any agent's ToolExecutor now automatically has json_diff
```

## 8. YAML Configuration

Declare your entire orchestration topology in a config file:

`config.yaml`:
```yaml
provider: anthropic
# model: omit to use provider-specific default, or specify explicitly
# model: claude-sonnet-4-5-20250929
max_tokens: 4000
temperature: 0.7
max_concurrent_agents: 5

presets:
  full:    [researcher, analyst, reporter]
  quick:   [researcher, reporter]
```

`run_from_config.py`:
```python
import asyncio
from framework import (
    AgentOrchestrator,
    load_config, agent_config_from, orchestrator_config_from,
    register_presets_from_config
)
from my_agent import MyFirstAgent

async def main():
    cfg       = load_config("config.yaml")
    agent_cfg = agent_config_from(cfg)
    orch_cfg  = orchestrator_config_from(cfg)

    orchestrator = AgentOrchestrator(orch_cfg)
    orchestrator.register_agent("researcher", MyFirstAgent(agent_cfg))
    orchestrator.register_agent("analyst",    MyFirstAgent(agent_cfg))
    orchestrator.register_agent("reporter",   MyFirstAgent(agent_cfg))
    register_presets_from_config(orchestrator, cfg)

    result = await orchestrator.run_preset("full", task="Summarize recent AI research")
    print(result["status"])

if __name__ == "__main__":
    asyncio.run(main())
```

## What Next?

### Intelligent Provider Routing with Fallback
```python
from framework import get_adaptive_provider

# Tries providers in priority order; falls back automatically on failure
provider, name = await get_adaptive_provider(task_type="coding")
response = await provider.query("Write a fast sort in Python")
print(f"Used: {name}")
```

### Response Cleaning
```python
from framework import BaseAgent

raw = "<think>private reasoning</think>```python\nprint('hello')\n```"
clean = BaseAgent.clean_response(raw)
# → "print('hello')"
```

### Persistent Async Memory
```python
from framework import AgentMemory

memory = AgentMemory(agent_id="my_agent")
await memory.store("project_goal", "Optimize framework performance")
goal = await memory.retrieve("project_goal")
```

### Access Full Pipeline History in an Agent
```python
async def run(self, task: str, context=None) -> Dict[str, Any]:
    prior_stages = (context or {}).get("pipeline_stages", [])
    for stage in prior_stages:
        print(f"Prior stage: {stage['agent_id']} → {stage['result']['status']}")
    ...
```

## Tips

1. **Always `await`**: Every LLM call and tool execution is async — always use `await`.
2. **Use `clean_response`**: Call `self.clean_response(raw)` on every LLM output to strip formatting noise, especially when using reasoning models.
3. **Presets over lists**: Register pipeline presets by name for reusable, config-friendly workflows.
4. **Global registry for custom tools**: Use `global_registry.register()` rather than repeating tool setup in every agent class.
5. **Optimized Caching**: The framework automatically caches responses to `.llm_cache.json` with model-aware keys.
6. **Use `uv`**: For the fastest installation and dependency resolution.
