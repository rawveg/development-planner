FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p plans docs

# Copy application files
COPY development_plan.py convert_to_markdown.py ./

# Make scripts executable
RUN chmod +x /app/development_plan.py /app/convert_to_markdown.py

# Create entrypoint script
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'if [ "$1" = "plan" ]; then' >> /app/entrypoint.sh && \
    echo '    shift' >> /app/entrypoint.sh && \
    echo '    # Check if model is explicitly set or use environment variable' >> /app/entrypoint.sh && \
    echo '    if [[ "$*" != *"--model"* ]] && [[ "$*" != *"-m"* ]]; then' >> /app/entrypoint.sh && \
    echo '        if [ ! -z "$OPENROUTER_MODEL" ]; then' >> /app/entrypoint.sh && \
    echo '            echo "Using model: $OPENROUTER_MODEL"' >> /app/entrypoint.sh && \
    echo '        else' >> /app/entrypoint.sh && \
    echo '            echo "Using default model: google/gemini-2.0-pro-exp-02-05:free"' >> /app/entrypoint.sh && \
    echo '        fi' >> /app/entrypoint.sh && \
    echo '    fi' >> /app/entrypoint.sh && \
    echo '    python development_plan.py "$@"' >> /app/entrypoint.sh && \
    echo 'elif [ "$1" = "convert" ]; then' >> /app/entrypoint.sh && \
    echo '    shift' >> /app/entrypoint.sh && \
    echo '    python convert_to_markdown.py "$@"' >> /app/entrypoint.sh && \
    echo 'else' >> /app/entrypoint.sh && \
    echo '    echo "Usage:"' >> /app/entrypoint.sh && \
    echo '    echo "  docker-compose run development-planner plan [options] \"Your idea here\""' >> /app/entrypoint.sh && \
    echo '    echo "  docker-compose run development-planner convert plans/your_plan.json [--output docs/custom.md]"' >> /app/entrypoint.sh && \
    echo '    echo ""' >> /app/entrypoint.sh && \
    echo '    echo "Environment variables:"' >> /app/entrypoint.sh && \
    echo '    echo "  OPENROUTER_API_KEY: Your OpenRouter API key (required)"' >> /app/entrypoint.sh && \
    echo '    echo "  OPENROUTER_MODEL: Model to use (default: google/gemini-2.0-pro-exp-02-05:free)"' >> /app/entrypoint.sh && \
    echo '    echo ""' >> /app/entrypoint.sh && \
    echo '    echo "For more information, run:"' >> /app/entrypoint.sh && \
    echo '    echo "  docker-compose run development-planner plan --help"' >> /app/entrypoint.sh && \
    echo '    echo "  docker-compose run development-planner convert --help"' >> /app/entrypoint.sh && \
    echo 'fi' >> /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]