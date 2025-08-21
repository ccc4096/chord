#!/usr/bin/env python3
"""
CHORD Compiler - Parses .chord files and generates IR (Intermediate Representation)
"""

import re
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum


class NodeType(Enum):
    CTX = "ctx"
    CAP = "cap"
    ROLE = "role"
    POLICY = "policy"
    MODEL = "model"
    TASK = "task"
    FLOW = "flow"
    VIEW = "view"
    SIGNAL = "signal"
    MEMORY = "memory"
    HOOK = "hook"
    TEST = "test"
    CACHE = "cache"


class TokenType(Enum):
    DEF = "def"
    IDENTIFIER = "identifier"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    COLON = ":"
    COMMA = ","
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"
    REFERENCE = "reference"
    COMMENT = "comment"
    PIPE = "|"
    NEWLINE = "newline"
    EOF = "eof"


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int


@dataclass
class Node:
    type: NodeType
    id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    line: int = 0


@dataclass
class Graph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)


class Lexer:
    """Tokenizes CHORD source code"""
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        pos = self.pos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self) -> str:
        char = self.current_char()
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char
    
    def skip_whitespace(self):
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        if self.current_char() == '#':
            # Check for multi-line comment
            if self.peek_char() == '[':
                self.advance()  # Skip #
                self.advance()  # Skip [
                while True:
                    if self.current_char() == ']' and self.peek_char() == '#':
                        self.advance()  # Skip ]
                        self.advance()  # Skip #
                        break
                    if not self.current_char():
                        break
                    self.advance()
            else:
                # Single line comment
                while self.current_char() and self.current_char() != '\n':
                    self.advance()
    
    def read_string(self) -> str:
        quote = self.advance()  # Skip opening quote
        value = ""
        while self.current_char() and self.current_char() != quote:
            if self.current_char() == '\\':
                self.advance()
                next_char = self.current_char()
                if next_char == 'n':
                    value += '\n'
                elif next_char == 't':
                    value += '\t'
                elif next_char == '\\':
                    value += '\\'
                elif next_char == quote:
                    value += quote
                else:
                    value += next_char
                self.advance()
            else:
                value += self.advance()
        self.advance()  # Skip closing quote
        return value
    
    def read_multiline_string(self) -> str:
        self.advance()  # Skip |
        # Skip to next line
        while self.current_char() and self.current_char() != '\n':
            self.advance()
        if self.current_char() == '\n':
            self.advance()
        
        # Determine base indentation
        base_indent = 0
        while self.current_char() and self.current_char() in ' \t':
            base_indent += 1
            self.advance()
        
        lines = []
        current_line = ""
        
        while self.current_char():
            # Check if we've reached the end (less indentation)
            if self.current_char() == '\n':
                lines.append(current_line)
                current_line = ""
                self.advance()
                
                # Count indentation of next line
                indent = 0
                start_pos = self.pos
                while self.current_char() and self.current_char() in ' \t':
                    indent += 1
                    self.advance()
                
                # If less indented or empty line followed by less indented, we're done
                if indent < base_indent and self.current_char() and self.current_char() not in '\n':
                    self.pos = start_pos  # Reset position
                    break
            else:
                current_line += self.advance()
        
        if current_line:
            lines.append(current_line)
        
        return '\n'.join(lines)
    
    def read_number(self) -> Union[int, float]:
        value = ""
        has_dot = False
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_dot:
                    break
                has_dot = True
            value += self.advance()
        
        return float(value) if has_dot else int(value)
    
    def read_identifier(self) -> str:
        value = ""
        while self.current_char() and (self.current_char().isalnum() or self.current_char() in '_-'):
            value += self.advance()
        return value
    
    def read_reference(self) -> str:
        self.advance()  # Skip @
        reference = ""
        
        # Handle dynamic references @{...}
        if self.current_char() == '{':
            self.advance()
            depth = 1
            while depth > 0 and self.current_char():
                if self.current_char() == '{':
                    depth += 1
                elif self.current_char() == '}':
                    depth -= 1
                    if depth == 0:
                        break
                reference += self.advance()
            self.advance()  # Skip closing }
            return f"{{{reference}}}"
        
        # Regular reference
        while self.current_char() and (self.current_char().isalnum() or self.current_char() in '_.[]'):
            reference += self.advance()
        
        return reference
    
    def tokenize(self) -> List[Token]:
        while self.current_char():
            self.skip_whitespace()
            
            if not self.current_char():
                break
            
            line = self.line
            column = self.column
            
            # Comments
            if self.current_char() == '#':
                self.skip_comment()
                continue
            
            # Newline
            if self.current_char() == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', line, column))
                self.advance()
                continue
            
            # Strings
            if self.current_char() in '"\'':
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, line, column))
                continue
            
            # Multi-line strings
            if self.current_char() == '|':
                value = self.read_multiline_string()
                self.tokens.append(Token(TokenType.STRING, value, line, column))
                continue
            
            # Numbers
            if self.current_char().isdigit():
                value = self.read_number()
                self.tokens.append(Token(TokenType.NUMBER, value, line, column))
                continue
            
            # References
            if self.current_char() == '@':
                value = self.read_reference()
                self.tokens.append(Token(TokenType.REFERENCE, value, line, column))
                continue
            
            # Single character tokens
            char = self.current_char()
            if char == '{':
                self.tokens.append(Token(TokenType.LBRACE, char, line, column))
                self.advance()
            elif char == '}':
                self.tokens.append(Token(TokenType.RBRACE, char, line, column))
                self.advance()
            elif char == '[':
                self.tokens.append(Token(TokenType.LBRACKET, char, line, column))
                self.advance()
            elif char == ']':
                self.tokens.append(Token(TokenType.RBRACKET, char, line, column))
                self.advance()
            elif char == ':':
                self.tokens.append(Token(TokenType.COLON, char, line, column))
                self.advance()
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, char, line, column))
                self.advance()
            else:
                # Keywords and identifiers
                value = self.read_identifier()
                if value == "def":
                    self.tokens.append(Token(TokenType.DEF, value, line, column))
                elif value in ["true", "false"]:
                    self.tokens.append(Token(TokenType.BOOLEAN, value == "true", line, column))
                elif value == "null":
                    self.tokens.append(Token(TokenType.NULL, None, line, column))
                else:
                    self.tokens.append(Token(TokenType.IDENTIFIER, value, line, column))
        
        self.tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return self.tokens


class Parser:
    """Parses tokens into an AST"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.graph = Graph()
    
    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # Return EOF
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Token:
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[pos]
    
    def advance(self) -> Token:
        token = self.current_token()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token
    
    def skip_newlines(self):
        while self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def expect(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type} at line {token.line}")
        return self.advance()
    
    def parse_value(self) -> Any:
        self.skip_newlines()
        token = self.current_token()
        
        if token.type == TokenType.STRING:
            return self.advance().value
        elif token.type == TokenType.NUMBER:
            return self.advance().value
        elif token.type == TokenType.BOOLEAN:
            return self.advance().value
        elif token.type == TokenType.NULL:
            self.advance()
            return None
        elif token.type == TokenType.REFERENCE:
            return f"@{self.advance().value}"
        elif token.type == TokenType.LBRACKET:
            return self.parse_array()
        elif token.type == TokenType.LBRACE:
            return self.parse_object()
        else:
            raise SyntaxError(f"Unexpected token {token.type} at line {token.line}")
    
    def parse_array(self) -> List[Any]:
        self.expect(TokenType.LBRACKET)
        self.skip_newlines()
        
        items = []
        while self.current_token().type != TokenType.RBRACKET:
            items.append(self.parse_value())
            self.skip_newlines()
            
            if self.current_token().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()
            elif self.current_token().type != TokenType.RBRACKET:
                break
        
        self.expect(TokenType.RBRACKET)
        return items
    
    def parse_object(self) -> Dict[str, Any]:
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        obj = {}
        while self.current_token().type != TokenType.RBRACE:
            # Parse key
            if self.current_token().type != TokenType.IDENTIFIER:
                break
            
            key = self.advance().value
            self.expect(TokenType.COLON)
            value = self.parse_value()
            obj[key] = value
            
            self.skip_newlines()
            if self.current_token().type == TokenType.COMMA:
                self.advance()
                self.skip_newlines()
        
        self.expect(TokenType.RBRACE)
        return obj
    
    def parse_properties(self) -> Dict[str, Any]:
        self.expect(TokenType.LBRACE)
        self.skip_newlines()
        
        properties = {}
        while self.current_token().type != TokenType.RBRACE:
            if self.current_token().type != TokenType.IDENTIFIER:
                break
            
            key = self.advance().value
            
            # Handle metadata
            if key == "@meta":
                self.expect(TokenType.COLON)
                metadata = self.parse_value()
                properties["@meta"] = metadata
            else:
                self.expect(TokenType.COLON)
                value = self.parse_value()
                properties[key] = value
            
            self.skip_newlines()
        
        self.expect(TokenType.RBRACE)
        return properties
    
    def parse_definition(self):
        self.expect(TokenType.DEF)
        
        # Parse node type
        type_token = self.expect(TokenType.IDENTIFIER)
        try:
            node_type = NodeType(type_token.value)
        except ValueError:
            raise SyntaxError(f"Unknown node type '{type_token.value}' at line {type_token.line}")
        
        # Parse node ID
        id_token = self.expect(TokenType.IDENTIFIER)
        node_id = id_token.value
        
        # Parse properties
        properties = self.parse_properties()
        
        # Extract metadata if present
        metadata = properties.pop("@meta", {})
        
        # Create node
        node = Node(
            type=node_type,
            id=node_id,
            properties=properties,
            metadata=metadata,
            line=type_token.line
        )
        
        # Add to graph
        self.graph.nodes[node_id] = node
    
    def parse(self) -> Graph:
        while self.current_token().type != TokenType.EOF:
            self.skip_newlines()
            
            if self.current_token().type == TokenType.DEF:
                self.parse_definition()
            elif self.current_token().type == TokenType.EOF:
                break
            else:
                # Skip unknown tokens
                self.advance()
        
        return self.graph


class Compiler:
    """Compiles a Graph into IR (Intermediate Representation)"""
    
    def __init__(self, graph: Graph):
        self.graph = graph
        self.ir = {
            "version": "1.0.0",
            "metadata": graph.metadata,
            "nodes": {},
            "views": [],
            "flows": [],
            "tests": []
        }
    
    def resolve_reference(self, ref: str, context: Dict[str, Any]) -> Any:
        """Resolve @ references"""
        if not ref.startswith("@"):
            return ref
        
        ref = ref[1:]  # Remove @
        
        # Handle dynamic references
        if ref.startswith("{") and ref.endswith("}"):
            # This would need template evaluation
            return f"@{{{ref[1:-1]}}}"
        
        # Split reference path
        parts = ref.split(".")
        node_id = parts[0]
        
        # Look up node
        if node_id not in self.graph.nodes:
            raise ValueError(f"Unknown reference: @{ref}")
        
        node = self.graph.nodes[node_id]
        
        # If just node reference, return node ID
        if len(parts) == 1:
            return f"@{node_id}"
        
        # Navigate properties
        value = node.properties
        for part in parts[1:]:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return f"@{ref}"  # Return unresolved
        
        return value
    
    def compile_node(self, node: Node) -> Dict[str, Any]:
        """Compile a single node"""
        compiled = {
            "type": node.type.value,
            "id": node.id,
            "properties": {}
        }
        
        # Process properties
        for key, value in node.properties.items():
            if isinstance(value, str) and value.startswith("@"):
                compiled["properties"][key] = self.resolve_reference(value, {})
            elif isinstance(value, list):
                compiled["properties"][key] = [
                    self.resolve_reference(v, {}) if isinstance(v, str) and v.startswith("@") else v
                    for v in value
                ]
            elif isinstance(value, dict):
                compiled["properties"][key] = self.compile_object(value)
            else:
                compiled["properties"][key] = value
        
        if node.metadata:
            compiled["metadata"] = node.metadata
        
        return compiled
    
    def compile_object(self, obj: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively compile an object"""
        compiled = {}
        for key, value in obj.items():
            if isinstance(value, str) and value.startswith("@"):
                compiled[key] = self.resolve_reference(value, {})
            elif isinstance(value, list):
                compiled[key] = [
                    self.resolve_reference(v, {}) if isinstance(v, str) and v.startswith("@") else v
                    for v in value
                ]
            elif isinstance(value, dict):
                compiled[key] = self.compile_object(value)
            else:
                compiled[key] = value
        return compiled
    
    def compile_view(self, node: Node) -> Dict[str, Any]:
        """Compile a view node into executable form"""
        view = {
            "id": node.id,
            "type": "view",
            "task": node.properties.get("task"),
            "role": node.properties.get("role"),
            "model": node.properties.get("model"),
            "policy": node.properties.get("policy"),
            "selectors": node.properties.get("selectors", []),
            "prompt": node.properties.get("prompt", {}),
            "response_format": node.properties.get("response_format"),
            "post_process": node.properties.get("post_process", []),
            "asserts": node.properties.get("asserts", [])
        }
        
        # Process selectors
        compiled_selectors = []
        for selector in view["selectors"]:
            compiled_selector = self.compile_object(selector) if isinstance(selector, dict) else selector
            compiled_selectors.append(compiled_selector)
        view["selectors"] = compiled_selectors
        
        return view
    
    def compile_flow(self, node: Node) -> Dict[str, Any]:
        """Compile a flow node"""
        flow = {
            "id": node.id,
            "type": "flow",
            "entry": node.properties.get("entry"),
            "edges": node.properties.get("edges", []),
            "parallel": node.properties.get("parallel"),
            "sequential": node.properties.get("sequential"),
            "conditional": node.properties.get("conditional"),
            "error_handling": node.properties.get("error_handling"),
            "schedule": node.properties.get("schedule")
        }
        
        # Remove None values
        flow = {k: v for k, v in flow.items() if v is not None}
        
        return flow
    
    def compile(self) -> Dict[str, Any]:
        """Compile the graph into IR"""
        
        # Compile all nodes
        for node_id, node in self.graph.nodes.items():
            self.ir["nodes"][node_id] = self.compile_node(node)
            
            # Special handling for views, flows, and tests
            if node.type == NodeType.VIEW:
                self.ir["views"].append(self.compile_view(node))
            elif node.type == NodeType.FLOW:
                self.ir["flows"].append(self.compile_flow(node))
            elif node.type == NodeType.TEST:
                self.ir["tests"].append(self.compile_node(node))
        
        return self.ir


def compile_chord(source: str) -> Dict[str, Any]:
    """Main compilation function"""
    
    # Tokenize
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Parse
    parser = Parser(tokens)
    graph = parser.parse()
    
    # Compile
    compiler = Compiler(graph)
    ir = compiler.compile()
    
    return ir


def compile_file(filepath: Path) -> Dict[str, Any]:
    """Compile a .chord file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    return compile_chord(source)


def main():
    """CLI entry point"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="CHORD Compiler")
    parser.add_argument("file", help="Path to .chord file")
    parser.add_argument("-o", "--output", help="Output file path (.chordi)")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    parser.add_argument("--validate", action="store_true", help="Validate only")
    
    args = parser.parse_args()
    
    try:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File '{filepath}' not found", file=sys.stderr)
            sys.exit(1)
        
        # Compile
        ir = compile_file(filepath)
        
        if args.validate:
            print(f"✓ {filepath} is valid CHORD")
            sys.exit(0)
        
        # Output
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w', encoding='utf-8') as f:
                if args.pretty:
                    json.dump(ir, f, indent=2)
                else:
                    json.dump(ir, f)
            print(f"✓ Compiled to {output_path}")
        else:
            # Print to stdout
            if args.pretty:
                print(json.dumps(ir, indent=2))
            else:
                print(json.dumps(ir))
    
    except SyntaxError as e:
        print(f"Syntax Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()