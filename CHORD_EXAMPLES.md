# CHORD Examples

Real-world examples demonstrating CHORD's capabilities across different use cases.

## Table of Contents

1. [Code Review System](#code-review-system)
2. [API Documentation Generator](#api-documentation-generator)
3. [Bug Fix Workflow](#bug-fix-workflow)
4. [Data Pipeline Orchestration](#data-pipeline-orchestration)
5. [Multi-Language Translation](#multi-language-translation)
6. [Security Audit Pipeline](#security-audit-pipeline)
7. [Test Generation Suite](#test-generation-suite)
8. [Refactoring Assistant](#refactoring-assistant)
9. [Documentation Q&A System](#documentation-qa-system)
10. [Performance Optimization Flow](#performance-optimization-flow)

---

## Code Review System

A comprehensive code review system that analyzes PRs, checks security, and suggests improvements.

```chord
# ===== contexts.chord =====
def ctx pull_request {
  type: repo
  uri: "git+ssh://github.com/{{signal.org}}/{{signal.repo}}.git"
  branch: "{{signal.pr_branch}}"
  watch: true
}

def ctx main_branch {
  type: repo
  uri: "git+ssh://github.com/{{signal.org}}/{{signal.repo}}.git"
  branch: "main"
}

def ctx coding_standards {
  type: file
  uri: "fs:///standards/coding_guidelines.md"
  tags: ["standards", "reference"]
}

# ===== models.chord =====
def model reviewer {
  provider: "anthropic"
  id: "claude-3-opus-20240229"
  context_window: 200000
  temperature: 0.3  # Lower temperature for consistent reviews
}

# ===== roles.chord =====
def role senior_reviewer {
  persona: "senior software engineer with 15 years experience"
  principles: [
    "focus on maintainability and readability",
    "security is non-negotiable",
    "performance matters but not prematurely",
    "tests are documentation"
  ]
  style: {
    tone: "constructive and educational"
    feedback: "specific with examples"
  }
}

# ===== tasks.chord =====
def task analyze_changes {
  objective: "Analyze PR changes and categorize by risk and complexity"
  inputs: {
    pr_branch: "string"
    base_branch: "string"
  }
  outputs: {
    changed_files: "array<string>"
    risk_level: "enum[low,medium,high,critical]"
    complexity_score: "number[1-10]"
    requires_security_review: "boolean"
  }
}

def task security_scan {
  objective: "Scan for security vulnerabilities and sensitive data exposure"
  inputs: {
    changed_files: "array<string>"
  }
  outputs: {
    vulnerabilities: "array<object>"
    secrets_exposed: "boolean"
    security_score: "number[0-100]"
  }
  constraints: [
    "check OWASP top 10",
    "scan for hardcoded credentials",
    "verify input validation",
    "check for SQL injection vectors"
  ]
}

def task suggest_improvements {
  objective: "Provide actionable improvement suggestions"
  inputs: {
    analysis: "@task.analyze_changes.outputs"
    security: "@task.security_scan.outputs"
  }
  outputs: {
    suggestions: "array<{file, line, issue, suggestion, priority}>"
    must_fix: "array<string>"
    nice_to_have: "array<string>"
  }
}

# ===== flow.chord =====
def flow code_review {
  entry: @task.analyze_changes
  
  edges: [
    {
      from: @task.analyze_changes,
      to: @task.security_scan,
      condition: "risk_level != 'low'"
    },
    {
      from: @task.analyze_changes,
      to: @task.suggest_improvements,
      condition: "risk_level == 'low'"
    },
    {
      from: @task.security_scan,
      to: @task.alert_security_team,
      condition: "security_score < 70 || secrets_exposed"
    },
    {
      from: @task.security_scan,
      to: @task.suggest_improvements,
      condition: "security_score >= 70 && !secrets_exposed"
    }
  ]
  
  error_handling: {
    on_timeout: "summarize_partial_results"
    on_rate_limit: "queue_for_retry"
  }
}

# ===== views.chord =====
def view comprehensive_review {
  task: @task.suggest_improvements
  role: @role.senior_reviewer
  model: @model.reviewer
  policy: @policy.code_review
  
  selectors: [
    # Get the diff
    {
      from: @ctx.pull_request,
      op: "diff",
      base: @ctx.main_branch,
      context_lines: 5,
      format: "unified"
    },
    # Extract relevant coding standards
    {
      from: @ctx.coding_standards,
      op: "semantic_search",
      query: "{{changed_files | extract_concepts}}",
      top_k: 5
    },
    # Get test coverage for changed files
    {
      from: @ctx.pull_request,
      op: "exec",
      command: "coverage report --include={{changed_files | join(',')}}",
      format: "parse_coverage"
    },
    # Find similar past issues
    {
      from: @ctx.issue_database,
      op: "vector_search",
      query: "{{analysis.summary}}",
      top_k: 3,
      min_similarity: 0.7
    }
  ]
  
  prompt: {
    system: |
      You are {{role.persona}} conducting a thorough code review.
      Apply these principles: {{role.principles | bulletize}}
      Focus on: security, performance, maintainability, and test coverage.
    
    developer: |
      ## PR Analysis
      Risk Level: {{analysis.risk_level}}
      Complexity: {{analysis.complexity_score}}/10
      Security Score: {{security.security_score}}/100
      
      ## Changed Files
      {{changed_files | format_file_tree}}
      
      ## Diff
      {{resolved_context.diff | syntax_highlight}}
      
      ## Relevant Standards
      {{resolved_context.standards | format_sections}}
      
      ## Test Coverage
      {{resolved_context.coverage | format_table}}
    
    user: |
      Review this pull request and provide:
      1. Must-fix issues (blocking)
      2. Suggestions for improvement (non-blocking)
      3. Commendations for good practices
      
      Format as actionable comments with file:line references.
  }
  
  response_format: {
    type: "structured"
    schema: {
      must_fix: "array<{file, line, issue, fix, reason}>",
      suggestions: "array<{file, line, suggestion, benefit}>",
      commendations: "array<{file, line, practice, why_good}>",
      overall_assessment: "string",
      approved: "boolean"
    }
  }
}
```

---

## API Documentation Generator

Automatically generates comprehensive API documentation from code.

```chord
# ===== api_doc_generator.chord =====

def ctx api_codebase {
  type: dir
  uri: "fs:///project/src/api"
  include: ["**/*.py", "**/*.js", "**/*.ts"]
  exclude: ["**/*.test.*", "**/*.spec.*"]
}

def ctx existing_docs {
  type: dir
  uri: "fs:///project/docs/api"
  include: ["**/*.md"]
}

def ctx openapi_spec {
  type: file
  uri: "fs:///project/openapi.yaml"
}

def model doc_writer {
  provider: "openai"
  id: "gpt-4-turbo-preview"
  temperature: 0.3
  context_window: 128000
}

def role technical_writer {
  persona: "experienced technical writer specializing in API documentation"
  principles: [
    "clarity over brevity",
    "examples are essential",
    "consider the developer journey",
    "document edge cases and errors"
  ]
  style: {
    format: "markdown"
    tone: "professional yet approachable"
    structure: "hierarchical with clear navigation"
  }
}

def task extract_endpoints {
  objective: "Extract all API endpoints and their metadata"
  outputs: {
    endpoints: "array<{method, path, handler, params, returns}>"
    models: "array<{name, fields, validation}>"
    authentication: "object"
  }
}

def task generate_endpoint_docs {
  objective: "Generate documentation for each endpoint"
  inputs: {
    endpoint: "object"
    models: "array"
  }
  outputs: {
    documentation: "markdown"
    examples: "array<{request, response}>"
    errors: "array<{code, message, cause}>"
  }
}

def view endpoint_documenter {
  task: @task.generate_endpoint_docs
  role: @role.technical_writer
  model: @model.doc_writer
  
  selectors: [
    # Extract endpoint implementation
    {
      from: @ctx.api_codebase,
      op: "ast_extract",
      symbol: "{{endpoint.handler}}",
      include_decorators: true,
      include_docstring: true
    },
    # Find related models
    {
      from: @ctx.api_codebase,
      op: "find_references",
      symbols: "{{endpoint.params | extract_types}}",
      context: "definition"
    },
    # Get existing documentation if any
    {
      from: @ctx.existing_docs,
      op: "search",
      query: "{{endpoint.path}}",
      max_results: 1
    },
    # Extract from OpenAPI spec
    {
      from: @ctx.openapi_spec,
      op: "extract",
      path: "paths.{{endpoint.path | escape_json_path}}"
    },
    # Find usage examples in tests
    {
      from: @ctx.api_codebase,
      op: "grep",
      pattern: "{{endpoint.path | regex_escape}}",
      include: "**/*.test.*",
      context: 10
    }
  ]
  
  prompt: {
    system: |
      Generate comprehensive API documentation following these guidelines:
      {{role.principles | bulletize}}
      Use {{role.style.format}} format with {{role.style.tone}} tone.
    
    developer: |
      ## Endpoint: {{endpoint.method}} {{endpoint.path}}
      
      ### Implementation
      ```{{endpoint.language}}
      {{resolved_context.implementation}}
      ```
      
      ### Related Models
      {{resolved_context.models | format_model_definitions}}
      
      ### OpenAPI Definition
      {{resolved_context.openapi | format_yaml}}
      
      ### Test Examples
      {{resolved_context.tests | format_code_blocks}}
    
    user: |
      Generate complete documentation for this endpoint including:
      1. Description and purpose
      2. Request parameters (path, query, body)
      3. Response format and status codes
      4. Authentication requirements
      5. Rate limiting information
      6. Multiple examples (success and error cases)
      7. Common pitfalls and best practices
      8. Related endpoints
  }
}

def flow generate_api_docs {
  entry: @task.extract_endpoints
  
  loop: {
    over: "@task.extract_endpoints.outputs.endpoints"
    as: "endpoint"
    task: @task.generate_endpoint_docs
    parallel: 5
  }
  
  exit: @task.compile_documentation
}
```

---

## Bug Fix Workflow

Automated bug analysis and fix generation with validation.

```chord
# ===== bug_fix_workflow.chord =====

def ctx bug_report {
  type: api
  uri: "https://api.github.com/repos/{{org}}/{{repo}}/issues/{{issue_id}}"
  headers: {
    Authorization: "Bearer {{env.GITHUB_TOKEN}}"
  }
}

def ctx error_logs {
  type: stream
  uri: "elasticsearch://logs.company.com/errors"
  query: {
    issue_id: "{{signal.issue_id}}"
    time_range: "last_7_days"
  }
}

def ctx codebase {
  type: repo
  uri: "git+ssh://github.com/{{org}}/{{repo}}.git"
  branch: "main"
  sparse_checkout: ["src/", "tests/"]
}

def task analyze_bug {
  objective: "Understand the bug's root cause and impact"
  inputs: {
    bug_report: "@ctx.bug_report"
    error_logs: "@ctx.error_logs"
  }
  outputs: {
    root_cause: "string"
    affected_files: "array<string>"
    severity: "enum[low,medium,high,critical]"
    reproduction_steps: "array<string>"
  }
}

def task generate_fix {
  objective: "Generate a fix for the identified bug"
  inputs: {
    analysis: "@task.analyze_bug.outputs"
    codebase: "@ctx.codebase"
  }
  outputs: {
    changes: "array<{file, diff}>"
    explanation: "string"
    risk_assessment: "object"
  }
}

def task create_tests {
  objective: "Create tests that verify the fix"
  inputs: {
    bug_analysis: "@task.analyze_bug.outputs"
    fix: "@task.generate_fix.outputs"
  }
  outputs: {
    test_files: "array<{path, content}>"
    test_plan: "markdown"
  }
}

def task validate_fix {
  objective: "Validate the fix doesn't break existing functionality"
  inputs: {
    fix: "@task.generate_fix.outputs"
    tests: "@task.create_tests.outputs"
  }
  outputs: {
    tests_pass: "boolean"
    coverage_delta: "number"
    performance_impact: "object"
    breaking_changes: "array"
  }
}

def flow bug_fix_pipeline {
  entry: @task.analyze_bug
  
  edges: [
    {
      from: @task.analyze_bug,
      to: @task.generate_fix
    },
    {
      from: @task.generate_fix,
      to: @task.create_tests
    },
    {
      from: @task.create_tests,
      to: @task.validate_fix
    },
    {
      from: @task.validate_fix,
      to: @task.create_pr,
      condition: "tests_pass && breaking_changes.length == 0"
    },
    {
      from: @task.validate_fix,
      to: @task.request_review,
      condition: "!tests_pass || breaking_changes.length > 0"
    }
  ]
  
  error_handling: {
    on_test_failure: {
      action: "retry_with_different_approach"
      max_attempts: 3
    }
  }
}

def view bug_analyzer {
  task: @task.analyze_bug
  model: @model.claude_opus
  role: @role.senior_debugger
  
  selectors: [
    # Get bug report
    {
      from: @ctx.bug_report,
      op: "extract",
      fields: ["title", "description", "labels", "comments"]
    },
    # Analyze error patterns
    {
      from: @ctx.error_logs,
      op: "aggregate",
      group_by: "error_type",
      metrics: ["count", "first_seen", "last_seen"]
    },
    # Find similar past bugs
    {
      from: @ctx.bug_database,
      op: "semantic_search",
      query: "{{bug_report.title}} {{bug_report.description}}",
      top_k: 5
    },
    # Get stack traces
    {
      from: @ctx.error_logs,
      op: "extract",
      field: "stack_trace",
      unique: true,
      limit: 10
    }
  ]
  
  prompt: {
    system: |
      You are an expert debugger. Analyze bugs systematically:
      1. Identify symptoms
      2. Form hypotheses
      3. Find root cause
      4. Assess impact
      5. Suggest fix approach
    
    developer: |
      ## Bug Report
      Title: {{bug_report.title}}
      Description: {{bug_report.description}}
      
      ## Error Patterns
      {{resolved_context.error_patterns | format_table}}
      
      ## Stack Traces
      {{resolved_context.stack_traces | format_code}}
      
      ## Similar Past Bugs
      {{resolved_context.similar_bugs | format_list}}
    
    user: |
      Analyze this bug and provide:
      1. Root cause analysis
      2. Affected components
      3. Reproduction steps
      4. Severity assessment
      5. Recommended fix approach
  }
}
```

---

## Data Pipeline Orchestration

Complex ETL pipeline with multiple data sources and transformations.

```chord
# ===== data_pipeline.chord =====

def ctx raw_data {
  type: api
  uri: "https://api.datasource.com/v2/export"
  auth: {
    type: "oauth2"
    token: "{{env.API_TOKEN}}"
  }
  pagination: {
    type: "cursor"
    page_size: 1000
  }
}

def ctx database {
  type: database
  uri: "postgresql://{{env.DB_HOST}}/analytics"
  credentials: {
    user: "{{env.DB_USER}}"
    password: "{{env.DB_PASSWORD}}"
  }
}

def ctx s3_bucket {
  type: storage
  uri: "s3://data-lake/raw/{{signal.date}}"
  region: "us-east-1"
}

def task extract_data {
  objective: "Extract data from multiple sources"
  outputs: {
    raw_records: "array"
    metadata: {
      source: "string"
      timestamp: "datetime"
      record_count: "number"
    }
  }
  retry: {
    max_attempts: 3
    backoff: "exponential"
  }
}

def task transform_data {
  objective: "Clean, validate, and transform data"
  inputs: {
    raw_data: "@task.extract_data.outputs.raw_records"
  }
  outputs: {
    transformed: "array"
    validation_report: {
      valid: "number"
      invalid: "number"
      errors: "array"
    }
  }
  constraints: [
    "remove duplicates",
    "validate required fields",
    "normalize date formats",
    "handle missing values according to business rules"
  ]
}

def task load_data {
  objective: "Load transformed data into target systems"
  inputs: {
    data: "@task.transform_data.outputs.transformed"
  }
  outputs: {
    loaded_count: "number"
    destination: "string"
    load_time: "duration"
  }
}

def flow etl_pipeline {
  schedule: "0 2 * * *"  # Daily at 2 AM
  
  parallel: [
    {
      name: "api_extract"
      task: @task.extract_data
      config: { source: @ctx.raw_data }
    },
    {
      name: "db_extract"
      task: @task.extract_data
      config: { source: @ctx.database }
    }
  ]
  
  sequential: [
    {
      name: "merge_sources"
      task: @task.merge_data
      inputs: ["api_extract.outputs", "db_extract.outputs"]
    },
    {
      name: "transform"
      task: @task.transform_data
      inputs: ["merge_sources.outputs"]
    },
    {
      name: "quality_check"
      task: @task.data_quality_check
      inputs: ["transform.outputs"]
    }
  ]
  
  conditional: [
    {
      condition: "quality_check.pass_rate > 0.95"
      path: [
        @task.load_to_warehouse,
        @task.update_dashboards,
        @task.send_success_notification
      ]
    },
    {
      condition: "quality_check.pass_rate <= 0.95"
      path: [
        @task.quarantine_bad_data,
        @task.alert_data_team,
        @task.generate_quality_report
      ]
    }
  ]
  
  cleanup: @task.archive_raw_data
}

def view data_transformer {
  task: @task.transform_data
  model: @model.gpt4_turbo
  
  selectors: [
    # Get transformation rules
    {
      from: @ctx.transformation_rules,
      op: "extract",
      section: "{{signal.data_type}}_rules"
    },
    # Get data schema
    {
      from: @ctx.schema_registry,
      op: "lookup",
      schema: "{{signal.target_schema}}"
    },
    # Sample of raw data
    {
      from: @input.raw_data,
      op: "sample",
      size: 100,
      strategy: "stratified"
    }
  ]
  
  prompt: {
    developer: |
      ## Transformation Rules
      {{resolved_context.rules | format_yaml}}
      
      ## Target Schema
      {{resolved_context.schema | format_json_schema}}
      
      ## Data Sample
      {{resolved_context.sample | format_table}}
    
    user: |
      Generate Python code to transform this data according to the rules.
      Include:
      1. Data validation
      2. Type conversions
      3. Business logic transformations
      4. Error handling
      5. Logging
  }
}
```

---

## Multi-Language Translation

Translates and localizes content across multiple languages with context awareness.

```chord
# ===== translation_system.chord =====

def ctx source_content {
  type: dir
  uri: "fs:///content/en"
  include: ["**/*.md", "**/*.json"]
  watch: true
}

def ctx translation_memory {
  type: database
  uri: "mongodb://translations.db/memory"
  index: ["source_hash", "target_language"]
}

def ctx glossary {
  type: file
  uri: "fs:///localization/glossary.json"
  schema: {
    terms: "array<{source, target, context, notes}>"
  }
}

def model translator {
  provider: "anthropic"
  id: "claude-3-opus-20240229"
  temperature: 0.3
}

def role localizer {
  persona: "professional translator and localization expert"
  principles: [
    "preserve meaning over literal translation",
    "maintain consistent terminology",
    "respect cultural context",
    "adapt idioms appropriately"
  ]
  languages: ["en", "es", "fr", "de", "ja", "zh"]
}

def task detect_changes {
  objective: "Identify content that needs translation"
  outputs: {
    changed_files: "array<string>"
    new_strings: "array<{file, key, text}>"
    modified_strings: "array<{file, key, old, new}>"
  }
}

def task translate_content {
  objective: "Translate content to target language"
  inputs: {
    source_text: "string"
    source_lang: "string"
    target_lang: "string"
    context: "object"
  }
  outputs: {
    translation: "string"
    confidence: "number[0-1]"
    notes: "array<string>"
  }
}

def task validate_translation {
  objective: "Validate translation quality and consistency"
  inputs: {
    source: "string"
    translation: "string"
    language_pair: "object"
  }
  outputs: {
    quality_score: "number[0-100]"
    issues: "array<{type, severity, suggestion}>"
    approved: "boolean"
  }
}

def flow localization_pipeline {
  trigger: "on_content_change"
  
  entry: @task.detect_changes
  
  parallel_for: {
    each: "target_language in @config.languages"
    do: [
      {
        task: @task.check_translation_memory
        inputs: { lang: "target_language" }
      },
      {
        task: @task.translate_content
        condition: "!found_in_memory"
        inputs: { target_lang: "target_language" }
      },
      {
        task: @task.validate_translation
        inputs: { translation: "@task.translate_content.outputs" }
      }
    ]
  }
  
  converge: @task.compile_translations
  
  quality_gate: {
    condition: "all_validations_passed"
    pass: @task.publish_translations
    fail: @task.request_human_review
  }
}

def view context_aware_translator {
  task: @task.translate_content
  role: @role.localizer
  model: @model.translator
  
  selectors: [
    # Get surrounding context
    {
      from: @ctx.source_content,
      op: "extract",
      file: "{{input.file}}",
      lines_before: 10,
      lines_after: 10
    },
    # Lookup in translation memory
    {
      from: @ctx.translation_memory,
      op: "query",
      filter: {
        source_hash: "{{hash(input.source_text)}}",
        target_lang: "{{input.target_lang}}"
      },
      limit: 5
    },
    # Get relevant glossary terms
    {
      from: @ctx.glossary,
      op: "search",
      text: "{{input.source_text}}",
      language: "{{input.target_lang}}"
    },
    # Find similar translations
    {
      from: @ctx.translation_memory,
      op: "semantic_search",
      query: "{{input.source_text}}",
      filter: { target_lang: "{{input.target_lang}}" },
      top_k: 3
    }
  ]
  
  prompt: {
    system: |
      You are a professional translator specializing in software localization.
      Translate from {{input.source_lang}} to {{input.target_lang}}.
      
      Guidelines:
      {{role.principles | bulletize}}
      
      Maintain consistency with the glossary and previous translations.
    
    developer: |
      ## Source Text
      {{input.source_text}}
      
      ## Context
      File: {{input.file}}
      Type: {{input.content_type}}
      
      ## Surrounding Content
      {{resolved_context.surrounding | format_with_line_numbers}}
      
      ## Glossary Terms
      {{resolved_context.glossary | format_table}}
      
      ## Similar Translations
      {{resolved_context.similar | format_translation_pairs}}
    
    user: |
      Translate this text to {{input.target_lang}}:
      "{{input.source_text}}"
      
      Consider:
      1. The context in which this appears
      2. Technical terminology consistency
      3. Cultural appropriateness
      4. Natural flow in the target language
      
      Provide the translation and any notes about choices made.
  }
}
```

---

## Security Audit Pipeline

Comprehensive security scanning and vulnerability assessment.

```chord
# ===== security_audit.chord =====

def ctx application_code {
  type: repo
  uri: "git+ssh://github.com/{{org}}/{{repo}}.git"
  branch: "{{signal.branch}}"
}

def ctx dependencies {
  type: files
  paths: [
    "package.json",
    "requirements.txt",
    "Gemfile",
    "go.mod",
    "pom.xml"
  ]
}

def ctx security_rules {
  type: api
  uri: "https://security.company.com/api/rules"
  cache: {
    ttl: 3600
    key: "security_rules_{{version}}"
  }
}

def cap static_analyzer {
  type: tool
  command: "semgrep"
  args: ["--config=auto", "--json"]
}

def cap dependency_scanner {
  type: tool
  command: "snyk"
  args: ["test", "--json"]
}

def cap secret_scanner {
  type: tool
  command: "trufflehog"
  args: ["filesystem", ".", "--json"]
}

def task scan_code {
  objective: "Perform static analysis on source code"
  capabilities: [@cap.static_analyzer]
  outputs: {
    vulnerabilities: "array<object>"
    code_quality_issues: "array<object>"
    complexity_metrics: "object"
  }
}

def task scan_dependencies {
  objective: "Check dependencies for known vulnerabilities"
  capabilities: [@cap.dependency_scanner]
  outputs: {
    vulnerable_packages: "array<object>"
    severity_counts: "object"
    remediation_paths: "array<object>"
  }
}

def task scan_secrets {
  objective: "Detect exposed secrets and credentials"
  capabilities: [@cap.secret_scanner]
  outputs: {
    exposed_secrets: "array<object>"
    false_positives: "array<object>"
  }
}

def task generate_report {
  objective: "Generate comprehensive security report"
  inputs: {
    code_scan: "@task.scan_code.outputs"
    dependency_scan: "@task.scan_dependencies.outputs"
    secret_scan: "@task.scan_secrets.outputs"
  }
  outputs: {
    report: "markdown"
    risk_score: "number[0-100]"
    priority_fixes: "array<object>"
  }
}

def flow security_audit {
  trigger: {
    events: ["push", "pull_request", "schedule"]
    schedule: "0 0 * * 1"  # Weekly on Monday
  }
  
  parallel: [
    @task.scan_code,
    @task.scan_dependencies,
    @task.scan_secrets,
    @task.check_compliance,
    @task.penetration_test
  ]
  
  converge: @task.aggregate_findings
  
  decision: {
    critical_vulnerabilities: {
      condition: "any_critical_findings"
      actions: [
        @task.block_deployment,
        @task.create_incident,
        @task.notify_security_team
      ]
    },
    high_vulnerabilities: {
      condition: "high_findings && !critical_findings"
      actions: [
        @task.create_tickets,
        @task.notify_developers
      ]
    },
    clean: {
      condition: "no_high_or_critical_findings"
      actions: [
        @task.approve_deployment,
        @task.update_dashboard
      ]
    }
  }
  
  finally: @task.generate_report
}

def view vulnerability_analyzer {
  task: @task.analyze_vulnerability
  model: @model.security_expert
  
  selectors: [
    # Get vulnerability details
    {
      from: @ctx.vulnerability_db,
      op: "lookup",
      cve: "{{vulnerability.cve}}"
    },
    # Get affected code
    {
      from: @ctx.application_code,
      op: "extract",
      file: "{{vulnerability.file}}",
      lines: "{{vulnerability.line_range}}"
    },
    # Find exploit information
    {
      from: @ctx.exploit_db,
      op: "search",
      cve: "{{vulnerability.cve}}",
      include: ["poc", "in_the_wild"]
    },
    # Get remediation guidance
    {
      from: @ctx.security_rules,
      op: "query",
      type: "{{vulnerability.type}}",
      language: "{{vulnerability.language}}"
    }
  ]
  
  prompt: {
    developer: |
      ## Vulnerability: {{vulnerability.title}}
      CVE: {{vulnerability.cve}}
      Severity: {{vulnerability.severity}}
      
      ## Affected Code
      ```{{vulnerability.language}}
      {{resolved_context.affected_code}}
      ```
      
      ## Vulnerability Details
      {{resolved_context.cve_details | format_security_advisory}}
      
      ## Exploit Information
      {{resolved_context.exploits | format_threat_intelligence}}
    
    user: |
      Analyze this security vulnerability and provide:
      1. Detailed explanation of the vulnerability
      2. Attack vectors and potential impact
      3. Proof of concept (if applicable)
      4. Remediation steps with code examples
      5. Prevention strategies
      6. Testing approach to verify the fix
  }
}
```

---

## Test Generation Suite

Automatically generates comprehensive test suites for code.

```chord
# ===== test_generation.chord =====

def ctx source_code {
  type: dir
  uri: "fs:///project/src"
  include: ["**/*.py", "**/*.js", "**/*.java"]
  exclude: ["**/*.test.*", "**/*.spec.*"]
}

def ctx existing_tests {
  type: dir
  uri: "fs:///project/tests"
  include: ["**/*.test.*", "**/*.spec.*"]
}

def model test_generator {
  provider: "anthropic"
  id: "claude-3-opus-20240229"
  temperature: 0.2  # Low temperature for consistent test generation
}

def role test_engineer {
  persona: "senior QA engineer with TDD expertise"
  principles: [
    "test behavior, not implementation",
    "each test should test one thing",
    "tests should be readable and maintainable",
    "consider edge cases and error conditions"
  ]
  frameworks: {
    python: "pytest",
    javascript: "jest",
    java: "junit5"
  }
}

def task analyze_code {
  objective: "Analyze code to understand testing requirements"
  inputs: {
    file_path: "string"
  }
  outputs: {
    functions: "array<{name, params, returns, complexity}>"
    classes: "array<{name, methods, dependencies}>"
    coverage_gaps: "array<{type, location}>"
    suggested_test_cases: "array<{name, type, priority}>"
  }
}

def task generate_unit_tests {
  objective: "Generate unit tests for individual functions/methods"
  inputs: {
    code_analysis: "@task.analyze_code.outputs"
    target: "object"
  }
  outputs: {
    test_code: "string"
    test_cases: "array<{name, description, assertions}>"
    mocks_needed: "array<object>"
  }
}

def task generate_integration_tests {
  objective: "Generate tests for component interactions"
  inputs: {
    components: "array<object>"
    interactions: "array<object>"
  }
  outputs: {
    test_code: "string"
    test_scenarios: "array<object>"
    setup_teardown: "object"
  }
}

def view test_creator {
  task: @task.generate_unit_tests
  role: @role.test_engineer
  model: @model.test_generator
  
  selectors: [
    # Get the function/class to test
    {
      from: @ctx.source_code,
      op: "ast_extract",
      symbol: "{{target.name}}",
      include_body: true,
      include_dependencies: true
    },
    # Check existing tests
    {
      from: @ctx.existing_tests,
      op: "search",
      query: "{{target.name}}",
      include_context: true
    },
    # Get test patterns from similar code
    {
      from: @ctx.test_patterns,
      op: "semantic_search",
      query: "{{target.signature}}",
      top_k: 3
    },
    # Extract dependencies for mocking
    {
      from: @ctx.source_code,
      op: "analyze_dependencies",
      symbol: "{{target.name}}",
      depth: 1
    }
  ]
  
  prompt: {
    system: |
      You are {{role.persona}}.
      Generate tests using {{role.frameworks[target.language]}} framework.
      Follow these principles:
      {{role.principles | bulletize}}
    
    developer: |
      ## Code to Test
      ```{{target.language}}
      {{resolved_context.code}}
      ```
      
      ## Dependencies
      {{resolved_context.dependencies | format_list}}
      
      ## Existing Test Patterns
      {{resolved_context.patterns | format_code_blocks}}
      
      ## Coverage Gaps
      {{code_analysis.coverage_gaps | format_table}}
    
    user: |
      Generate comprehensive unit tests for {{target.name}} including:
      
      1. Happy path scenarios
      2. Edge cases (empty inputs, boundary values)
      3. Error conditions
      4. Invalid input handling
      5. Mock external dependencies
      6. Performance considerations if applicable
      
      Each test should:
      - Have a descriptive name
      - Test one specific behavior
      - Include clear assertions
      - Be independent of other tests
  }
  
  response_format: {
    type: "structured"
    schema: {
      imports: "array<string>"
      fixtures: "array<{name, code}>"
      test_class: {
        name: "string"
        setup: "string"
        teardown: "string"
        tests: "array<{name, docstring, code}>"
      }
    }
  }
}

def flow test_generation_pipeline {
  entry: @task.scan_for_untested_code
  
  foreach: {
    items: "@task.scan_for_untested_code.outputs.files"
    as: "file"
    do: [
      {
        task: @task.analyze_code
        inputs: { file_path: "file" }
      },
      {
        task: @task.generate_unit_tests
        condition: "functions.length > 0 || classes.length > 0"
      },
      {
        task: @task.generate_integration_tests
        condition: "has_external_dependencies"
      },
      {
        task: @task.validate_generated_tests
        inputs: { tests: "@task.generate_unit_tests.outputs" }
      }
    ]
  }
  
  aggregate: @task.compile_test_suite
  
  validation: {
    task: @task.run_test_suite
    success_criteria: {
      all_tests_pass: true
      no_syntax_errors: true
      coverage_increase: true
    }
  }
  
  output: @task.generate_test_report
}
```

---

## Refactoring Assistant

Helps refactor code for better maintainability and performance.

```chord
# ===== refactoring_assistant.chord =====

def ctx legacy_code {
  type: dir
  uri: "fs:///project/legacy"
  include: ["**/*.py"]
}

def ctx metrics {
  type: tool
  command: "radon"
  args: ["cc", "-j", "--min", "B"]  # Cyclomatic complexity
}

def task analyze_code_quality {
  objective: "Identify code that needs refactoring"
  outputs: {
    complexity_hotspots: "array<{file, function, complexity}>"
    code_smells: "array<{type, location, severity}>"
    duplication: "array<{files, lines, similarity}>"
    suggested_refactorings: "array<{type, target, benefit}>"
  }
}

def task plan_refactoring {
  objective: "Create a refactoring plan"
  inputs: {
    analysis: "@task.analyze_code_quality.outputs"
    constraints: {
      maintain_api: true
      preserve_behavior: true
      max_changes_per_pr: 10
    }
  }
  outputs: {
    refactoring_steps: "array<{order, type, target, description}>"
    risk_assessment: "object"
    estimated_impact: "object"
  }
}

def task execute_refactoring {
  objective: "Apply refactoring to code"
  inputs: {
    step: "object"
    code: "string"
  }
  outputs: {
    refactored_code: "string"
    changes_made: "array<string>"
    tests_to_update: "array<string>"
  }
}

def view refactoring_planner {
  task: @task.plan_refactoring
  model: @model.architect
  
  selectors: [
    # Get complexity metrics
    {
      from: @ctx.metrics,
      op: "exec",
      target: "{{analysis.complexity_hotspots | map('file') | unique}}"
    },
    # Get architectural patterns
    {
      from: @ctx.architecture_docs,
      op: "extract",
      sections: ["Design Patterns", "Best Practices"]
    },
    # Find similar successful refactorings
    {
      from: @ctx.refactoring_history,
      op: "query",
      filter: {
        code_smell: "{{analysis.code_smells | map('type') | unique}}",
        success: true
      }
    }
  ]
  
  prompt: {
    developer: |
      ## Code Quality Analysis
      
      ### Complexity Hotspots
      {{analysis.complexity_hotspots | format_complexity_table}}
      
      ### Code Smells
      {{analysis.code_smells | group_by('type') | format_sections}}
      
      ### Duplication
      {{analysis.duplication | format_duplication_report}}
      
      ## Constraints
      - Maintain API compatibility: {{constraints.maintain_api}}
      - Preserve behavior: {{constraints.preserve_behavior}}
      - Max changes per PR: {{constraints.max_changes_per_pr}}
    
    user: |
      Create a refactoring plan that:
      1. Prioritizes high-impact improvements
      2. Minimizes risk
      3. Can be executed incrementally
      4. Maintains backward compatibility
      5. Improves testability
      
      For each refactoring step, explain:
      - What pattern/technique to apply
      - Why it improves the code
      - Potential risks
      - How to verify correctness
  }
}

def flow incremental_refactoring {
  entry: @task.analyze_code_quality
  
  sequential: [
    @task.plan_refactoring,
    @task.create_refactoring_branch
  ]
  
  iterate: {
    over: "@task.plan_refactoring.outputs.refactoring_steps"
    as: "step"
    do: [
      @task.execute_refactoring,
      @task.update_tests,
      @task.run_tests,
      @task.measure_improvement
    ]
    checkpoint_after_each: true
    rollback_on_failure: true
  }
  
  validation: [
    @task.run_full_test_suite,
    @task.performance_regression_check,
    @task.api_compatibility_check
  ]
  
  completion: [
    @task.generate_pr,
    @task.document_changes
  ]
}
```

---

## Documentation Q&A System

Interactive Q&A system for technical documentation.

```chord
# ===== doc_qa_system.chord =====

def ctx documentation {
  type: dir
  uri: "fs:///docs"
  include: ["**/*.md", "**/*.rst", "**/*.html"]
  index: {
    type: "semantic"
    model: "text-embedding-ada-002"
    chunk_size: 500
    chunk_overlap: 50
  }
}

def ctx code_examples {
  type: repo
  uri: "git+ssh://github.com/{{org}}/examples.git"
  include: ["**/*.py", "**/*.js", "**/*.sh"]
}

def memory conversation {
  type: "conversational"
  max_turns: 10
  compression: {
    method: "summary"
    after_turns: 5
  }
}

def task understand_question {
  objective: "Parse and understand user question"
  inputs: {
    question: "string"
    context: "@memory.conversation"
  }
  outputs: {
    intent: "enum[how_to, troubleshooting, explanation, example]"
    entities: "array<{type, value}>"
    related_topics: "array<string>"
  }
}

def task retrieve_context {
  objective: "Find relevant documentation"
  inputs: {
    query_understanding: "@task.understand_question.outputs"
  }
  outputs: {
    relevant_docs: "array<{source, content, relevance}>"
    code_examples: "array<{file, code, description}>"
  }
}

def task generate_answer {
  objective: "Generate comprehensive answer"
  inputs: {
    question: "string"
    context: "@task.retrieve_context.outputs"
    conversation: "@memory.conversation"
  }
  outputs: {
    answer: "markdown"
    sources: "array<string>"
    follow_up_suggestions: "array<string>"
  }
}

def view qa_responder {
  task: @task.generate_answer
  model: @model.claude_opus
  role: @role.technical_writer
  
  selectors: [
    # Get relevant documentation
    {
      from: @ctx.documentation,
      op: "vector_search",
      query: "{{question}}",
      top_k: 5,
      threshold: 0.7
    },
    # Find code examples
    {
      from: @ctx.code_examples,
      op: "semantic_search",
      query: "{{question}} example implementation",
      top_k: 3
    },
    # Get related Q&As
    {
      from: @ctx.qa_history,
      op: "similar_questions",
      question: "{{question}}",
      limit: 3
    },
    # Extract glossary terms
    {
      from: @ctx.glossary,
      op: "extract_terms",
      text: "{{question}}"
    }
  ]
  
  prompt: {
    system: |
      You are a helpful technical documentation assistant.
      Provide clear, accurate, and comprehensive answers.
      Always cite sources and provide examples when helpful.
    
    developer: |
      ## User Question
      {{question}}
      
      ## Question Analysis
      Intent: {{query_understanding.intent}}
      Key Topics: {{query_understanding.entities | map('value') | join(', ')}}
      
      ## Relevant Documentation
      {{resolved_context.documentation | format_doc_sections}}
      
      ## Code Examples
      {{resolved_context.examples | format_code_examples}}
      
      ## Related Q&As
      {{resolved_context.related_qa | format_qa_pairs}}
      
      ## Conversation History
      {{conversation | format_conversation}}
    
    user: |
      Please answer this question: {{question}}
      
      Provide:
      1. A clear, direct answer
      2. Step-by-step instructions if applicable
      3. Code examples if relevant
      4. Links to detailed documentation
      5. Common pitfalls or gotchas
      6. Related topics they might want to explore
  }
}

def flow qa_interaction {
  entry: @task.understand_question
  
  pipeline: [
    @task.retrieve_context,
    @task.check_cache,
    {
      condition: "!cache_hit"
      task: @task.generate_answer
    },
    @task.validate_answer,
    @task.update_conversation_memory
  ]
  
  feedback_loop: {
    task: @task.collect_feedback
    on_negative: [
      @task.escalate_to_human,
      @task.log_for_improvement
    ]
  }
}
```

---

## Performance Optimization Flow

Identifies and fixes performance bottlenecks.

```chord
# ===== performance_optimization.chord =====

def ctx application {
  type: dir
  uri: "fs:///app"
  include: ["**/*.py", "**/*.sql", "**/*.yaml"]
}

def ctx metrics {
  type: api
  uri: "https://metrics.datadog.com/api/v1/query"
  auth: {
    api_key: "{{env.DD_API_KEY}}"
  }
}

def ctx profiling_data {
  type: storage
  uri: "s3://profiling-data/{{signal.date}}"
}

def task identify_bottlenecks {
  objective: "Find performance bottlenecks"
  inputs: {
    metrics: "@ctx.metrics"
    profiling: "@ctx.profiling_data"
  }
  outputs: {
    bottlenecks: "array<{type, location, impact, frequency}>"
    slow_queries: "array<{query, avg_time, count}>"
    memory_leaks: "array<{location, growth_rate}>"
    cpu_hotspots: "array<{function, cpu_time, calls}>"
  }
}

def task optimize_code {
  objective: "Generate optimized version of code"
  inputs: {
    bottleneck: "object"
    code: "string"
  }
  outputs: {
    optimized_code: "string"
    optimization_type: "string"
    expected_improvement: "percentage"
    trade_offs: "array<string>"
  }
}

def task benchmark {
  objective: "Compare performance before and after"
  inputs: {
    original: "string"
    optimized: "string"
    test_data: "object"
  }
  outputs: {
    improvement: {
      execution_time: "percentage"
      memory_usage: "percentage"
      cpu_usage: "percentage"
    }
    regression_risks: "array<string>"
  }
}

def view performance_optimizer {
  task: @task.optimize_code
  model: @model.claude_opus
  
  selectors: [
    # Get the bottleneck code
    {
      from: @ctx.application,
      op: "extract",
      file: "{{bottleneck.file}}",
      function: "{{bottleneck.function}}"
    },
    # Get profiling details
    {
      from: @ctx.profiling_data,
      op: "query",
      function: "{{bottleneck.function}}",
      metrics: ["time", "memory", "calls"]
    },
    # Find optimization patterns
    {
      from: @ctx.optimization_patterns,
      op: "lookup",
      problem_type: "{{bottleneck.type}}",
      language: "{{bottleneck.language}}"
    },
    # Check for similar optimizations
    {
      from: @ctx.optimization_history,
      op: "search",
      similar_to: "{{bottleneck.signature}}"
    }
  ]
  
  prompt: {
    developer: |
      ## Performance Bottleneck
      Type: {{bottleneck.type}}
      Impact: {{bottleneck.impact}}
      
      ## Current Code
      ```{{bottleneck.language}}
      {{resolved_context.code}}
      ```
      
      ## Profiling Data
      {{resolved_context.profiling | format_performance_metrics}}
      
      ## Applicable Optimization Patterns
      {{resolved_context.patterns | format_list}}
      
      ## Similar Past Optimizations
      {{resolved_context.history | format_optimization_cases}}
    
    user: |
      Optimize this code for better performance.
      
      Consider:
      1. Algorithm complexity improvements
      2. Data structure optimizations
      3. Caching opportunities
      4. Parallelization possibilities
      5. Database query optimization
      6. Memory usage reduction
      
      Provide:
      - Optimized code
      - Explanation of changes
      - Expected performance improvement
      - Any trade-offs or risks
  }
}

def flow optimization_pipeline {
  entry: @task.collect_performance_data
  
  analysis: [
    @task.identify_bottlenecks,
    @task.prioritize_optimizations
  ]
  
  iterate: {
    over: "@task.prioritize_optimizations.outputs.top_bottlenecks"
    as: "bottleneck"
    max_iterations: 5
    do: [
      @task.optimize_code,
      @task.generate_benchmarks,
      @task.run_benchmarks,
      {
        condition: "improvement > 20%"
        tasks: [
          @task.create_optimization_pr,
          @task.update_documentation
        ]
      }
    ]
  }
  
  validation: [
    @task.run_regression_tests,
    @task.load_test,
    @task.measure_overall_improvement
  ]
  
  monitoring: {
    task: @task.monitor_in_production
    duration: "7d"
    rollback_on: {
      error_rate_increase: "> 5%"
      latency_increase: "> 10%"
    }
  }
}
```

---

## Best Practices Demonstrated

These examples showcase:

1. **Separation of Concerns**: Clear distinction between contexts, capabilities, roles, tasks, and views
2. **Reusability**: Shared definitions across multiple flows
3. **Error Handling**: Robust error handling and fallback strategies
4. **Testing**: Built-in validation and testing at each step
5. **Monitoring**: Performance tracking and quality gates
6. **Documentation**: Self-documenting with clear objectives and constraints
7. **Scalability**: Parallel processing and efficient resource usage
8. **Security**: Security-first approach with validation and scanning
9. **Maintainability**: Modular design that's easy to update and extend
10. **Model Optimization**: Strategic model selection based on task requirements

Each example can be adapted and extended for specific use cases, demonstrating CHORD's flexibility and power in orchestrating complex LLM-driven workflows.