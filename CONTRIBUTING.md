# Contributing to CHORD

Thank you for your interest in contributing to CHORD! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with:
- A clear title and description
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment details (OS, Python version, etc.)

### Submitting Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Install development dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Make your changes** following our coding standards
4. **Write tests** for new functionality
5. **Run tests** to ensure nothing is broken:
   ```bash
   pytest
   ```
6. **Format your code**:
   ```bash
   black .
   ruff check .
   ```
7. **Update documentation** if needed
8. **Submit a pull request** with a clear description of changes

## Coding Standards

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep functions focused and under 50 lines when possible
- Add comments for complex logic

## Areas for Contribution

- **Selector Operations**: Add new context transformation operations
- **Model Adapters**: Support for additional LLM providers
- **Test Coverage**: Improve test coverage and add edge cases
- **Documentation**: Improve docs, add tutorials, fix typos
- **Examples**: Create new example CHORD files for different use cases
- **Performance**: Optimization and caching improvements

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/chord.git
   cd chord
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install in development mode:
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```

## Testing

Run the test suite:
```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_compiler.py  # Run specific test file
```

## Documentation

Build documentation locally:
```bash
cd docs
make html
open _build/html/index.html
```

## Code of Conduct

Please be respectful and constructive in all interactions. We aim to maintain a welcoming environment for all contributors.

## Questions?

Feel free to open an issue for any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.