# AST-Grep Structural Rules for Clean Code

This directory contains **ast-grep** structural search and rewrite rules for AST-aware, deterministic code quality checks and agentic refactoring.

Unlike regex grep, **ast-grep** operates on the syntax tree:
- **Zero false positives** from comments, string literals, or variable names.
- **Accurate token replacement** across TypeScript, JavaScript, Python, Go, and Rust.
- **Direct Agent MCP integration** via `ast-grep-mcp` or CLI (`ast-grep scan`).

## Quick Start

```bash
# Install ast-grep (if not already installed)
npm install -g @ast-grep/cli   # or: brew install ast-grep / cargo install ast-grep

# Scan current directory using this rule set
ast-grep scan -c tools/ast-grep/sgconfig.yml

# Interactive structural search across codebase
ast-grep --pattern 'catch ($ERR) { }' --lang ts
```

## Rules Included

1. **`nested-ternary`**: Detects deeply nested ternary operations (`a ? b : c ? d : e`) that induce high cognitive complexity.
2. **`swallowed-catch`**: Detects empty catch blocks that silently swallow exceptions.
3. **`boolean-flag-call`**: Detects boolean literals passed as positional function arguments (`render(doc, true)`).
