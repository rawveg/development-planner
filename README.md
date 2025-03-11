# Development Planner ✨

> Transform vague ideas into structured development plans with AI

A powerful tool that takes your high-level concepts and converts them into detailed, hierarchical project plans with AI-generated implementation guidance. Each task includes specific prompts designed for Agentic AI implementation, making it perfect for developers working with AI assistants, project managers, and anyone who needs to structure complex ideas for execution.

## ✅ Features

- **Comprehensive Plans**: Generate complete project structures from simple idea descriptions
- **Hierarchical Tasks**: Automatically create task trees with proper dependencies
- **AI Implementation Prompts**: Get detailed prompts for each task specifically designed for Agentic AI implementation
- **Markdown Export**: Convert plans to readable documentation for sharing

## 🚀 Getting Started

### Using Docker (Recommended)

Docker provides the easiest way to run the tool without worrying about dependencies.

1. Make sure you have [Docker](https://www.docker.com/get-started) and Docker Compose installed
2. Clone this repository
3. Set your OpenRouter API key as an environment variable:
   ```bash
   export OPENROUTER_API_KEY=your_api_key_here
   ```
   Alternatively, you can embed the API key and specify a custom model directly in your docker-compose.yml file:
   ```yaml
   services:
     development-planner:
       # ... other configuration ...
       environment:
         - OPENROUTER_API_KEY=your_api_key_here
         - OPENROUTER_MODEL=anthropic/claude-3-opus-20240229
   ```
4. Build the Docker image:
   ```bash
   docker-compose build
   ```
5. Generate a plan:
   ```bash
   docker-compose run development-planner plan "Your vague idea here"
   ```
6. Convert to Markdown for better readability:
   ```bash
   docker-compose run development-planner convert plans/development_plan.json
   ```

### Running Locally with Python

If you prefer to run directly with Python:

1. Ensure Python 3.6+ is installed
2. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API key:
   ```bash
   export OPENROUTER_API_KEY=your_api_key_here
   ```
4. Generate a plan:
   ```bash
   python development_plan.py "Your vague idea here"
   ```
5. Convert to Markdown:
   ```bash
   python convert_to_markdown.py plans/development_plan.json
   ```

## 📋 Command Options

### Development Plan Generator

```bash
python development_plan.py [--output OUTPUT_FILE] [--model MODEL_NAME] "Your idea"
```

| Option | Description |
|--------|-------------|
| `--output`, `-o` | Output JSON file path (default: `plans/development_plan.json`) |
| `--model`, `-m` | AI model to use (default: `google/gemini-2.0-pro-exp-02-05:free`) |

### Markdown Converter

```bash
python convert_to_markdown.py JSON_FILE [--output OUTPUT_FILE]
```

| Option | Description |
|--------|-------------|
| `JSON_FILE` | Path to the JSON file to convert |
| `--output`, `-o` | Output markdown file path (default: `docs/<json_filename>.md`) |

## 💡 Example Usage

**Generate a plan for a recipe recommendation system:**
```bash
python development_plan.py "Build a recipe recommendation system based on users' dietary preferences and ingredient availability"
```

**Convert the plan to Markdown:**
```bash
python convert_to_markdown.py plans/development_plan.json
```

## 📁 Output

- JSON plans are saved in the `plans/` directory
- Markdown documentation is generated in the `docs/` directory

## 📝 Notes

- The tool uses OpenRouter API to connect to various AI models
- Internet connection is required for plan generation
- The more detailed your initial idea, the better the generated plan will be
- Implementation prompts are specifically crafted for use with AI assistants like Claude, ChatGPT, or Gemini
- Pass the implementation prompts to your preferred AI assistant to rapidly implement each task
- For security best practices, consider using environment variables for your API key rather than embedding it in the docker-compose.yml file, especially in shared repositories
- The default model (google/gemini-2.0-pro-exp-02-05:free) is recommended for most users, but you can specify paid models like `anthropic/claude-3-opus-20240229` for potentially higher quality plans

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Happy planning! 🎯