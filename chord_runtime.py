#!/usr/bin/env python3
"""
CHORD Runtime - Executes compiled CHORD IR with selector operations
"""

import os
import re
import json
import hashlib
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Runtime execution context"""
    signals: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    cache: Dict[str, Any] = field(default_factory=dict)
    resolved_contexts: Dict[str, Any] = field(default_factory=dict)
    
    def get_signal(self, name: str) -> Any:
        """Get signal value"""
        if name in self.signals:
            return self.signals[name]
        # Check environment variables
        env_name = f"CHORD_{name.upper()}"
        if env_name in os.environ:
            return os.environ[env_name]
        return None


class ContextSource(ABC):
    """Abstract base for context sources"""
    
    @abstractmethod
    async def fetch(self, uri: str, **kwargs) -> str:
        pass


class FileContextSource(ContextSource):
    """File system context source"""
    
    async def fetch(self, uri: str, **kwargs) -> str:
        if uri.startswith("fs://"):
            path = uri[5:]  # Remove fs:// prefix
        else:
            path = uri
        
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()


class DirectoryContextSource(ContextSource):
    """Directory context source"""
    
    async def fetch(self, uri: str, **kwargs) -> Dict[str, str]:
        if uri.startswith("fs://"):
            path = uri[5:]
        else:
            path = uri
        
        path = Path(path)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        
        include = kwargs.get('include', ['**/*'])
        exclude = kwargs.get('exclude', [])
        
        files = {}
        for pattern in include:
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    # Check exclusions
                    excluded = False
                    for exc_pattern in exclude:
                        if file_path.match(exc_pattern):
                            excluded = True
                            break
                    
                    if not excluded:
                        relative_path = file_path.relative_to(path)
                        with open(file_path, 'r', encoding='utf-8') as f:
                            files[str(relative_path)] = f.read()
        
        return files


class SelectorOperation(ABC):
    """Abstract base for selector operations"""
    
    @abstractmethod
    async def execute(self, data: Any, params: Dict[str, Any]) -> Any:
        pass


class HeadSelector(SelectorOperation):
    """Extract first N lines"""
    
    async def execute(self, data: str, params: Dict[str, Any]) -> str:
        lines = params.get('lines', 100)
        if isinstance(data, str):
            return '\n'.join(data.splitlines()[:lines])
        return data


class TailSelector(SelectorOperation):
    """Extract last N lines"""
    
    async def execute(self, data: str, params: Dict[str, Any]) -> str:
        lines = params.get('lines', 100)
        if isinstance(data, str):
            return '\n'.join(data.splitlines()[-lines:])
        return data


class ExtractSelector(SelectorOperation):
    """Extract specific sections or patterns"""
    
    async def execute(self, data: str, params: Dict[str, Any]) -> str:
        if 'sections' in params:
            # Extract markdown sections
            sections = params['sections']
            if not isinstance(sections, list):
                sections = [sections]
            
            extracted = []
            current_section = None
            current_content = []
            
            for line in data.splitlines():
                # Check if line is a header
                if line.startswith('#'):
                    # Save previous section if it matches
                    if current_section and any(s in current_section for s in sections):
                        extracted.append('\n'.join(current_content))
                    
                    current_section = line
                    current_content = [line]
                else:
                    current_content.append(line)
            
            # Check last section
            if current_section and any(s in current_section for s in sections):
                extracted.append('\n'.join(current_content))
            
            return '\n\n'.join(extracted)
        
        elif 'pattern' in params:
            # Extract using regex
            pattern = params['pattern']
            matches = re.findall(pattern, data, re.MULTILINE)
            return '\n'.join(matches)
        
        elif 'lines' in params:
            # Extract specific line range
            lines = data.splitlines()
            start = params.get('start', 0)
            end = params.get('end', len(lines))
            return '\n'.join(lines[start:end])
        
        return data


class GrepSelector(SelectorOperation):
    """Search for patterns in text"""
    
    async def execute(self, data: str, params: Dict[str, Any]) -> str:
        pattern = params.get('pattern', '')
        context_lines = params.get('context', 0)
        
        lines = data.splitlines()
        matches = []
        
        for i, line in enumerate(lines):
            if re.search(pattern, line):
                start = max(0, i - context_lines)
                end = min(len(lines), i + context_lines + 1)
                match_with_context = lines[start:end]
                matches.append('\n'.join(match_with_context))
        
        return '\n---\n'.join(matches)


class SummarizeSelector(SelectorOperation):
    """Summarize text (placeholder - would use LLM in production)"""
    
    async def execute(self, data: str, params: Dict[str, Any]) -> str:
        max_tokens = params.get('max_tokens', 500)
        
        # Simple truncation for demo - in production, use LLM
        words = data.split()
        # Rough estimate: 1 token ≈ 0.75 words
        max_words = int(max_tokens * 0.75)
        
        if len(words) <= max_words:
            return data
        
        truncated = ' '.join(words[:max_words])
        return f"{truncated}... [summarized from {len(words)} words]"


class TransformSelector(SelectorOperation):
    """Transform data format"""
    
    async def execute(self, data: Any, params: Dict[str, Any]) -> str:
        to_format = params.get('to', 'json')
        
        if to_format == 'json':
            if isinstance(data, str):
                try:
                    # Try to parse as JSON/dict
                    parsed = json.loads(data)
                    return json.dumps(parsed, indent=2)
                except:
                    return data
            else:
                return json.dumps(data, indent=2)
        
        elif to_format == 'yaml':
            # Simplified YAML output
            if isinstance(data, dict):
                lines = []
                for key, value in data.items():
                    if isinstance(value, (list, dict)):
                        lines.append(f"{key}:")
                        lines.append(f"  {json.dumps(value)}")
                    else:
                        lines.append(f"{key}: {value}")
                return '\n'.join(lines)
        
        return str(data)


class SemanticSearchSelector(SelectorOperation):
    """Semantic search (placeholder - would use embeddings in production)"""
    
    async def execute(self, data: str, params: Dict[str, Any]) -> str:
        query = params.get('query', '')
        top_k = params.get('top_k', 5)
        
        # Simple keyword matching for demo - in production, use embeddings
        lines = data.splitlines()
        query_words = set(query.lower().split())
        
        scored_lines = []
        for line in lines:
            line_words = set(line.lower().split())
            score = len(query_words.intersection(line_words))
            if score > 0:
                scored_lines.append((score, line))
        
        # Sort by score and return top K
        scored_lines.sort(key=lambda x: x[0], reverse=True)
        top_lines = [line for score, line in scored_lines[:top_k]]
        
        return '\n'.join(top_lines)


class SelectorRegistry:
    """Registry of selector operations"""
    
    def __init__(self):
        self.operations: Dict[str, SelectorOperation] = {
            'head': HeadSelector(),
            'tail': TailSelector(),
            'extract': ExtractSelector(),
            'grep': GrepSelector(),
            'summarize': SummarizeSelector(),
            'transform': TransformSelector(),
            'semantic_search': SemanticSearchSelector(),
            'search': SemanticSearchSelector(),  # Alias
        }
    
    def get(self, op_name: str) -> Optional[SelectorOperation]:
        return self.operations.get(op_name)
    
    def register(self, name: str, operation: SelectorOperation):
        self.operations[name] = operation


class ContextManager:
    """Manages context sources and caching"""
    
    def __init__(self):
        self.sources: Dict[str, ContextSource] = {
            'file': FileContextSource(),
            'dir': DirectoryContextSource(),
        }
        self.cache: Dict[str, Any] = {}
    
    async def fetch_context(self, node: Dict[str, Any]) -> Any:
        """Fetch context from a source"""
        ctx_type = node['properties'].get('type', 'file')
        uri = node['properties'].get('uri', '')
        
        # Check cache
        cache_key = f"{ctx_type}:{uri}"
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]
        
        # Fetch from source
        if ctx_type in self.sources:
            source = self.sources[ctx_type]
            data = await source.fetch(uri, **node['properties'])
            self.cache[cache_key] = data
            return data
        else:
            raise ValueError(f"Unknown context type: {ctx_type}")


class PromptRenderer:
    """Renders prompt templates"""
    
    def __init__(self, context: ExecutionContext):
        self.context = context
    
    def render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render a template with variables"""
        result = template
        
        # Simple template rendering - in production, use Jinja2 or similar
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in result:
                if isinstance(value, list):
                    # Handle list formatting
                    if '| bulletize' in result:
                        formatted = '\n'.join(f"• {item}" for item in value)
                        result = result.replace(f"{{{{{key} | bulletize}}}}", formatted)
                    elif '| join' in result:
                        # Extract separator
                        match = re.search(rf"{{{{{key} \| join\('(.+?)'\)}}}}", result)
                        if match:
                            sep = match.group(1)
                            formatted = sep.join(str(item) for item in value)
                            result = result.replace(match.group(0), formatted)
                    else:
                        result = result.replace(placeholder, str(value))
                else:
                    result = result.replace(placeholder, str(value))
        
        # Handle signals
        for signal_match in re.finditer(r'{{signal\.(\w+)}}', result):
            signal_name = signal_match.group(1)
            signal_value = self.context.get_signal(signal_name)
            if signal_value:
                result = result.replace(signal_match.group(0), str(signal_value))
        
        return result
    
    def render_prompt(self, prompt_config: Dict[str, str], resolved_context: Dict[str, Any]) -> Dict[str, str]:
        """Render all prompt sections"""
        rendered = {}
        
        variables = {
            'resolved_context': resolved_context,
            **self.context.signals
        }
        
        for section, template in prompt_config.items():
            if isinstance(template, str):
                rendered[section] = self.render_template(template, variables)
            else:
                rendered[section] = str(template)
        
        return rendered


class Runtime:
    """Main CHORD runtime engine"""
    
    def __init__(self, ir: Dict[str, Any]):
        self.ir = ir
        self.nodes = ir.get('nodes', {})
        self.views = ir.get('views', [])
        self.flows = ir.get('flows', [])
        self.context = ExecutionContext()
        self.selector_registry = SelectorRegistry()
        self.context_manager = ContextManager()
        self.prompt_renderer = PromptRenderer(self.context)
    
    def set_signal(self, name: str, value: Any):
        """Set a signal value"""
        self.context.signals[name] = value
    
    def set_signals(self, signals: Dict[str, Any]):
        """Set multiple signals"""
        self.context.signals.update(signals)
    
    async def execute_selector(self, selector: Dict[str, Any]) -> Any:
        """Execute a single selector"""
        from_ref = selector.get('from', '')
        op = selector.get('op', 'extract')
        
        # Resolve the source
        if from_ref.startswith('@'):
            node_id = from_ref[1:].split('.')[0]
            if node_id in self.nodes:
                node = self.nodes[node_id]
                if node['type'] == 'ctx':
                    # Fetch context
                    data = await self.context_manager.fetch_context(node)
                else:
                    data = node.get('properties', {})
            else:
                raise ValueError(f"Unknown node: {from_ref}")
        else:
            data = from_ref
        
        # Apply operation
        operation = self.selector_registry.get(op)
        if operation:
            return await operation.execute(data, selector)
        else:
            logger.warning(f"Unknown selector operation: {op}")
            return data
    
    async def resolve_selectors(self, selectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve all selectors for a view"""
        resolved = {}
        
        for selector in selectors:
            from_ref = selector.get('from', '')
            # Extract node ID for result key
            if from_ref.startswith('@'):
                key = from_ref[1:].split('.')[0]
            else:
                key = 'data'
            
            try:
                result = await self.execute_selector(selector)
                resolved[key] = result
            except Exception as e:
                logger.error(f"Error executing selector {selector}: {e}")
                resolved[key] = f"[Error: {e}]"
        
        return resolved
    
    async def execute_view(self, view_id: str) -> Dict[str, Any]:
        """Execute a view and generate prompt"""
        # Find view
        view = None
        for v in self.views:
            if v['id'] == view_id:
                view = v
                break
        
        if not view:
            raise ValueError(f"View not found: {view_id}")
        
        # Resolve selectors
        selectors = view.get('selectors', [])
        resolved_context = await self.resolve_selectors(selectors)
        
        # Get role and model info
        role_id = view.get('role', '')
        model_id = view.get('model', '')
        
        role = None
        model = None
        
        if role_id and role_id.startswith('@'):
            role_node_id = role_id[1:]
            if role_node_id in self.nodes:
                role = self.nodes[role_node_id]['properties']
        
        if model_id and model_id.startswith('@'):
            model_node_id = model_id[1:]
            if model_node_id in self.nodes:
                model = self.nodes[model_node_id]['properties']
        
        # Render prompt
        prompt_config = view.get('prompt', {})
        rendered_prompt = self.prompt_renderer.render_prompt(prompt_config, resolved_context)
        
        # Prepare result
        result = {
            'view_id': view_id,
            'task': view.get('task'),
            'role': role,
            'model': model,
            'resolved_context': resolved_context,
            'prompt': rendered_prompt,
            'response_format': view.get('response_format'),
            'asserts': view.get('asserts', [])
        }
        
        return result
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a task"""
        if task_id not in self.nodes:
            raise ValueError(f"Task not found: {task_id}")
        
        task = self.nodes[task_id]
        if task['type'] != 'task':
            raise ValueError(f"Node {task_id} is not a task")
        
        # Find views that reference this task
        task_views = []
        for view in self.views:
            if view.get('task') == f"@{task_id}":
                task_views.append(view['id'])
        
        if not task_views:
            logger.warning(f"No views found for task {task_id}")
            return {'task_id': task_id, 'status': 'no_views'}
        
        # Execute first view (in production, could execute all or select)
        view_result = await self.execute_view(task_views[0])
        
        return {
            'task_id': task_id,
            'task': task['properties'],
            'view_result': view_result
        }
    
    async def execute_flow(self, flow_id: str) -> Dict[str, Any]:
        """Execute a flow"""
        flow = None
        for f in self.flows:
            if f['id'] == flow_id:
                flow = f
                break
        
        if not flow:
            raise ValueError(f"Flow not found: {flow_id}")
        
        results = []
        
        # Simple sequential execution for demo
        if 'entry' in flow:
            entry_task = flow['entry']
            if entry_task.startswith('@'):
                task_id = entry_task[1:].split('.')[0]
                result = await self.execute_task(task_id)
                results.append(result)
        
        # Handle edges
        for edge in flow.get('edges', []):
            from_task = edge.get('from', '')
            to_task = edge.get('to', '')
            
            if to_task and to_task.startswith('@'):
                task_id = to_task[1:].split('.')[0]
                result = await self.execute_task(task_id)
                results.append(result)
        
        return {
            'flow_id': flow_id,
            'results': results
        }


async def execute_ir(ir: Dict[str, Any], signals: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute compiled CHORD IR"""
    runtime = Runtime(ir)
    
    if signals:
        runtime.set_signals(signals)
    
    # Default signals
    runtime.set_signal('date', datetime.now().strftime('%Y-%m-%d'))
    runtime.set_signal('timestamp', datetime.now().isoformat())
    
    # Find and execute default view or flow
    if runtime.views:
        # Execute first view
        return await runtime.execute_view(runtime.views[0]['id'])
    elif runtime.flows:
        # Execute first flow
        return await runtime.execute_flow(runtime.flows[0]['id'])
    else:
        return {'error': 'No executable views or flows found'}


def main():
    """CLI entry point for testing"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="CHORD Runtime")
    parser.add_argument("ir_file", help="Path to compiled .chordi file")
    parser.add_argument("--view", help="View ID to execute")
    parser.add_argument("--flow", help="Flow ID to execute")
    parser.add_argument("--task", help="Task ID to execute")
    parser.add_argument("--signal", action="append", help="Set signal (name=value)")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    try:
        # Load IR
        with open(args.ir_file, 'r', encoding='utf-8') as f:
            ir = json.load(f)
        
        # Parse signals
        signals = {}
        if args.signal:
            for sig in args.signal:
                if '=' in sig:
                    name, value = sig.split('=', 1)
                    signals[name] = value
        
        # Create runtime
        runtime = Runtime(ir)
        runtime.set_signals(signals)
        runtime.set_signal('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Execute
        async def run():
            if args.view:
                return await runtime.execute_view(args.view)
            elif args.flow:
                return await runtime.execute_flow(args.flow)
            elif args.task:
                return await runtime.execute_task(args.task)
            else:
                return await execute_ir(ir, signals)
        
        # Run async
        result = asyncio.run(run())
        
        # Output
        output_json = json.dumps(result, indent=2, default=str)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"✓ Output written to {args.output}")
        else:
            print(output_json)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()