# Development Planner - Commands & Style Guide

## Commands
- Run the tool: `python development_plan.py 'Your vague idea here'`
- Custom output: `python development_plan.py --output custom_plan.json 'Your idea'`
- Select model: `python development_plan.py --model 'model-name' 'Your idea'`
- Set API key: `export OPENROUTER_API_KEY=your_api_key_here`
- Convert to Markdown: `python convert_to_markdown.py plans/development_plan.json`
- Custom Markdown output: `python convert_to_markdown.py plans/development_plan.json --output docs/custom.md`

## Code Style
- **Typing**: Use Python type hints (`from typing import Dict, List, Any, Optional`)
- **Docstrings**: All functions need descriptive docstrings
- **Naming**: snake_case for functions and variables
- **Comments**: Add for complex operations
- **Formatting**: 4-space indentation
- **Error handling**: Use try/except with specific error messages and fallbacks
- **Imports**: Standard library first, then third-party packages

## Project Structure
- Main execution in `development_plan.py`
- Output plans stored as JSON files in `plans/` directory
- Markdown documentation in `docs/` directory
- Converter script in `convert_to_markdown.py`

## Docker Usage
- Build: `docker-compose build`
- Generate plan: `docker-compose run development-planner plan "Your idea here"`
- Convert to markdown: `docker-compose run development-planner convert plans/your_plan.json`