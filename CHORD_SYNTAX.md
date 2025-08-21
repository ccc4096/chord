# CHORD Syntax Reference

## File Structure

### File Extension
- Source files: `.chord`
- Compiled IR: `.chordi`
- Test files: `.chord.test`

### Encoding
- UTF-8 required
- Line endings: LF (Unix) or CRLF (Windows)

## Comments

```chord
# Single line comment

#[
  Multi-line comment
  Can span multiple lines
  Useful for documentation
]#
```

## Basic Syntax

### Definition Block

```chord
def <node_type> <identifier> {
  <property>: <value>
  <property>: <value>
  ...
}
```

### Node Types

| Type | Purpose | Required Fields |
|------|---------|-----------------|
| `ctx` | Context source | `type`, `uri` |
| `cap` | Capability | `type`, `bind` |
| `role` | Behavioral profile | `persona` |
| `policy` | Constraints | `resources` |
| `model` | Model specification | `provider`, `id` |
| `task` | Objective | `objective` |
| `flow` | Orchestration | `entry` |
| `view` | Prompt assembly | `task`, `role`, `prompt` |
| `signal` | Runtime value | `value` |
| `memory` | State management | `type` |
| `hook` | Extension point | `trigger` |
| `test` | Test case | `input`, `expect` |
| `cache` | Cache configuration | `storage` |

## Data Types

### Primitives

```chord
string: "hello world"
number: 42
float: 3.14
boolean: true | false
null: null
```

### Collections

```chord
# Array
array: ["item1", "item2", "item3"]

# Object
object: {
  key1: "value1"
  key2: 42
  nested: {
    inner: true
  }
}

# Set (unique values)
set: {"value1", "value2", "value3"}
```

### References

```chord
# Reference to node
@node_id

# Reference to node property
@node_id.property

# Reference to nested property
@node_id.property.nested.value

# Array element reference
@node_id.array[0]

# Dynamic reference
@{signal.environment}_config
```

## String Literals

### Basic Strings

```chord
single_line: "This is a string"
escaped: "Line 1\nLine 2\t\"quoted\""
```

### Multi-line Strings

```chord
# Pipe notation (preserves formatting)
description: |
  This is a multi-line string.
  Each line is preserved exactly.
    Including indentation.

# Folded notation (joins lines)
summary: >
  This is a long string that
  will be folded into a single
  line with spaces between.
```

### Template Strings

```chord
# Variable interpolation
message: "Hello {{user.name}}, today is {{signal.date}}"

# Expression interpolation
status: "Progress: {{completed_tasks}} of {{total_tasks}} ({{completed_tasks / total_tasks * 100}}%)"

# Filters
formatted: "{{price | currency('USD')}}"
list: "{{items | join(', ')}}"
```

## Operators

### Comparison

```chord
equals: "=="
not_equals: "!="
less_than: "<"
less_equal: "<="
greater_than: ">"
greater_equal: ">="
regex_match: "~="
contains: "in"
```

### Logical

```chord
and: "&&"
or: "||"
not: "!"
```

### Arithmetic

```chord
add: "+"
subtract: "-"
multiply: "*"
divide: "/"
modulo: "%"
power: "**"
```

## Selectors

### Basic Syntax

```chord
selectors: [
  { from: <source>, op: <operation>, <params...> }
]
```

### Common Operations

```chord
# Text extraction
{ from: @ctx.file, op: "head", lines: 100 }
{ from: @ctx.file, op: "tail", lines: 50 }
{ from: @ctx.file, op: "lines", start: 10, end: 50 }
{ from: @ctx.file, op: "extract", pattern: "## Section.*" }

# Transformation
{ from: @ctx.data, op: "summarize", max_tokens: 500 }
{ from: @ctx.json, op: "transform", to: "yaml" }
{ from: @ctx.code, op: "format", style: "black" }

# Search
{ from: @ctx.docs, op: "search", query: "authentication", top_k: 5 }
{ from: @ctx.logs, op: "grep", pattern: "ERROR", context: 3 }
{ from: @ctx.code, op: "find_symbol", name: "UserService" }

# Code operations
{ from: @ctx.source, op: "ast_extract", types: ["function", "class"] }
{ from: @ctx.module, op: "dep_graph", root: "main", depth: 3 }
{ from: @ctx.repo, op: "diff", base: "main", head: "feature" }
```

### Conditional Selectors

```chord
{
  from: @ctx.debug,
  op: "tail",
  lines: 1000,
  when: {
    condition: "error_occurred",
    signal: @signal.last_status
  }
}

{
  from: @ctx.config,
  op: "extract",
  when: {
    all: [
      { environment: "production" },
      { user_role: "admin" }
    ]
  }
}
```

### Chained Selectors

```chord
{
  from: @ctx.large_file,
  op: "chain",
  operations: [
    { op: "extract", sections: ["Introduction", "Methods"] },
    { op: "summarize", max_tokens: 500 },
    { op: "translate", to: "es" }
  ]
}
```

## Prompt Templates

### Structure

```chord
prompt: {
  system: <string | template>
  developer: <string | template>
  user: <string | template>
  assistant: <string | template>  # Optional, for few-shot
}
```

### Template Variables

```chord
# Simple variable
{{variable_name}}

# Nested property
{{user.profile.name}}

# Array element
{{items[0]}}

# With default value
{{variable_name | default("fallback")}}
```

### Template Filters

```chord
# String filters
{{text | upper}}
{{text | lower}}
{{text | capitalize}}
{{text | truncate(100)}}

# List filters
{{items | join(", ")}}
{{items | first}}
{{items | last}}
{{items | length}}
{{items | sort}}

# Formatting filters
{{number | round(2)}}
{{date | format("YYYY-MM-DD")}}
{{object | json}}
{{markdown | html}}

# Custom filters
{{code | syntax_highlight("python")}}
{{text | bulletize}}
{{data | table}}
```

### Conditional Templates

```chord
prompt: {
  user: |
    {{#if has_error}}
    Error occurred: {{error_message}}
    {{else}}
    Operation successful
    {{/if}}
    
    {{#each items}}
    - {{this.name}}: {{this.value}}
    {{/each}}
}
```

## Flow Control

### Sequential Flow

```chord
def flow sequential {
  steps: [
    @task.step1,
    @task.step2,
    @task.step3
  ]
}
```

### Conditional Flow

```chord
def flow conditional {
  entry: @task.analyze
  
  branches: [
    {
      condition: "score > 80",
      path: @task.advanced_processing
    },
    {
      condition: "score > 50",
      path: @task.standard_processing
    },
    {
      default: true,
      path: @task.basic_processing
    }
  ]
}
```

### Parallel Flow

```chord
def flow parallel {
  entry: @task.start
  
  parallel: [
    @task.process_a,
    @task.process_b,
    @task.process_c
  ]
  
  join: @task.combine_results
  join_strategy: "wait_all"  # wait_all | wait_any | wait_n(2)
}
```

### Loop Flow

```chord
def flow iterative {
  entry: @task.init
  
  loop: {
    task: @task.process_item
    over: @signal.items
    as: "current_item"
    parallel: 3  # Process 3 items concurrently
  }
  
  exit: @task.finalize
}
```

## Error Handling

### Try-Catch

```chord
def flow robust {
  try: {
    task: @task.risky_operation
    timeout: 30000
  }
  
  catch: {
    on_timeout: @task.handle_timeout
    on_error: @task.handle_error
    on_rate_limit: {
      wait: 60000
      retry: @task.risky_operation
    }
  }
  
  finally: @task.cleanup
}
```

### Retry Logic

```chord
def policy retry_policy {
  retry: {
    max_attempts: 3
    backoff: "exponential"  # constant | linear | exponential
    initial_delay: 1000
    max_delay: 30000
    
    retry_on: ["timeout", "rate_limit", "5xx_error"]
    abort_on: ["invalid_input", "403_error"]
  }
}
```

## Validation

### Schema Validation

```chord
def task validated_input {
  inputs: {
    email: {
      type: "string"
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      required: true
    }
    age: {
      type: "number"
      min: 0
      max: 150
      required: false
      default: null
    }
    tags: {
      type: "array"
      items: "string"
      min_items: 1
      max_items: 10
      unique: true
    }
  }
}
```

### Assertions

```chord
def view validated_view {
  asserts: [
    # Simple assertions
    "response != null",
    "response.code compiles",
    "response.tests.length > 0",
    
    # Complex assertions
    {
      condition: "response.performance.latency < 100",
      message: "Latency too high"
    },
    {
      condition: "response.coverage > 0.8",
      severity: "warning"  # info | warning | error
    }
  ]
}
```

## Metadata

### Node Metadata

```chord
def task example {
  @meta: {
    author: "team@example.com"
    version: "1.2.0"
    deprecated: false
    tags: ["production", "critical"]
    created: "2024-01-01T00:00:00Z"
    modified: "2024-01-15T10:30:00Z"
  }
  
  objective: "Example task"
}
```

### File Metadata

```chord
@file: {
  version: "1.0.0"
  chord_version: "1.0"
  description: "Authentication flow orchestration"
  imports: [
    "common/roles.chord",
    "common/policies.chord"
  ]
}
```

## Imports and Includes

### Import Syntax

```chord
# Import entire file
import "path/to/file.chord"

# Import specific nodes
import { task1, task2, role1 } from "path/to/file.chord"

# Import with alias
import "path/to/file.chord" as auth

# Use imported nodes
def view my_view {
  task: @auth.task1  # Using alias
  role: @role1       # Direct import
}
```

### Include Syntax

```chord
# Include file contents (merge into current namespace)
include "common/shared_definitions.chord"

# Conditional include
include "dev_config.chord" when { environment: "development" }
include "prod_config.chord" when { environment: "production" }
```

## Built-in Functions

### String Functions

```chord
length(string): number
substring(string, start, end): string
replace(string, search, replacement): string
split(string, delimiter): array
trim(string): string
```

### Array Functions

```chord
length(array): number
first(array): any
last(array): any
slice(array, start, end): array
concat(array1, array2): array
unique(array): array
```

### Math Functions

```chord
min(a, b): number
max(a, b): number
abs(number): number
round(number, decimals): number
floor(number): number
ceil(number): number
```

### Date Functions

```chord
now(): timestamp
date(string): date
format_date(date, format): string
add_days(date, days): date
diff_days(date1, date2): number
```

## Reserved Keywords

The following words are reserved and cannot be used as identifiers:

```
def, ctx, cap, role, policy, model, task, flow, view, signal,
memory, hook, test, cache, import, include, from, as, when,
if, else, for, while, try, catch, finally, true, false, null,
and, or, not, in, is, return, break, continue
```

## Escape Sequences

In string literals:

| Sequence | Meaning |
|----------|---------|
| `\\` | Backslash |
| `\"` | Double quote |
| `\n` | Newline |
| `\r` | Carriage return |
| `\t` | Tab |
| `\b` | Backspace |
| `\f` | Form feed |
| `\uXXXX` | Unicode character |
| `\xXX` | Hexadecimal character |

## Regular Expressions

CHORD uses PCRE-compatible regular expressions:

```chord
# Basic pattern matching
pattern: "^[A-Z][a-z]+$"

# With flags
pattern: "/hello/i"  # Case insensitive
pattern: "/^test/m"  # Multiline
pattern: "/\\s+/g"   # Global

# Named groups
pattern: "(?P<year>\\d{4})-(?P<month>\\d{2})-(?P<day>\\d{2})"
```

## Grammar (BNF)

```bnf
<chord_file> ::= <metadata>? <statement>*

<statement> ::= <import_stmt> | <include_stmt> | <definition>

<definition> ::= "def" <node_type> <identifier> "{" <properties> "}"

<properties> ::= (<property> | <metadata>)*

<property> ::= <identifier> ":" <value>

<value> ::= <primitive> | <array> | <object> | <reference> | <template>

<primitive> ::= <string> | <number> | <boolean> | "null"

<array> ::= "[" <value_list>? "]"

<object> ::= "{" <property_list>? "}"

<reference> ::= "@" <identifier> ("." <identifier>)*

<template> ::= <string> ("{{" <expression> "}}")*
```

## File Organization

### Recommended Structure

```
project/
├── chord.config.json       # Global configuration
├── main.chord             # Entry point
├── contexts/              # Context definitions
│   ├── codebase.chord
│   ├── documentation.chord
│   └── apis.chord
├── capabilities/          # Capability definitions
│   ├── functions.chord
│   └── tools.chord
├── orchestration/         # Flows and views
│   ├── flows/
│   │   └── main_flow.chord
│   └── views/
│       └── prompts.chord
├── policies/              # Policies and roles
│   ├── roles.chord
│   └── policies.chord
├── models/                # Model configurations
│   └── models.chord
└── tests/                 # Test definitions
    ├── unit/
    └── integration/
```

## Naming Conventions

### Identifiers

- Node IDs: `snake_case` (e.g., `user_context`, `main_task`)
- Properties: `snake_case` (e.g., `max_tokens`, `input_files`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)

### Files

- Definition files: `descriptive_name.chord`
- Test files: `test_*.chord` or `*.test.chord`
- Config files: `*.config.chord`

## Version Compatibility

```chord
@file: {
  chord_version: "1.0"  # Minimum CHORD version required
  
  compatibility: {
    forward: true  # Can be used with newer versions
    strict: false  # Relaxed parsing mode
  }
}
```