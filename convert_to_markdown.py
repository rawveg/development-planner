#!/usr/bin/env python3
import json
import os
import sys
import argparse
import re
from typing import Dict, List, Any
import html

def format_task_for_html(task: Dict[str, Any], depth: int = 0) -> str:
    """
    Format a task and its subtasks as HTML with proper formatting.
    
    Args:
        task: The task to format
        depth: The current depth level (0 for top-level tasks)
        
    Returns:
        A string containing the formatted task in HTML
    """
    # Calculate the heading level
    heading_level = min(depth + 3, 6)  # HTML only supports h1-h6
    indent = '  ' * depth
    
    # Start with the task heading
    html_content = f"<h{heading_level} class='task-heading'>Task {task['task_id']}: {task['name']}</h{heading_level}>\n\n"
    
    # Add the task description
    html_content += f"<p class='task-description'><strong>Description:</strong> {task['description']}</p>\n\n"
    
    # Add dependencies if they exist
    if task.get('dependencies') and len(task['dependencies']) > 0:
        html_content += f"<p class='task-dependencies'><strong>Dependencies:</strong> {', '.join(task['dependencies'])}</p>\n\n"
    
    # Add implementation prompt if it exists - handle this specially
    if task.get('prompt'):
        html_content += "<div class='implementation-prompt'>\n"
        html_content += "<h4 class='prompt-heading'>Implementation Prompt</h4>\n"
        
        # Process the prompt to format code blocks, lists, etc.
        processed_prompt = process_prompt_content(task['prompt'])
        html_content += processed_prompt
        
        html_content += "</div>\n\n"
    
    # Recursively add subtasks if they exist
    if task.get('tasks') and len(task['tasks']) > 0:
        html_content += "<div class='subtasks'>\n"
        for subtask in task['tasks']:
            html_content += format_task_for_html(subtask, depth + 1)
        html_content += "</div>\n\n"
    
    return html_content

def process_prompt_content(prompt_text: str) -> str:
    """
    Process the prompt text to convert code blocks, lists, and other markdown elements to HTML.
    
    Args:
        prompt_text: The raw prompt text
        
    Returns:
        Formatted HTML content
    """
    # Replace code blocks
    def replace_code_block(match):
        code = match.group(2)
        language = match.group(1) or ""
        escaped_code = html.escape(code)
        return f'<div class="code-block"><pre><code class="language-{language}">{escaped_code}</code></pre></div>'
    
    # Process fenced code blocks
    prompt_html = re.sub(r'```(\w*)\n([\s\S]*?)```', replace_code_block, prompt_text)
    
    # Process numbered lists (1., 2., etc.)
    lines = prompt_html.split('\n')
    in_list = False
    list_type = None
    result_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for numbered list items (1. Item)
        numbered_match = re.match(r'^(\s*)(\d+)\.(\s+)(.+)$', line)
        # Check for alphabetic list items (a. Item or A. Item)
        alpha_match = re.match(r'^(\s*)([a-zA-Z])\.(\s+)(.+)$', line)
        
        if numbered_match or alpha_match:
            match = numbered_match or alpha_match
            spaces, number, mid_spaces, content = match.groups()
            
            if not in_list:
                # Start a new list
                in_list = True
                list_type = 'ol' if numbered_match else 'ul'
                result_lines.append(f'<{list_type}>')
            
            # Add the list item
            result_lines.append(f'<li><strong>{number}.</strong> {content}')
            
            # Look ahead for continuation lines
            j = i + 1
            continuation = []
            while j < len(lines) and (not lines[j].strip() or 
                                      (lines[j].startswith(' ' * (len(spaces) + 2)) and 
                                       not re.match(r'^\s*(\d+|[a-zA-Z])\.', lines[j]))):
                if lines[j].strip():
                    continuation.append(lines[j].strip())
                j += 1
            
            if continuation:
                result_lines[-1] += ' ' + ' '.join(continuation)
                i = j - 1
            
            result_lines[-1] += '</li>'
        else:
            if in_list and (not line.strip() or not line.startswith(' ')):
                # End the list
                result_lines.append(f'</{list_type}>')
                in_list = False
            
            if line.strip():
                # Regular paragraph
                if not in_list:
                    result_lines.append(f'<p>{line}</p>')
                else:
                    # This is content inside a list but not a new item
                    result_lines.append(line)
            else:
                # Empty line
                result_lines.append('')
        
        i += 1
    
    # Close any open list
    if in_list:
        result_lines.append(f'</{list_type}>')
    
    # Join the processed lines
    return '\n'.join(result_lines)

def json_to_html(plan: Dict[str, Any]) -> str:
    """
    Convert a development plan JSON to an HTML document.
    
    Args:
        plan: The parsed JSON development plan
        
    Returns:
        A string containing the formatted HTML
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{plan['title']} | Development Plan</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, 
                    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                font-size: 2.5rem;
                margin-bottom: 1.5rem;
                color: #2563eb;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid #e5e7eb;
            }}
            h2 {{
                font-size: 2rem;
                margin: 2rem 0 1rem;
                color: #2563eb;
                padding-bottom: 0.3rem;
                border-bottom: 1px solid #e5e7eb;
            }}
            .task-heading {{
                font-size: 1.75rem;
                margin: 2rem 0 1rem;
                color: #1e40af;
            }}
            .task-description {{
                margin-bottom: 1rem;
            }}
            .task-dependencies {{
                margin-bottom: 1.5rem;
                color: #4b5563;
            }}
            .implementation-prompt {{
                background-color: #f3f4f6;
                border-radius: 8px;
                padding: 1.5rem;
                margin: 1.5rem 0;
                border-left: 4px solid #2563eb;
            }}
            .prompt-heading {{
                margin-top: 0;
                margin-bottom: 1rem;
                color: #1e40af;
                font-size: 1.25rem;
            }}
            .code-block {{
                background-color: #1e293b;
                color: #e2e8f0;
                border-radius: 6px;
                padding: 1rem;
                margin: 1rem 0;
                overflow-x: auto;
            }}
            .code-block pre {{
                margin: 0;
                font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
                font-size: 0.9rem;
                line-height: 1.5;
            }}
            .subtasks {{
                margin-left: 2rem;
                border-left: 2px solid #e5e7eb;
                padding-left: 1.5rem;
            }}
            ul, ol {{
                margin: 1rem 0 1.5rem 2rem;
            }}
            li {{
                margin-bottom: 0.5rem;
            }}
            p {{
                margin-bottom: 1rem;
            }}
        </style>
    </head>
    <body>
        <h1>{plan['title']}</h1>
        
        <h2>Project Description</h2>
        <p>{plan['description']}</p>
        
        <h2>Tasks</h2>
    """
    
    # Add all tasks recursively
    for task in plan['tasks']:
        html_content += format_task_for_html(task, 0)
    
    html_content += """
    </body>
    </html>
    """
    
    return html_content

def convert_plan_to_html(json_file_path: str, output_file: str = None) -> None:
    """
    Convert a development plan JSON file to an HTML file.
    
    Args:
        json_file_path: Path to the JSON file
        output_file: Path for the output HTML file (optional)
    """
    # Default output file if not specified
    if output_file is None:
        # Get the base name without extension
        base_name = os.path.splitext(os.path.basename(json_file_path))[0]
        output_file = f"docs/{base_name}.html"
    
    # Read the JSON file
    try:
        with open(json_file_path, "r") as f:
            plan = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {json_file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file: {json_file_path}")
        sys.exit(1)
    
    # Convert to HTML
    html_content = json_to_html(plan)
    
    # Make sure the docs directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write the HTML file
    with open(output_file, "w") as f:
        f.write(html_content)
    
    print(f"HTML file successfully created at {output_file}")

    # Generate markdown file 
    md_output_file = os.path.splitext(output_file)[0] + ".md"
    with open(md_output_file, "w") as f:
        f.write(f"# {plan['title']}\n\n")
        f.write(f"## Project Description\n\n{plan['description']}\n\n")
        f.write(f"## Tasks\n\n")
        
        # Write task descriptions in markdown format
        def write_task_markdown(task, depth=0):
            indent = "  " * depth
            f.write(f"{indent}### Task {task['task_id']}: {task['name']}\n\n")
            f.write(f"{indent}**Description:** {task['description']}\n\n")
            
            if task.get('dependencies') and len(task['dependencies']) > 0:
                f.write(f"{indent}**Dependencies:** {', '.join(task['dependencies'])}\n\n")
            
            if task.get('prompt'):
                f.write(f"{indent}**Implementation Prompt:**\n\n{indent}```\n{task['prompt']}\n{indent}```\n\n")
            
            if task.get('tasks') and len(task['tasks']) > 0:
                for subtask in task['tasks']:
                    write_task_markdown(subtask, depth + 1)
        
        for task in plan['tasks']:
            write_task_markdown(task)
    
    print(f"Markdown file created at {md_output_file}")

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Convert a development plan JSON file to an HTML file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "json_file", 
        help="Path to the JSON file to convert"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output HTML file path (default: docs/<json_filename>.html)"
    )
    
    return parser.parse_args()

def main():
    """
    Main function to run the script.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Convert the plan to HTML
    convert_plan_to_html(args.json_file, args.output)

if __name__ == "__main__":
    main()