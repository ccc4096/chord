Let’s build something bold and context‑first, not a “markup” wrapper on prompts but a **graph of definitions** that an orchestrator can compile into the **minimum, situation‑aware prompt** an LLM needs at each step.

Below is a complete first cut: name, mental model, core spec, an example that **rewrites your acPOML into the new form**, and a tiny compiler plan. It’s intentionally radical but implementable today.

---

## Name: **CHORD**

**C**ontextual **H**ierarchy & **O**rchestration for **R**equests & **D**irectives

> CHORD is not markup. It’s a **declarative context graph**: you define **things** (contexts, roles, capabilities, tasks, flows, and policies) and the runtime **renders views** that become prompts.
> File extension: `.chord` (source) and `.chordi` (compiled IR).

**Why “CHORD”?** It emphasizes relationships (edges), harmony of parts (context + intent), and orchestration (flows).
*Alternative names if you ever want to rebrand: LATTICE, CHOREO, CORTEX, RUNE—but let’s ship with CHORD.*

---

## Design goals (what makes this new)

1. **Context first**: prompts are **views** over a graph; the view chooses *what to surface* and *how to compress* (summarize, extract signatures, etc.).
2. **Definitions, not documents**: no HTML/XML. Everything is a **typed node** with an **id** and **edges**.
3. **Deterministic assembly**: same graph + same signals ⇒ same prompt bytes (great for testing).
4. **Separation of concerns**:

   * *context* (files, repos, APIs…),
   * *capabilities* (what we can do),
   * *policies* (boundaries),
   * *roles* (LLM persona/strategy),
   * *tasks* (LLM objectives),
   * *flows* (how tasks chain),
   * *views* (how we render a prompt for a task).
5. **Selectable compression**: context is pulled through **selectors** with **operators** (chunk, summarize, extract, embed‑search).
6. **Language‑agnostic outputs**: CHORD compiles to a **canonical JSON IR** your runtime can use with any LLM API.

---

## The CHORD mental model

**Node types (all are first‑class `def`s):**

* `ctx`: a context source (file, dir, repo, api, memory, note...).
* `cap`: a capability the runtime can execute (tool/function, code unit, command).
* `role`: the voice/strategy and quality bars for the LLM.
* `task`: an LLM objective with inputs/outputs and constraints.
* `policy`: guardrails (privacy, cost, style, safety).
* `flow`: orchestration graph: conditions, branching, retries.
* `view`: **how to render** a specific prompt for a `task` using chosen `ctx` + `role` + `policy` + selectors.
* `signal`: dynamic values (date, user, unique\_id, env vars) available at render time.

**Edges (relationships) are explicit**: `consumes`, `produces`, `depends_on`, `watches`, `binds_to`, `uses_role`, `enforced_by`.

---

## Minimal syntax (source `.chord`)

Readable, block‑based definitions. No angle brackets, no tags.

```
def <kind> <id> {
  <property>: <value>
  <property>: [<value>, ...]
  <nested> { ... }
}
```

* `<kind>` ∈ { `ctx`, `cap`, `role`, `task`, `policy`, `flow`, `view`, `signal` }
* Values can be strings, numbers, arrays, or inline objects.
* References use `@<id>` or `@<id>.<field>`.

---

## Core fields by kind

### `ctx` — context source

```
def ctx <id> {
  type: file|dir|repo|api|note|memory
  uri: "fs:///abs/path" | "git+ssh://..." | "https://..." | "note:<name>"
  tags: ["lib", "manifest", "cpp", ...]
  watch?: true|false            # allow runtime to update working memory on changes
  include?: ["**/*.cpp", ...]   # for dir/repo
  exclude?: ["**/build/**"]
}
```

### `cap` — capability/tool/code binding

```
def cap <id> {
  type: function|code_unit|command
  language?: "cpp"|"python"|...
  bind: {
    file?: @ctx_id               # where the unit lives
    symbol?: "read_files"        # function/class name
    cmd?: "make test"            # shell command if type=command
    signature?: "std::vector<std::string> read_files(std::string main_path, ...)"
  }
}
```

### `role`

```
def role <id> {
  persona: "senior systems engineer"
  principles: [
    "prefer deterministic, testable code",
    "minimize external deps",
  ]
  style: {
    tone: "precise",
    code_rules: ["compile-ready", "no pseudocode"]
  }
}
```

### `policy`

```
def policy <id> {
  allow_tools: ["search?": false, "shell": true]
  privacy: ["never paste full file; summarize if > 2000 tokens"]
  cost_limit_tokens: 24000
  max_context_chars: 120000
}
```

### `task`

```
def task <id> {
  objective: "Implement read_files"
  inputs: {
    main_path: "string"
    date: "string"
    unique_id: "string"
    filelist: "vector<string>&"
  }
  outputs: { returns: "vector<string>" }
  consumes: [@cap.code_read_files, @ctx.manifest, ...]  # references
  constraints: [
    "use common_libs/file_watcher",
    "handle UTF-8",
    "return sorted unique paths"
  ]
}
```

### `flow`

```
def flow <id> {
  entry: @task.implement_read_files
  edges: [
    { from: @task.implement_read_files, to: @task.execute_read_files, on: "success" },
    { from: @task.implement_read_files, to: "halt", on: "failure" }
  ]
}
```

### `view` — **the prompt renderer**

```
def view <id> {
  task: @task.implement_read_files
  role: @role.cpp_engineer
  policy: @policy.default
  selectors: [
    { from: @ctx.manifest, op: "extract", what: "sections:Dependencies,Build" },
    { from: @ctx.context_map, op: "summarize", max_tokens: 300 },
    { from: @ctx.lib_registry, op: "extract", what: "file_watcher.*" },
    { from: @cap.code_test_cpp, op: "signature" },
    { from: @cap.code_read_files, op: "signature" }
  ]
  prompt: {
    system: |
      You are a rigorous C++ systems engineer. Follow role principles and policies.
    developer: |
      Implement the function defined in `read_files` inside the specified code unit.
      Adhere to constraints and prefer portability.
    user: |
      Please examine the `common_libs/file_watcher` project and write this function.
      Today's date is {{ signal.date }}. Unique run id: {{ signal.unique_id }}.
  }
  asserts: [
    "compiles with -std=c++17",
    "returns non-empty when directory has files"
  ]
}
```

### `signal`

```
def signal date { value: "2025-08-16" }
def signal unique_id { value: "{{$RANDOM_UUID}}" }   # runtime may expand
```

> **Note**: Selectors define *how* to transform raw context into what the prompt actually sees: `extract`, `summarize`, `grep`, `signature`, `embed_search{query:..., top_k:...}`, `head{n:...}`, etc.

---

## Your acPOML rewritten in CHORD

> I’ve preserved your intent and paths, but expressed as CHORD nodes. Save this as `file_watcher.chord`.

```chord
# --- Contexts (files that need to be read) ---
def ctx manifest {
  type: file
  uri: "fs:///Users/alperyilmaz/Documents/ARR_SOURCES/cyberdroid/manifest.md"
  tags: ["manifest", "project"]
}

def ctx context_map {
  type: file
  uri: "fs:///Users/alperyilmaz/Documents/ARR_SOURCES/cyberdroid/common_libs/context_map.md"
  tags: ["doc", "map"]
}

def ctx lib_registry {
  type: file
  uri: "fs:///Users/alperyilmaz/Documents/ARR_SOURCES/cyberdroid/lib_registry.md"
  tags: ["registry"]
}

# --- Code units / capabilities ---
def ctx test_dir {
  type: dir
  uri: "fs:///Users/alperyilmaz/Documents/ARR_SOURCES/cyberdroid/common_libs/file_watcher/test"
  include: ["**/*.cpp", "**/*.h", "**/CMakeLists.txt"]
}

def cap code_test_cpp {
  type: code_unit
  language: "cpp"
  bind: { file: @test_dir, symbol: "test_basic_read.cpp" }
}

def cap code_read_files {
  type: function
  language: "cpp"
  bind: {
    file: @test_dir
    symbol: "read_files"
    signature: "std::vector<std::string> read_files(std::string main_path, std::string date, std::string unique_id, std::vector<std::string>& filelist)"
  }
}

def cap run_execute_read_files {
  type: command
  bind: { cmd: "execute read_files function" }
}

# --- Role & policy ---
def role cpp_engineer {
  persona: "seasoned C++17 systems engineer"
  principles: [
    "production-quality, deterministic code",
    "avoid UB; prefer std::filesystem",
    "clear, minimal dependencies"
  ]
  style: { tone: "concise", code_rules: ["compile-ready", "no pseudocode", "explain choices in short comments"] }
}

def policy default {
  allow_tools: ["shell": true]
  privacy: ["never paste entire large file; summarize beyond 2000 tokens"]
  cost_limit_tokens: 24000
  max_context_chars: 120000
}

# --- The Task(s) ---
def task implement_read_files {
  objective: "Implement `read_files` for common_libs/file_watcher"
  inputs: {
    main_path: "std::string"
    date: "std::string"
    unique_id: "std::string"
    filelist: "std::vector<std::string>&"
  }
  outputs: { returns: "std::vector<std::string>" }
  consumes: [@code_read_files, @manifest, @context_map, @lib_registry, @code_test_cpp]
  constraints: [
    "use std::filesystem to traverse under main_path",
    "collect files into filelist and return a copy",
    "de-duplicate, sort, and handle paths consistently (UTF-8)",
    "graceful errors; do not throw on non-critical issues"
  ]
}

def task execute_read_files {
  objective: "Execute test that exercises read_files"
  consumes: [@code_test_cpp, @run_execute_read_files]
}

# --- Orchestration ---
def flow default {
  entry: @task.implement_read_files
  edges: [
    { from: @task.implement_read_files, to: @task.execute_read_files, on: "success" }
  ]
}

# --- Signals / run-scoped values ---
def signal date { value: "2025-08-16" }
def signal unique_id { value: "run-{{RANDOM_6}}" }

# --- View: what the model will actually see ---
def view implement_read_files_view {
  task: @task.implement_read_files
  role: @role.cpp_engineer
  policy: @policy.default

  selectors: [
    { from: @manifest, op: "extract", what: "sections:Build,Dependencies" },
    { from: @context_map, op: "summarize", max_tokens: 250 },
    { from: @lib_registry, op: "extract", what: "file_watcher.*" },
    { from: @code_test_cpp, op: "head", n: 3000 },
    { from: @code_read_files, op: "signature" }
  ]

  prompt: {
    system: |
      You are a C++17 systems engineer. Follow persona principles and policy limits.
    developer: |
      Implement `read_files` in the code unit bound to @code_read_files.
      Use std::filesystem and ensure portability. Keep the function self-contained.
    user: |
      Could you please examine the "common_libs/file_watcher" project and write this function?
      date={{ signal.date }}, unique_id={{ signal.unique_id }}
  }

  asserts: [
    "Returns sorted unique list of files",
    "Handles non-existent main_path by returning empty vector",
    "No platform-specific separators in output"
  ]
}
```

---

## What the runtime *renders* (illustrative)

CHORD compiles a `view` into a **canonical prompt** (System/Developer/User blocks) after executing selectors. A concrete example (abbreviated):

**SYSTEM**

* You are a C++17 systems engineer… (from `role` + `view.prompt.system`)
* Policy: never paste… cost\_limit… (from `policy`)

**DEVELOPER**

* Objective, constraints, signature…
* Summarized context (manifest Build & Dependencies; context\_map summary; lib\_registry file\_watcher entry)
* Header of `test_basic_read.cpp` (first N chars)

**USER**

* “Please examine the common\_libs/file\_watcher project…”
* `date=2025-08-16, unique_id=run-4F9A2B`

This is the **only** thing sent to the LLM for this task—assembled from definitions, not hand‑written every time.

---

## The CHORD IR (canonical JSON)

Every `.chord` source compiles to a **normalized JSON graph**. Example top of the IR for one `view`:

```json
{
  "version": "0.1",
  "views": [
    {
      "id": "implement_read_files_view",
      "task": "implement_read_files",
      "role": "cpp_engineer",
      "policy": "default",
      "signals": { "date": "2025-08-16", "unique_id": "run-4F9A2B" },
      "resolved_context": [
        { "id": "manifest", "payload": "## Build\n... (extracted)\n" },
        { "id": "context_map", "payload": "(250-token summary)" },
        { "id": "lib_registry", "payload": "file_watcher: ..." },
        { "id": "code_test_cpp", "payload": "/* first 3000 chars */" },
        { "id": "code_read_files", "payload": "std::vector<std::string> read_files(...)" }
      ],
      "prompt": {
        "system": "...",
        "developer": "...",
        "user": "..."
      },
      "asserts": [
        "Returns sorted unique list of files",
        "Handles non-existent main_path by returning empty vector",
        "No platform-specific separators in output"
      ]
    }
  ]
}
```

---

## A tiny compiler/executor plan (pseudocode)

```python
# 1) Parse .chord into AST (blocks -> nodes)
ast = parse_chord(source_text)  # trivial tokenizer: def, kind, id, {, }, key:, values

# 2) Validate & index
graph = index_nodes(ast)        # dict by id; type-checked

# 3) Resolve a view
view = graph["implement_read_files_view"]

# 4) Collect role/policy/signals
role = graph[view.role]
policy = graph[view.policy]
signals = resolve_signals(graph, env=os.environ)

# 5) Execute selectors
resolved_ctx = []
for sel in view.selectors:
    raw = fetch_ctx(graph[sel["from"]])         # open file/dir/etc.
    payload = apply_op(raw, sel["op"], sel)     # extract/summarize/head/signature/...
    resolved_ctx.append({"id": sel["from"], "payload": payload})

# 6) Render prompt templates (system/developer/user) with {{ signal.* }}
prompt_blocks = render_templates(view.prompt, signals)

# 7) Produce IR
ir = {
  "version": "0.1",
  "view_id": view.id,
  "task": view.task,
  "role": role.id,
  "policy": policy.id,
  "signals": signals,
  "resolved_context": resolved_ctx,
  "prompt": prompt_blocks,
  "asserts": view.asserts
}

# 8) Send to LLM; capture output; run asserts (e.g., compile & test if allowed)
result = llm_call(ir["prompt"], tools=policy_tools(policy))
run_asserts(result, ir["asserts"], workspace)
```

**Selectors (initial ops):**

* `head{n}`: prefix bytes/chars
* `extract{what}`: headings / regex / fenced code blocks by label
* `summarize{max_tokens}`: LLM or embedded summarizer
* `signature`: derive function signature from code unit
* `embed_search{query, top_k}`: pre-built vector index (optional)

---

## Why this is “radical enough”

* **Zero HTML/markup.** Pure definitions + edges.
* **Prompt = view over a graph.** LLMs see *only* what the view selects and composes.
* **Composable compression.** Declarative selector ops become your “context algorithms.”
* **Deterministic.** The same graph yields byte‑stable prompts (good for caching, diffing, and reproducible runs).
* **Testable.** Assertions live with the view; policies cap context and cost.

---

## Next: immediate things you can do

1. **Drop the example into a file** `file_watcher.chord` and wire a minimal Python runtime:

   * Simple lexer for `def` blocks.
   * Map `uri: fs:///...` to file IO.
   * Implement `head`, `extract(heading)`, and `signature` ops first.
   * Render the prompt and use your favorite model.
2. **Add a second view** `execute_read_files_view` that binds to `cap.run_execute_read_files` and presents a short “run log” context back to the model for diagnosis on failure.
3. **Turn policies into reality**: enforce `max_context_chars` by truncating less‑relevant selectors first (e.g., with weights).

---

## Optional: a starter `read_files` design (to anchor expectations)

Even before running CHORD, here’s an outline the model would likely produce, aligning with constraints:

```cpp
#include <filesystem>
#include <string>
#include <vector>
#include <unordered_set>
#include <algorithm>

namespace fs = std::filesystem;

std::vector<std::string> read_files(std::string main_path,
                                    std::string date,
                                    std::string unique_id,
                                    std::vector<std::string>& filelist) {
    filelist.clear();
    std::unordered_set<std::string> seen;

    std::error_code ec;
    fs::path root = fs::u8path(main_path);
    if (!fs::exists(root, ec) || !fs::is_directory(root, ec)) {
        return {};
    }

    for (auto it = fs::recursive_directory_iterator(root, ec);
         it != fs::recursive_directory_iterator(); it.increment(ec)) {
        if (ec) { ec.clear(); continue; }
        if (it->is_regular_file(ec)) {
            std::string p = it->path().generic_string(); // normalized sep
            if (seen.insert(p).second) filelist.emplace_back(std::move(p));
        }
    }

    std::sort(filelist.begin(), filelist.end());
    return filelist; // copy to return type as requested
}
```

(Your runtime can test this automatically in the `execute_read_files` task.)

---

If this matches your appetite for “new, untested, but viable,” we can harden the selector ops and wire a tiny reference compiler next. When you’re ready, drop any additional projects or constraints and I’ll extend the graph & views accordingly.
#  <#Title#>

