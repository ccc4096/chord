#!/usr/bin/env python3
"""
CHORD CLI - Command-line interface for CHORD orchestration language
"""

import os
import sys
import json
import asyncio
import argparse
import readline
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

# Import CHORD modules
try:
    from chord_compiler import compile_chord, compile_file
    from chord_runtime import Runtime, execute_ir
except ImportError:
    print("Error: chord_compiler.py and chord_runtime.py must be in the same directory or installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class CHORDRepl:
    """Interactive REPL for CHORD"""
    
    def __init__(self, initial_file: Optional[Path] = None):
        self.graph = {}
        self.ir = None
        self.runtime = None
        self.signals = {}
        self.history = []
        
        if initial_file:
            self.load_file(initial_file)
    
    def load_file(self, filepath: Path):
        """Load a CHORD file"""
        try:
            with open(filepath, 'r') as f:
                source = f.read()
            
            self.ir = compile_chord(source)
            self.runtime = Runtime(self.ir)
            print(f"{Colors.GREEN}✓ Loaded {filepath}{Colors.END}")
            print(f"  Nodes: {len(self.ir.get('nodes', {}))}")
            print(f"  Views: {len(self.ir.get('views', []))}")
            print(f"  Flows: {len(self.ir.get('flows', []))}")
        except Exception as e:
            print(f"{Colors.FAIL}Error loading file: {e}{Colors.END}")
    
    def set_signal(self, name: str, value: str):
        """Set a signal value"""
        self.signals[name] = value
        if self.runtime:
            self.runtime.set_signal(name, value)
        print(f"{Colors.GREEN}✓ Set signal {name} = {value}{Colors.END}")
    
    def list_nodes(self, node_type: Optional[str] = None):
        """List nodes in the graph"""
        if not self.ir:
            print(f"{Colors.WARNING}No CHORD file loaded{Colors.END}")
            return
        
        nodes = self.ir.get('nodes', {})
        
        if node_type:
            filtered = {k: v for k, v in nodes.items() if v['type'] == node_type}
            nodes = filtered
        
        if not nodes:
            print(f"{Colors.WARNING}No nodes found{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}Nodes:{Colors.END}")
        for node_id, node in nodes.items():
            print(f"  {Colors.CYAN}{node['type']}{Colors.END} {node_id}")
    
    def show_node(self, node_id: str):
        """Show details of a specific node"""
        if not self.ir:
            print(f"{Colors.WARNING}No CHORD file loaded{Colors.END}")
            return
        
        nodes = self.ir.get('nodes', {})
        if node_id not in nodes:
            print(f"{Colors.FAIL}Node not found: {node_id}{Colors.END}")
            return
        
        node = nodes[node_id]
        print(f"\n{Colors.BOLD}Node: {node_id}{Colors.END}")
        print(f"Type: {node['type']}")
        print(f"Properties:")
        print(json.dumps(node.get('properties', {}), indent=2))
    
    async def execute_view(self, view_id: str):
        """Execute a view"""
        if not self.runtime:
            print(f"{Colors.WARNING}No CHORD file loaded{Colors.END}")
            return
        
        try:
            result = await self.runtime.execute_view(view_id)
            
            print(f"\n{Colors.BOLD}View: {view_id}{Colors.END}")
            print(f"\n{Colors.CYAN}Resolved Context:{Colors.END}")
            for key, value in result.get('resolved_context', {}).items():
                print(f"  {key}: {str(value)[:100]}...")
            
            print(f"\n{Colors.CYAN}Prompt:{Colors.END}")
            for section, content in result.get('prompt', {}).items():
                print(f"\n  {Colors.BOLD}{section}:{Colors.END}")
                print(f"  {content[:500]}...")
            
        except Exception as e:
            print(f"{Colors.FAIL}Error executing view: {e}{Colors.END}")
    
    async def execute_task(self, task_id: str):
        """Execute a task"""
        if not self.runtime:
            print(f"{Colors.WARNING}No CHORD file loaded{Colors.END}")
            return
        
        try:
            result = await self.runtime.execute_task(task_id)
            print(f"\n{Colors.BOLD}Task: {task_id}{Colors.END}")
            print(json.dumps(result, indent=2, default=str))
        except Exception as e:
            print(f"{Colors.FAIL}Error executing task: {e}{Colors.END}")
    
    def run(self):
        """Run the REPL"""
        print(f"\n{Colors.BOLD}CHORD Interactive Shell{Colors.END}")
        print("Type 'help' for commands or 'quit' to exit\n")
        
        while True:
            try:
                command = input(f"{Colors.CYAN}chord>{Colors.END} ").strip()
                
                if not command:
                    continue
                
                self.history.append(command)
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                
                elif cmd == 'help':
                    self.show_help()
                
                elif cmd == 'load':
                    if len(parts) < 2:
                        print(f"{Colors.WARNING}Usage: load <file.chord>{Colors.END}")
                    else:
                        self.load_file(Path(parts[1]))
                
                elif cmd == 'signal':
                    if len(parts) < 3:
                        print(f"{Colors.WARNING}Usage: signal <name> <value>{Colors.END}")
                    else:
                        self.set_signal(parts[1], ' '.join(parts[2:]))
                
                elif cmd == 'signals':
                    print(f"\n{Colors.BOLD}Signals:{Colors.END}")
                    for name, value in self.signals.items():
                        print(f"  {name} = {value}")
                
                elif cmd == 'nodes':
                    node_type = parts[1] if len(parts) > 1 else None
                    self.list_nodes(node_type)
                
                elif cmd == 'show':
                    if len(parts) < 2:
                        print(f"{Colors.WARNING}Usage: show <node_id>{Colors.END}")
                    else:
                        self.show_node(parts[1])
                
                elif cmd == 'view':
                    if len(parts) < 2:
                        print(f"{Colors.WARNING}Usage: view <view_id>{Colors.END}")
                    else:
                        asyncio.run(self.execute_view(parts[1]))
                
                elif cmd == 'task':
                    if len(parts) < 2:
                        print(f"{Colors.WARNING}Usage: task <task_id>{Colors.END}")
                    else:
                        asyncio.run(self.execute_task(parts[1]))
                
                elif cmd == 'ir':
                    if self.ir:
                        print(json.dumps(self.ir, indent=2))
                    else:
                        print(f"{Colors.WARNING}No CHORD file loaded{Colors.END}")
                
                elif cmd == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                
                else:
                    print(f"{Colors.WARNING}Unknown command: {cmd}{Colors.END}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"{Colors.FAIL}Error: {e}{Colors.END}")
    
    def show_help(self):
        """Show help message"""
        help_text = f"""
{Colors.BOLD}Available Commands:{Colors.END}

  {Colors.CYAN}load <file>{Colors.END}       Load a CHORD file
  {Colors.CYAN}nodes [type]{Colors.END}      List nodes (optionally filtered by type)
  {Colors.CYAN}show <node_id>{Colors.END}    Show node details
  {Colors.CYAN}view <view_id>{Colors.END}    Execute a view
  {Colors.CYAN}task <task_id>{Colors.END}    Execute a task
  {Colors.CYAN}signal <n> <v>{Colors.END}    Set signal value
  {Colors.CYAN}signals{Colors.END}           List all signals
  {Colors.CYAN}ir{Colors.END}                Show compiled IR
  {Colors.CYAN}clear{Colors.END}             Clear screen
  {Colors.CYAN}help{Colors.END}              Show this help
  {Colors.CYAN}quit{Colors.END}              Exit REPL
"""
        print(help_text)


def cmd_run(args):
    """Run a CHORD file"""
    try:
        # Compile
        ir = compile_file(Path(args.file))
        
        # Parse signals
        signals = {}
        if args.signal:
            for sig in args.signal:
                if '=' in sig:
                    name, value = sig.split('=', 1)
                    signals[name] = value
        
        # Execute
        result = asyncio.run(execute_ir(ir, signals))
        
        # Output
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"{Colors.GREEN}✓ Output written to {args.output}{Colors.END}")
        else:
            # Pretty print prompt if it's a view result
            if 'prompt' in result:
                print(f"\n{Colors.BOLD}Generated Prompt:{Colors.END}")
                for section, content in result['prompt'].items():
                    print(f"\n{Colors.CYAN}{section.upper()}:{Colors.END}")
                    print(content)
            else:
                print(json.dumps(result, indent=2, default=str))
    
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.END}")
        sys.exit(1)


def cmd_compile(args):
    """Compile a CHORD file to IR"""
    try:
        ir = compile_file(Path(args.file))
        
        output_path = args.output or args.file.replace('.chord', '.chordi')
        
        with open(output_path, 'w') as f:
            if args.pretty:
                json.dump(ir, f, indent=2)
            else:
                json.dump(ir, f)
        
        print(f"{Colors.GREEN}✓ Compiled to {output_path}{Colors.END}")
        
        # Show stats
        print(f"  Nodes: {len(ir.get('nodes', {}))}")
        print(f"  Views: {len(ir.get('views', []))}")
        print(f"  Flows: {len(ir.get('flows', []))}")
    
    except Exception as e:
        print(f"{Colors.FAIL}Compilation Error: {e}{Colors.END}")
        sys.exit(1)


def cmd_validate(args):
    """Validate a CHORD file"""
    try:
        ir = compile_file(Path(args.file))
        print(f"{Colors.GREEN}✓ {args.file} is valid CHORD{Colors.END}")
        
        # Show warnings if any
        warnings = []
        
        # Check for unreferenced nodes
        referenced = set()
        for view in ir.get('views', []):
            for key in ['task', 'role', 'model', 'policy']:
                ref = view.get(key, '')
                if ref.startswith('@'):
                    referenced.add(ref[1:])
        
        unreferenced = set(ir.get('nodes', {}).keys()) - referenced
        if unreferenced:
            warnings.append(f"Unreferenced nodes: {', '.join(unreferenced)}")
        
        # Check for missing required fields
        for node_id, node in ir.get('nodes', {}).items():
            if node['type'] == 'ctx' and 'uri' not in node.get('properties', {}):
                warnings.append(f"Context {node_id} missing 'uri' property")
        
        if warnings:
            print(f"\n{Colors.WARNING}Warnings:{Colors.END}")
            for warning in warnings:
                print(f"  • {warning}")
    
    except Exception as e:
        print(f"{Colors.FAIL}Validation Error: {e}{Colors.END}")
        sys.exit(1)


def cmd_repl(args):
    """Start interactive REPL"""
    initial_file = Path(args.file) if args.file else None
    repl = CHORDRepl(initial_file)
    repl.run()


def cmd_init(args):
    """Initialize a new CHORD project"""
    project_name = args.project
    project_path = Path(project_name)
    
    if project_path.exists():
        print(f"{Colors.WARNING}Directory {project_name} already exists{Colors.END}")
        sys.exit(1)
    
    try:
        # Create project structure
        project_path.mkdir()
        (project_path / "contexts").mkdir()
        (project_path / "capabilities").mkdir()
        (project_path / "orchestration").mkdir()
        (project_path / "orchestration" / "flows").mkdir()
        (project_path / "orchestration" / "views").mkdir()
        (project_path / "policies").mkdir()
        (project_path / "models").mkdir()
        (project_path / "tests").mkdir()
        
        # Create main.chord
        main_content = """# Main CHORD file for {project}

# Import common definitions
# import "contexts/main.chord"
# import "policies/default.chord"
# import "models/models.chord"

# Define a simple example
def ctx readme {{
  type: file
  uri: "fs://README.md"
}}

def role assistant {{
  persona: "helpful AI assistant"
  principles: ["be clear", "be concise"]
}}

def task summarize {{
  objective: "Summarize the README"
}}

def view main {{
  task: @task.summarize
  role: @role.assistant
  
  selectors: [
    {{ from: @ctx.readme, op: "head", lines: 50 }}
  ]
  
  prompt: {{
    system: "You are {{{{role.persona}}}}."
    user: "Please summarize this README."
  }}
}}
""".format(project=project_name)
        
        with open(project_path / "main.chord", 'w') as f:
            f.write(main_content)
        
        # Create README
        readme_content = f"""# {project_name}

A CHORD orchestration project.

## Structure

- `main.chord` - Main orchestration file
- `contexts/` - Context definitions
- `capabilities/` - Capability definitions
- `orchestration/` - Flows and views
- `policies/` - Policy definitions
- `models/` - Model configurations
- `tests/` - Test definitions

## Usage

```bash
# Run the main view
chord run main.chord

# Start interactive REPL
chord repl main.chord

# Compile to IR
chord compile main.chord
```
"""
        
        with open(project_path / "README.md", 'w') as f:
            f.write(readme_content)
        
        # Create .gitignore
        gitignore_content = """*.chordi
*.cache
__pycache__/
.env
"""
        
        with open(project_path / ".gitignore", 'w') as f:
            f.write(gitignore_content)
        
        print(f"{Colors.GREEN}✓ Created CHORD project: {project_name}{Colors.END}")
        print(f"\nNext steps:")
        print(f"  cd {project_name}")
        print(f"  chord run main.chord")
    
    except Exception as e:
        print(f"{Colors.FAIL}Error creating project: {e}{Colors.END}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CHORD - Contextual Hierarchy & Orchestration for Requests & Directives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chord run example.chord                     # Run a CHORD file
  chord compile example.chord -o example.ir   # Compile to IR
  chord validate example.chord                # Validate syntax
  chord repl                                   # Start interactive REPL
  chord init my-project                       # Create new project
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Execute a CHORD file')
    run_parser.add_argument('file', help='CHORD file to run')
    run_parser.add_argument('--signal', '-s', action='append', help='Set signal (name=value)')
    run_parser.add_argument('--output', '-o', help='Output file path')
    run_parser.set_defaults(func=cmd_run)
    
    # Compile command
    compile_parser = subparsers.add_parser('compile', help='Compile to IR')
    compile_parser.add_argument('file', help='CHORD file to compile')
    compile_parser.add_argument('--output', '-o', help='Output file path')
    compile_parser.add_argument('--pretty', action='store_true', help='Pretty print JSON')
    compile_parser.set_defaults(func=cmd_compile)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate CHORD file')
    validate_parser.add_argument('file', help='CHORD file to validate')
    validate_parser.set_defaults(func=cmd_validate)
    
    # REPL command
    repl_parser = subparsers.add_parser('repl', help='Start interactive REPL')
    repl_parser.add_argument('file', nargs='?', help='Initial CHORD file to load')
    repl_parser.set_defaults(func=cmd_repl)
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize new project')
    init_parser.add_argument('project', help='Project name')
    init_parser.set_defaults(func=cmd_init)
    
    # Version command
    version_parser = subparsers.add_parser('version', help='Show version')
    version_parser.set_defaults(func=lambda args: print("CHORD v1.0.0"))
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(0)
    
    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()