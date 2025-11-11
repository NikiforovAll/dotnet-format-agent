# Building Specialized AI Agents with Claude Agent SDK

**How to turn your CLI tools into conversational AI agents**

## Why This Matters

You have great CLI tools. But running them requires:
- Remembering command syntax
- Piping outputs between tools
- Manually analyzing results
- Context switching between terminal and docs

**What if your tools could have a conversation with you?**

```bash
$ tda "Show me the most common code quality issues"
→ Using tool: extract_style_diagnostics
→ Using tool: extract_analyzers_diagnostics

# 📊 Code Quality Analysis

Found 47 diagnostics across 12 files:

**Top Issues:**
1. IDE0055 (Fix formatting) - 23 occurrences
2. CA1031 (Don't catch general exceptions) - 12 occurrences
3. IDE1006 (Naming rule violation) - 8 occurrences

**Next Steps:**
1. Run `tda "Fix all IDE0055 in Program.cs"` to auto-fix formatting
2. Review exception handling in error-prone files
```

That's what specialized AI agents enable. Let's build one.

## The Anatomy of a Specialized Agent

Think of a specialized agent as having **three layers**:

```
┌─────────────────────────────────────┐
│  1. Conversational Interface        │  ← What users interact with
│     "Show me code quality issues"   │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│  2. Agent Brain (Claude SDK)        │  ← Understands intent, calls tools
│     • Interprets natural language   │
│     • Calls appropriate tools       │
│     • Formats responses            │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│  3. Tool Layer (Your CLI Tools)     │  ← Does the actual work
│     • Executes dotnet format        │
│     • Parses results                │
│     • Returns structured data       │
└─────────────────────────────────────┘
```

**The beauty**: Your existing CLI tools become conversational with minimal changes.

### Project Structure

```
your-agent/
├── src/
│   ├── tool/               # Your existing CLI tool
│   │   ├── runner.py       # Executes external commands
│   │   ├── parser.py       # Processes output
│   │   └── cli.py          # CLI interface
│   └── agent/              # AI wrapper (new!)
│       ├── tools.py        # Exposes CLI as AI tools
│       ├── agent.py        # MCP server setup
│       ├── cli.py          # Conversational interface
│       └── system_prompt.prompty  # Agent instructions
```

**Key insight**: Keep your tool layer independent. The agent is just a wrapper.

## Building Block 1: Your Tool Layer

**Start with what you have**. You probably already have CLI tools that do useful work:

```python
# Your existing tool that wraps external commands
class MyToolRunner:
    def run_analysis(self, project_path: str, options: dict):
        # Run external tool (linter, formatter, analyzer, etc.)
        result = subprocess.run(["your-tool", "--json", project_path])

        # Parse output
        data = json.loads(result.stdout)

        # Return structured data
        return {
            "findings": parse_findings(data),
            "summary": generate_summary(data)
        }
```

**Three simple rules**:
1. ✅ Accept structured inputs (paths, options)
2. ✅ Return structured outputs (dicts, lists)
3. ✅ Handle errors gracefully

**Pro tip**: Optimize your output format. We use TOON (Terminal Object Notation) which reduces token usage by 30-60% compared to JSON:

```
# Instead of JSON (verbose)
[{"file": "foo.cs", "line": 10, "rule": "IDE0055"}]

# Use compact format
IDE0055 (count: 1):
 foo.cs:10
```

Token efficiency = cost savings + faster responses.

## Building Block 2: Wrapping Tools with MCP

**The Model Context Protocol (MCP)** is how you expose your tools to Claude. Think of it as the API contract between your tool and the AI.

### Step 1: Expose Your Tool

```python
from claude_agent_sdk import tool

@tool(
    "analyze_code",  # Tool name
    "Analyzes code quality in a project",  # Description
    {"path": str, "severity": str}  # Input schema
)
async def analyze_code(args: dict) -> dict:
    """This is what the AI calls when users ask about code quality."""

    # 1. Extract parameters
    path = args["path"]
    severity = args.get("severity", "warn")

    # 2. Call your existing tool
    runner = MyToolRunner()
    result = runner.run_analysis(path, {"severity": severity})

    # 3. Return formatted response
    return {
        "content": [{
            "type": "text",
            "text": f"Found {len(result['findings'])} issues"
        }]
    }
```

That's it! Three steps: extract → execute → return.

### Step 2: Create MCP Server

```python
from claude_agent_sdk import create_sdk_mcp_server

# Bundle your tools into a server
my_server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[analyze_code, other_tool]  # List all your tools
)
```

### Step 3: Configure the Agent

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

options = ClaudeAgentOptions(
    mcp_servers={"mytools": my_server},  # Your MCP server
    allowed_tools=["mcp__mytools__analyze_code"],  # Which tools to enable
    cwd="/path/to/project",
    permission_mode="bypassPermissions",  # Auto-approve
    system_prompt={
        "type": "preset",
        "preset": "claude_code",  # Inherit base behavior
        "append": "You are a code quality expert..."  # Add your instructions
    }
)

# Use the agent
async with ClaudeSDKClient(options=options) as client:
    await client.query("What's the code quality?")
    async for message in client.receive_response():
        print(message)
```

**That's the whole pattern**:
1. `@tool` decorator → expose function
2. `create_sdk_mcp_server` → bundle tools
3. `ClaudeAgentOptions` → configure agent
4. `ClaudeSDKClient` → run queries

## Building Block 3: Teaching Your Agent

**The system prompt is where your agent learns its personality and expertise.**

Create a file `system_prompt.prompty`:

```yaml
---
name: My Agent System Prompt
---
system:
You are a {DOMAIN} expert specialized in {TASK}.

Your capabilities:
- Tool 1: What it does
- Tool 2: What it does

When users ask for {COMMON_REQUEST}:
1. Use {TOOL} to gather data
2. Analyze and prioritize findings
3. Provide actionable next steps

Always format responses in Markdown with clear sections.
```

**Real example** from TDA:

```yaml
You are a Technical Debt Agent for .NET codebases.

Available tools:
- extract_style_diagnostics: Code formatting issues
- extract_analyzers_diagnostics: Code analysis warnings

When analyzing codebases:
1. Extract diagnostics with 'warn' severity by default
2. Group similar issues together
3. Always include "Next Steps" section

Use .NET terminology (diagnostics, not errors).
Reference diagnostic IDs (IDE0055, CA1031).
```

**Pro tips**:
- ✅ Set smart defaults ("filter to 'warn' by default")
- ✅ Document tool limitations ("paths are literal, not globs")
- ✅ Define output structure ("always include Next Steps")
- ✅ Use domain terminology consistently

## Building Block 4: Handling AI Quirks

**AI agents don't always pass perfect parameters**. You might get:
- `include='[]'` (string) instead of `include=[]` (list)
- `severity='all'` instead of `severity=None`

**Solution: Normalize at the boundary**:

```python
@tool("my_tool", "...", {"severity": str, "include": list[str]})
async def my_tool(args: dict) -> dict:
    # Normalize messy inputs
    severity = args.get("severity")
    if severity in ["all", "None", "", None]:
        severity = None  # "No filter" is None

    include = args.get("include")
    if not include or include == "[]":
        include = None  # Empty list = no filter

    # Now call your clean tool layer
    result = my_runner.run(severity=severity, include=include)
    ...
```

**Pattern**: Trust your tool layer, normalize at the agent boundary.

## Building Block 5: Polish the UX

**Make it feel good to use**. Small details matter:

```python
# 1. Show what the agent is doing
console.print("[dim cyan]→ Using tool: analyze_code[/dim cyan]")

# 2. Render responses beautifully (use Rich library)
from rich.markdown import Markdown
markdown = Markdown(response.text)
console.print(markdown)

# 3. Interactive mode for exploration
async with ClaudeSDKClient(options) as client:
    while True:
        query = input("You> ")
        if query.lower() in ["exit", "quit"]:
            break

        await client.query(query)
        async for message in client.receive_response():
            display(message)

# 4. Show cost tracking
console.print(f"[dim]Cost: ${message.total_cost_usd:.4f}[/dim]")
```

**UX Checklist**:
- ✅ Show tool usage ("→ Using tool: X")
- ✅ Markdown formatting (headers, code blocks, lists)
- ✅ Interactive mode for multi-turn conversations
- ✅ Cost transparency
- ✅ Clean error messages

## Why Build Specialized Agents?

### Before (Traditional CLI)
```bash
$ dotnet format --verify-no-changes --report report.json --severity warn
$ cat report.json | jq '.[] | select(.severity=="Warning")'
$ # manually analyze JSON...
$ # manually read docs for CA1031...
$ # manually decide what to fix...
```

### After (Specialized Agent)
```bash
$ tda "What should I fix first?"

Found 47 warnings. Top priorities:

1. **IDE0055** (23 occurrences) - Formatting
   → Auto-fixable. Run: tda "Fix formatting"

2. **CA1031** (12 occurrences) - Catching general exceptions
   → Security risk. Let me show you the official docs...

**Want me to fix the formatting issues automatically?**
```

**The difference**:
- ❌ Remember command syntax → ✅ Ask in plain English
- ❌ Parse JSON manually → ✅ Get analyzed summaries
- ❌ Look up docs yourself → ✅ Agent fetches them
- ❌ One-shot commands → ✅ Iterative conversation

## The Pattern: Reusable Building Blocks

Every specialized agent follows this recipe:

1. **Tool Layer** (what you already have)
   - CLI tool that does the work
   - Clean input/output interface

2. **Agent Layer** (what you add)
   ```python
   @tool("your_tool", "description", {schema})
   async def your_tool(args):
       result = your_runner.run(...)
       return {"content": [{"type": "text", "text": result}]}

   server = create_sdk_mcp_server(tools=[your_tool])

   options = ClaudeAgentOptions(
       mcp_servers={"your": server},
       system_prompt={"append": "You are a {DOMAIN} expert..."}
   )
   ```

3. **UX Layer** (polish)
   - Interactive mode
   - Rich markdown rendering
   - Helpful defaults

**That's it**. Same pattern for:
- Code analysis agents (this post)
- DevOps automation agents
- Data pipeline agents
- Testing agents
- Documentation agents

## Quick Start Guide

```bash
# 1. Install SDK
pip install claude-agent-sdk

# 2. Wrap your tool
@tool("my_analysis", "Analyzes something", {"path": str})
async def my_analysis(args):
    result = my_runner.run(args["path"])
    return {"content": [{"type": "text", "text": result}]}

# 3. Create agent
server = create_sdk_mcp_server(tools=[my_analysis])
options = ClaudeAgentOptions(
    mcp_servers={"mine": server},
    system_prompt={"append": "You are an expert..."}
)

# 4. Run
async with ClaudeSDKClient(options) as client:
    await client.query("Analyze my code")
    async for msg in client.receive_response():
        print(msg)
```

## Resources

- **[Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)** - Main SDK
- **[MCP Documentation](https://modelcontextprotocol.io/)** - Protocol spec
- **[TDA Repository](https://github.com/yourusername/techdebt-agent)** - Full example
- **[Context7 for SDK docs](https://context7.com/anthropics/claude-agent-sdk-python)** - API reference

## What Will You Build?

Specialized agents shine when you have:
- ✅ A task you repeat weekly/daily
- ✅ CLI tools that need orchestration
- ✅ Domain knowledge worth embedding
- ✅ Workflows that benefit from conversation

**Examples**:
- Security scanner agent (integrates multiple tools, explains vulnerabilities)
- Performance profiler agent (analyzes bottlenecks, suggests optimizations)
- CI/CD agent (checks build status, investigates failures)
- Database migration agent (validates schemas, suggests fixes)

**Start with what you know**. Take your existing tools, wrap them with Claude Agent SDK, and give them a conversation interface.

The future isn't AI replacing tools - it's AI making tools conversational.
