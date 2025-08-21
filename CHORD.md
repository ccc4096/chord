# CHORD: Contextual Hierarchy & Orchestration for Requests & Directives

**Version**: 1.0.0  
**Status**: Production Ready  
**License**: MIT

> CHORD is not a markup language. It's a **declarative context graph** that compiles prompts as **deterministic views** over your knowledge space.

## Table of Contents

1. [Philosophy](#philosophy)
2. [Core Concepts](#core-concepts)
3. [Node Types](#node-types)
4. [Syntax](#syntax)
5. [Selectors](#selectors)
6. [Model Management](#model-management)
7. [Orchestration](#orchestration)
8. [Runtime](#runtime)
9. [Testing](#testing)
10. [Best Practices](#best-practices)

## Philosophy

CHORD represents a paradigm shift in prompt engineering:

- **Context is primary**: Prompts are merely views over a knowledge graph
- **Deterministic assembly**: Same inputs → same outputs, always
- **Compression as strategy**: Intelligent context selection, not brute force
- **Separation of concerns**: Context, capabilities, policies, and execution are distinct
- **Graph, not documents**: Relationships matter more than sequence

### Design Principles

1. **Declarative over imperative**: Define what, not how
2. **Composable primitives**: Small, reusable definitions
3. **Fail predictably**: Explicit error handling and fallbacks
4. **Test everything**: Built-in validation and assertions
5. **Model agnostic**: Works with any LLM provider

## Core Concepts

### The Graph Model

CHORD treats your entire context as a directed graph where:

- **Nodes** are typed definitions (context, capabilities, roles, etc.)
- **Edges** represent relationships (consumes, produces, depends_on, etc.)
- **Views** are compiled projections over the graph
- **Selectors** transform raw context into prompt-ready content

### Compilation Process

```
.chord source → Parser → Graph → View Resolution → Selector Execution → Prompt Assembly → LLM
                                        ↓
                                   IR (JSON)
```

## Node Types

### `ctx` - Context Sources

Represents any source of information:

```chord
def ctx codebase {
  type: repo                    # file|dir|repo|api|memory|stream
  uri: "git+ssh://github.com/user/project.git"
  branch: "main"
  watch: true                    # Enable file watching
  include: ["**/*.py", "**/*.md"]
  exclude: ["**/node_modules/**", "**/__pycache__/**"]
  index: {
    type: "semantic"             # semantic|keyword|hybrid
    update: "on_change"          # on_change|periodic|manual
  }
}
```

### `cap` - Capabilities

Defines what the system can do:

```chord
def cap database_query {
  type: function
  runtime: "python"
  bind: {
    module: "app.database"
    function: "execute_query"
    signature: "List[Dict] execute_query(sql: str, params: Dict = {})"
  }
  sandbox: true                  # Run in isolated environment
  timeout: 30000                 # ms
  retry: { attempts: 3, backoff: "exponential" }
}
```

### `role` - Behavioral Profiles

Defines how the LLM should behave:

```chord
def role senior_architect {
  persona: "principal software architect with 20 years experience"
  principles: [
    "design for maintainability over cleverness",
    "explicit is better than implicit",
    "prefer composition over inheritance"
  ]
  style: {
    tone: "professional but approachable"
    verbosity: "concise with examples"
    code_style: ["typed", "documented", "tested"]
  }
  knowledge_domains: ["distributed systems", "event sourcing", "DDD"]
}
```

### `policy` - Constraints & Guardrails

Controls execution boundaries:

```chord
def policy production {
  privacy: {
    pii_handling: "redact"
    secrets: "never_log"
    data_retention: "session_only"
  }
  resources: {
    max_tokens: 32000
    max_cost_usd: 1.50
    timeout_ms: 60000
    max_parallel_calls: 3
  }
  tools: {
    allow: ["read", "search", "analyze"]
    deny: ["write", "delete", "execute"]
    require_confirmation: ["database_write"]
  }
  compliance: ["gdpr", "sox", "hipaa"]
}
```

### `model` - Model Specifications

Defines available models and their characteristics:

```chord
def model claude_opus {
  provider: "anthropic"
  id: "claude-3-opus-20240229"
  endpoint: "https://api.anthropic.com/v1/messages"
  context_window: 200000
  max_output: 4096
  strengths: ["reasoning", "code_generation", "long_context"]
  weaknesses: ["real_time_data", "image_generation"]
  cost: { input_per_1k: 0.015, output_per_1k: 0.075 }
  rate_limit: { requests_per_minute: 60, tokens_per_minute: 80000 }
  temperature_range: [0.0, 1.0]
  supports: ["tools", "vision", "streaming"]
}
```

### `task` - Objectives

Defines what needs to be accomplished:

```chord
def task refactor_module {
  objective: "Refactor authentication module for better testability"
  priority: "high"
  inputs: {
    module_path: { type: "string", required: true }
    style_guide: { type: "@ctx", default: @ctx.style_guide }
  }
  outputs: {
    refactored_code: "string"
    migration_guide: "markdown"
    breaking_changes: "list"
  }
  constraints: [
    "maintain backward compatibility for public APIs",
    "achieve 90% test coverage",
    "reduce cyclomatic complexity below 10"
  ]
  success_criteria: {
    tests_pass: true
    coverage: { min: 0.9 }
    performance: { regression_threshold: 0.1 }
  }
}
```

### `flow` - Orchestration

Defines execution sequences:

```chord
def flow code_review {
  entry: @task.analyze_pr
  
  edges: [
    { 
      from: @task.analyze_pr, 
      to: @task.security_scan,
      condition: "has_code_changes"
    },
    { 
      from: @task.security_scan, 
      to: @task.suggest_improvements,
      condition: "security_passed"
    },
    { 
      from: @task.security_scan, 
      to: @task.alert_security_team,
      condition: "critical_vulnerability_found"
    }
  ]
  
  error_handling: {
    on_timeout: "retry_with_smaller_context"
    on_model_error: "fallback_to_simpler_model"
    max_retries: 3
  }
  
  parallelism: {
    max_concurrent: 3
    strategy: "breadth_first"
  }
}
```

### `view` - Prompt Rendering

Defines how to assemble prompts:

```chord
def view implement_feature {
  task: @task.implement_oauth
  role: @role.senior_engineer
  model: @model.claude_opus
  policy: @policy.development
  
  selectors: [
    # Context selection with advanced operations
    { 
      from: @ctx.codebase, 
      op: "semantic_search",
      query: "authentication OAuth2 implementation",
      top_k: 10,
      rerank: true
    },
    {
      from: @ctx.documentation,
      op: "extract",
      sections: ["OAuth2 Flow", "Security Best Practices"],
      summarize_if_over: 2000
    },
    {
      from: @ctx.tests,
      op: "ast_extract",
      symbols: ["test_oauth_*"],
      include_imports: true
    },
    {
      from: @ctx.dependencies,
      op: "dep_graph",
      root: "auth_module",
      depth: 2,
      include_versions: true
    }
  ]
  
  prompt: {
    system: |
      You are {{role.persona}} with expertise in {{role.knowledge_domains | join(", ")}}.
      Follow these principles: {{role.principles | bulletize}}
      Current date: {{signal.date}}
      Environment: {{signal.environment}}
    
    developer: |
      ## Objective
      {{task.objective}}
      
      ## Context
      {{resolved_context | format_as_sections}}
      
      ## Constraints
      {{task.constraints | bulletize}}
      
      ## Success Criteria
      {{task.success_criteria | format_as_checklist}}
    
    user: |
      Please implement OAuth2 authentication for our application.
      Use the existing auth framework where possible.
      Session ID: {{signal.session_id}}
  }
  
  response_format: {
    type: "structured"
    schema: {
      code: "string"
      explanation: "string"
      tests: "array<string>"
      migration_steps: "array<string>"
    }
  }
  
  post_process: [
    { action: "validate_syntax", language: "python" },
    { action: "check_imports", available: @ctx.dependencies },
    { action: "estimate_complexity" }
  ]
}
```

### `memory` - Conversation & State

Manages stateful information:

```chord
def memory session {
  type: "conversational"
  strategy: "sliding_window"
  max_turns: 20
  compression: {
    after_turns: 10
    method: "summary"
    preserve: ["decisions", "code_blocks", "errors"]
  }
  persistence: {
    backend: "redis"
    ttl: 86400
    key_prefix: "chord_session_"
  }
}
```

### `hook` - Extension Points

Defines custom processing:

```chord
def hook pre_execution {
  trigger: "before_llm_call"
  script: "validators/check_context_size.py"
  timeout: 5000
  on_failure: "continue_with_warning"
  
  params: {
    max_tokens: @policy.resources.max_tokens
    model_limit: @model.context_window
  }
}

def hook post_response {
  trigger: "after_llm_response"
  actions: [
    { script: "quality/check_code_style.py", blocking: false },
    { script: "security/scan_for_vulnerabilities.py", blocking: true },
    { script: "metrics/track_usage.py", blocking: false }
  ]
}
```

## Selectors

Selectors transform raw context into prompt-ready content:

### Basic Operations

```chord
# Simple extraction
{ from: @ctx.file, op: "head", lines: 100 }
{ from: @ctx.file, op: "tail", lines: 50 }
{ from: @ctx.file, op: "lines", start: 10, end: 50 }

# Pattern matching
{ from: @ctx.logs, op: "grep", pattern: "ERROR.*timeout", context: 3 }
{ from: @ctx.code, op: "regex", pattern: "class\\s+(\\w+)", capture: 1 }
```

### Semantic Operations

```chord
# Embedding-based search
{ 
  from: @ctx.knowledge_base, 
  op: "semantic_search",
  query: "how to handle authentication errors",
  top_k: 5,
  threshold: 0.7,
  rerank: true
}

# Semantic chunking
{
  from: @ctx.large_document,
  op: "semantic_chunk",
  max_chunks: 10,
  chunk_size: 500,
  overlap: 50,
  method: "sentence_boundary"
}
```

### Code-Aware Operations

```chord
# AST extraction
{
  from: @ctx.source_code,
  op: "ast_extract",
  types: ["function", "class", "import"],
  filter: {
    visibility: "public",
    has_decorator: "@api_endpoint"
  }
}

# Dependency graph
{
  from: @ctx.module,
  op: "dep_graph",
  root: "UserService",
  depth: 3,
  include: ["imports", "calls", "inheritance"]
}

# Symbol resolution
{
  from: @ctx.codebase,
  op: "resolve_symbol",
  symbol: "DatabaseConnection",
  include: ["definition", "usages", "tests"]
}
```

### Transformation Operations

```chord
# Summarization
{
  from: @ctx.meeting_notes,
  op: "summarize",
  max_tokens: 500,
  style: "bullet_points",
  preserve: ["action_items", "decisions"]
}

# Format conversion
{
  from: @ctx.json_data,
  op: "transform",
  to: "yaml",
  pretty: true
}

# Diff generation
{
  from: @ctx.repo,
  op: "diff",
  base: "main",
  head: "feature/oauth",
  context_lines: 3,
  exclude: ["*.lock", "*.generated.*"]
}
```

### Conditional Selection

```chord
{
  from: @ctx.debug_logs,
  op: "tail",
  lines: 1000,
  when: {
    condition: "task_failed",
    signal: @signal.last_task_status
  }
}

{
  from: @ctx.production_config,
  op: "extract",
  when: {
    environment: "production",
    user_role: "admin"
  }
}
```

## Model Management

### Model Selection Strategy

```chord
def strategy model_selection {
  rules: [
    {
      when: { task_type: "architecture", complexity: "high" },
      use: @model.gpt4_turbo,
      reason: "Best for high-level design decisions"
    },
    {
      when: { task_type: "implementation", language: "python" },
      use: @model.claude_opus,
      reason: "Superior code generation capabilities"
    },
    {
      when: { context_size: "> 100000" },
      use: @model.claude_opus,
      reason: "Largest context window"
    },
    {
      when: { budget_remaining: "< 0.50" },
      use: @model.local_llama,
      reason: "Cost optimization"
    }
  ]
  
  fallback_chain: [
    @model.claude_opus,
    @model.gpt4_turbo,
    @model.local_llama
  ]
}
```

### Multi-Model Orchestration

```chord
def flow multi_model_pipeline {
  stages: [
    {
      name: "planning",
      task: @task.design_architecture,
      model: @model.gpt4_turbo,
      temperature: 0.7
    },
    {
      name: "implementation",
      task: @task.write_code,
      model: @model.claude_opus,
      temperature: 0.3
    },
    {
      name: "review",
      task: @task.code_review,
      model: @model.local_codellama,
      temperature: 0.1
    }
  ]
  
  aggregation: {
    method: "ensemble",
    weights: { planning: 0.3, implementation: 0.5, review: 0.2 }
  }
}
```

## Orchestration

### Complex Flow Patterns

```chord
def flow distributed_processing {
  type: "dag"  # directed acyclic graph
  
  nodes: [
    { id: "split", task: @task.partition_data },
    { id: "process_1", task: @task.analyze_chunk },
    { id: "process_2", task: @task.analyze_chunk },
    { id: "process_3", task: @task.analyze_chunk },
    { id: "merge", task: @task.combine_results }
  ]
  
  edges: [
    { from: "split", to: ["process_1", "process_2", "process_3"], strategy: "scatter" },
    { from: ["process_1", "process_2", "process_3"], to: "merge", strategy: "gather" }
  ]
  
  execution: {
    parallelism: 3
    timeout_per_node: 30000
    retry_failed_nodes: true
  }
}
```

### Conditional Branching

```chord
def flow adaptive_review {
  entry: @task.initial_analysis
  
  branches: [
    {
      condition: "complexity_score > 8",
      path: [@task.deep_analysis, @task.expert_review, @task.comprehensive_report]
    },
    {
      condition: "has_security_implications",
      path: [@task.security_scan, @task.vulnerability_assessment, @task.security_report]
    },
    {
      condition: "is_performance_critical",
      path: [@task.performance_profile, @task.optimization_suggestions]
    },
    {
      default: true,
      path: [@task.standard_review, @task.basic_report]
    }
  ]
  
  merge_strategy: "combine_all_paths"
}
```

## Runtime

### Compilation Pipeline

```python
# Conceptual runtime implementation
class CHORDRuntime:
    def compile(self, source: str) -> IntermediateRepresentation:
        ast = self.parser.parse(source)
        graph = self.builder.build_graph(ast)
        validated = self.validator.validate(graph)
        return self.ir_generator.generate(validated)
    
    def execute(self, ir: IntermediateRepresentation, signals: Dict) -> Result:
        view = self.resolve_view(ir, signals)
        context = self.execute_selectors(view.selectors)
        prompt = self.render_prompt(view.prompt, context, signals)
        
        with self.policy_enforcer(view.policy):
            response = self.llm_client.complete(
                model=view.model,
                prompt=prompt,
                **view.model_params
            )
        
        return self.post_process(response, view.post_process)
```

### Caching Strategy

```chord
def cache config {
  levels: [
    {
      name: "selector_cache",
      storage: "memory",
      ttl: 300,
      max_size: "100MB",
      key: ["file_hash", "selector_op", "params"]
    },
    {
      name: "prompt_cache",
      storage: "redis",
      ttl: 3600,
      key: ["view_id", "context_hash", "signals_hash"]
    },
    {
      name: "response_cache",
      storage: "disk",
      ttl: 86400,
      key: ["prompt_hash", "model_id", "temperature"]
    }
  ]
  
  invalidation: {
    on_file_change: ["selector_cache", "prompt_cache"],
    on_model_update: ["response_cache"],
    manual_flush: true
  }
}
```

## Testing

### Unit Testing

```chord
def test selector_extraction {
  input: {
    context: @ctx.sample_file,
    selector: { op: "extract", lines: [10, 20] }
  }
  
  expect: {
    output_lines: 11,
    contains: ["function", "return"],
    not_contains: ["private", "deprecated"]
  }
}
```

### Integration Testing

```chord
def test end_to_end_flow {
  scenario: "OAuth implementation"
  
  given: {
    contexts: [@ctx.test_codebase, @ctx.test_docs],
    signals: { environment: "test", date: "2024-01-01" }
  }
  
  when: {
    execute_flow: @flow.implement_oauth,
    with_model: @model.mock_llm
  }
  
  then: {
    tasks_completed: ["design", "implement", "test"],
    outputs_valid: true,
    cost_under: 0.50,
    time_under: 60000
  }
}
```

### Property-Based Testing

```chord
def property deterministic_compilation {
  for_all: {
    graph: "valid_chord_graph",
    signals: "valid_signal_set"
  }
  
  property: "compile(graph, signals) == compile(graph, signals)"
  
  invariants: [
    "same input produces same prompt",
    "prompt size within policy limits",
    "all references resolve"
  ]
}
```

## Best Practices

### 1. **Context Minimization**

Always select the minimum context needed:

```chord
# Good: Specific selection
{ from: @ctx.api_docs, op: "extract", sections: ["Authentication", "Error Handling"] }

# Bad: Entire document
{ from: @ctx.api_docs, op: "all" }
```

### 2. **Fail Gracefully**

Always define fallbacks:

```chord
def policy resilient {
  on_error: {
    context_too_large: { action: "summarize_aggressively", max_tokens: 1000 },
    model_unavailable: { action: "use_fallback", model: @model.local },
    rate_limited: { action: "exponential_backoff", max_retries: 5 }
  }
}
```

### 3. **Test Everything**

Every view should have tests:

```chord
def test_suite my_feature {
  tests: [
    @test.unit_selectors,
    @test.integration_flow,
    @test.edge_cases,
    @test.performance_bounds
  ]
  
  coverage_threshold: 0.8
  performance_threshold: { p95_latency: 5000 }
}
```

### 4. **Version Control**

Track changes to your CHORD definitions:

```chord
def meta version {
  chord_version: "1.0.0"
  schema_version: "2024.1"
  compatibility: ["0.9.x", "1.x"]
  
  migrations: [
    { from: "0.9", to: "1.0", script: "migrations/v1.py" }
  ]
}
```

### 5. **Monitor and Optimize**

Track performance and costs:

```chord
def monitor metrics {
  track: [
    { metric: "prompt_tokens", aggregate: "sum", window: "1h" },
    { metric: "response_time", aggregate: "p95", window: "5m" },
    { metric: "cost_usd", aggregate: "sum", window: "1d" },
    { metric: "cache_hit_rate", aggregate: "avg", window: "1h" }
  ]
  
  alerts: [
    { when: "cost_usd > 100", action: "notify_admin" },
    { when: "response_time.p95 > 10000", action: "scale_up" },
    { when: "cache_hit_rate < 0.3", action: "investigate" }
  ]
}
```

## Implementation Roadmap

### Phase 1: Core (Week 1-2)
- Parser for .chord files
- Basic selector operations (head, tail, extract)
- Simple prompt assembly
- CLI interface

### Phase 2: Advanced (Week 3-4)
- Semantic search selectors
- AST-based code extraction
- Multi-model support
- Caching layer

### Phase 3: Production (Week 5-6)
- Distributed execution
- Monitoring and metrics
- IDE extensions
- Comprehensive test suite

### Phase 4: Ecosystem (Ongoing)
- Community patterns library
- Third-party integrations
- GUI editor
- Cloud runtime

## Contributing

CHORD is designed to be extensible. Key extension points:

1. **Custom Selectors**: Implement new selector operations
2. **Model Adapters**: Add support for new LLM providers
3. **Storage Backends**: Integrate different caching/persistence layers
4. **Hooks**: Create custom pre/post processors

## License

MIT License - See LICENSE file for details

## Acknowledgments

CHORD builds on insights from the prompt engineering community while introducing novel concepts in context management and deterministic prompt assembly.

---

*For examples, see [CHORD_EXAMPLES.md](./CHORD_EXAMPLES.md)*  
*For syntax reference, see [CHORD_SYNTAX.md](./CHORD_SYNTAX.md)*  
*For implementation, see [Reference Implementation](./src/)*