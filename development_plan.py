#!/usr/bin/env python3
import requests
import json
import re
import os
import sys
import argparse
import time
from typing import Dict, List, Any, Optional

def extract_json_from_response(raw_content: str) -> str:
    """
    Extract valid JSON from the response, handling various formats:
    - Markdown code blocks
    - Schema objects
    - Extra text before or after JSON
    """
    # Remove markdown code blocks if present
    json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
    matches = re.findall(json_pattern, raw_content)
    if matches:
        raw_content = matches[0].strip()
    
    # Check if the content contains multiple JSON objects (schema + actual data)
    if raw_content.count('{') > 1 and raw_content.count('}') > 1:
        try:
            # Try to parse as is first
            json.loads(raw_content)
            return raw_content
        except json.JSONDecodeError:
            # If that fails, try to extract just the development plan JSON
            # Look for the schema object and remove it
            schema_pattern = r'(\{\s*"\$schema".*?"definitions"\s*:\s*\{.*?"task"\s*:\s*\{.*?\}\s*\}\s*\})'
            schema_matches = re.search(schema_pattern, raw_content, re.DOTALL)
            
            if schema_matches:
                # Remove the schema object and any trailing comma
                cleaned_content = raw_content.replace(schema_matches.group(1), '', 1).lstrip()
                if cleaned_content.startswith(','):
                    cleaned_content = cleaned_content[1:].lstrip()
                
                # If we don't have a valid JSON object after removal, wrap it
                if not cleaned_content.startswith('{'):
                    cleaned_content = '{' + cleaned_content
                
                # Ensure it ends with a closing brace
                if not cleaned_content.rstrip().endswith('}'):
                    cleaned_content = cleaned_content.rstrip() + '}'
                
                return cleaned_content
    
    # If no special handling needed, just return the content
    return raw_content

def get_schema() -> Dict[str, Any]:
    """
    Return the JSON schema for the development plan.
    """
    return {
        "$schema": "http://json-schema.org/draft/2020-12/schema",
        "title": "Project Schema",
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "tasks": {
                "type": "array",
                "items": {"$ref": "#/definitions/task"}
            }
        },
        "required": ["title", "description", "tasks"],
        "definitions": {
            "task": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "prompt": {"type": "string"},
                    "tasks": {
                        "type": "array",
                        "items": {"$ref": "#/definitions/task"}
                    },
                    "dependencies": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["task_id", "name", "description"]
            }
        }
    }

def apply_hierarchical_numbering(tasks: List[Dict[str, Any]], prefix: str) -> None:
    """
    Recursively applies hierarchical numbering to tasks and their dependencies.
    """
    for index, task in enumerate(tasks, start=1):
        task_id = f"{prefix}{index}" if prefix else str(index)
        task["task_id"] = task_id
        
        # Ensure tasks and dependencies exist to avoid KeyErrors
        if "dependencies" not in task:
            task["dependencies"] = []
        elif task["dependencies"]:
            # Format dependencies with proper prefix
            task["dependencies"] = [f"{prefix}{dep}" if not dep.startswith(prefix) else dep 
                                   for dep in task["dependencies"]]
        
        if "tasks" not in task:
            task["tasks"] = []
        elif task["tasks"]:
            apply_hierarchical_numbering(task["tasks"], f"{task_id}.")

def create_prompt(vague_idea: str) -> str:
    """
    Create the prompt for the AI model.
    """
    return f"""
    You are an advanced AI assistant tasked with expanding a vague idea into a comprehensive development plan.
    
    Given the following high-level idea:
    "{vague_idea}"
    
    Please generate a fully fleshed-out structured development plan in JSON format, following this schema:
    {json.dumps(get_schema(), indent=2)}
    
    Ensure the plan includes:
    - A clear project title and detailed description.
    - A list of well-defined tasks with names and detailed descriptions.
    - A hierarchical structure where each task may contain subtasks, with numbering as follows:
      - Main tasks: 1, 2, 3, etc.
      - Subtasks: 1.1, 1.2, 1.3, etc.
      - Sub-subtasks: 1.1.1, 1.1.2, 1.1.3, etc.
    - Dependencies must also follow this numbering format to clearly reference tasks.
    - Comprehensive breakdowns to facilitate structured development.
    
    IMPORTANT: Return ONLY the development plan JSON without including the schema in your response.
    Do NOT include a "prompt" field for tasks - this will be added separately.
    """

def create_task_prompt(project_title: str, project_description: str, task: Dict[str, Any], all_tasks: Dict[str, Dict[str, Any]]) -> str:
    """
    Create a prompt for generating a detailed implementation prompt for a specific task.
    """
    # Get dependency information
    dependencies = []
    for dep_id in task.get("dependencies", []):
        if dep_id in all_tasks:
            dependencies.append(f"{dep_id}: {all_tasks[dep_id]['name']} - {all_tasks[dep_id]['description']}")
    
    dependencies_text = "\n".join(dependencies) if dependencies else "None"
    
    return f"""
    You are an expert developer creating detailed implementation instructions for an AI agent.
    
    Project: {project_title}
    Project Description: {project_description}
    
    Task ID: {task['task_id']}
    Task Name: {task['name']}
    Task Description: {task['description']}
    
    Dependencies:
    {dependencies_text}
    
    Please write a detailed, prescriptive prompt that an AI agent could follow to implement this specific task.
    The prompt should:
    1. Provide clear, step-by-step instructions
    2. Include technical details and best practices
    3. Mention specific technologies, libraries, or frameworks that would be appropriate
    4. Consider the context of the overall project and any dependencies
    5. Be actionable and specific enough that an AI could use it to generate code
    
    Return ONLY the implementation prompt text, without any additional explanations or meta-commentary.
    """

def call_api(api_key: str, prompt: str, model: str = "google/gemini-2.0-pro-exp-02-05:free") -> Dict[str, Any]:
    """
    Call the OpenRouter API to generate the development plan.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an expert project planner."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        error_msg = f"API request failed with status code: {response.status_code}"
        try:
            error_details = response.json()
            error_msg += f"\nDetails: {json.dumps(error_details, indent=2)}"
        except:
            error_msg += f"\nResponse: {response.text}"
        raise Exception(error_msg)
    
    return response.json()

def parse_and_validate_json(raw_content: str) -> Dict[str, Any]:
    """
    Parse and validate the JSON response.
    """
    # Clean up the response to extract valid JSON
    cleaned_content = extract_json_from_response(raw_content)
    
    try:
        # Try to parse the JSON
        parsed_json = json.loads(cleaned_content)
        
        # Validate required fields
        if not all(key in parsed_json for key in ["title", "description", "tasks"]):
            missing = [key for key in ["title", "description", "tasks"] if key not in parsed_json]
            raise ValueError(f"Missing required fields in JSON: {', '.join(missing)}")
        
        return parsed_json
    except json.JSONDecodeError as e:
        # If JSON parsing fails, print the content for debugging
        print(f"Failed to parse JSON: {e}")
        print(f"Content that failed to parse:\n{cleaned_content}")
        
        # Try a more aggressive approach to extract just the development plan
        try:
            # Find the position after the schema
            schema_end = cleaned_content.find('"definitions"')
            if schema_end != -1:
                # Find the next opening brace after the schema
                plan_start = cleaned_content.find('{', schema_end + 20)
                if plan_start != -1:
                    plan_json = cleaned_content[plan_start:]
                    return json.loads(plan_json)
        except Exception:
            pass
        
        raise

def flatten_tasks(tasks: List[Dict[str, Any]], result: Dict[str, Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Flatten the hierarchical task structure into a dictionary with task_id as keys.
    """
    if result is None:
        result = {}
    
    for task in tasks:
        result[task["task_id"]] = task
        if task.get("tasks"):
            flatten_tasks(task["tasks"], result)
    
    return result

def generate_task_prompts(api_key: str, plan: Dict[str, Any], model: str) -> None:
    """
    Generate detailed implementation prompts for each task in the plan.
    """
    # Flatten the task hierarchy for easy lookup
    all_tasks = flatten_tasks(plan["tasks"])
    total_tasks = len(all_tasks)
    
    print(f"Generating implementation prompts for {total_tasks} tasks...")
    
    # Process tasks in order of their IDs (breadth-first)
    for i, task_id in enumerate(sorted(all_tasks.keys(), key=lambda x: [int(n) if n.isdigit() else n for n in x.split('.')])):
        task = all_tasks[task_id]
        
        # Skip if prompt already exists
        if "prompt" in task and task["prompt"]:
            continue
        
        # Create and call the prompt
        task_prompt = create_task_prompt(plan["title"], plan["description"], task, all_tasks)
        
        print(f"Generating prompt for task {task_id} ({i+1}/{total_tasks}): {task['name']}")
        
        try:
            response = call_api(api_key, task_prompt, model)
            prompt_text = response["choices"][0]["message"]["content"].strip()
            
            # Store the prompt in the task
            task["prompt"] = prompt_text
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"Error generating prompt for task {task_id}: {e}")
            # Set a placeholder prompt
            task["prompt"] = f"[Error generating prompt: {str(e)}]"

def generate_development_plan(api_key: str, vague_idea: str, output_file: str = "plans/development_plan.json", model: str = None) -> None:
    """
    Generate a development plan from a vague idea and save it to a file.
    """
    # Use the environment variable model if not specified
    if model is None:
        model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-pro-exp-02-05:free")
    # Create the prompt
    prompt = create_prompt(vague_idea)
    
    # Call the API
    print(f"Generating development plan for: {vague_idea}")
    response = call_api(api_key, prompt, model)
    
    # Extract the content from the response
    if "choices" not in response or not response["choices"]:
        raise Exception("Unexpected response format from API: 'choices' field missing")
    
    raw_content = response["choices"][0]["message"]["content"].strip()
    
    # Parse and validate the JSON
    parsed_json = parse_and_validate_json(raw_content)
    
    # Apply hierarchical numbering
    apply_hierarchical_numbering(parsed_json["tasks"], "")
    
    # Generate implementation prompts for each task
    generate_task_prompts(api_key, parsed_json, model)
    
    # Create plans directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to file
    with open(output_file, "w") as f:
        json.dump(parsed_json, f, indent=2)
    
    print(f"Development plan successfully saved to {output_file}")
    print(f"Title: {parsed_json['title']}")
    print(f"Number of top-level tasks: {len(parsed_json['tasks'])}")
    
    # Count total tasks including subtasks
    all_tasks = flatten_tasks(parsed_json["tasks"])
    print(f"Total number of tasks: {len(all_tasks)}")
    print(f"All tasks have implementation prompts: {all(('prompt' in task and task['prompt']) for task in all_tasks.values())}")

def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Generate a structured development plan from a vague idea using AI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "idea", 
        nargs="?", 
        help="The vague idea to expand into a development plan"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="plans/development_plan.json",
        help="Output JSON file path"
    )
    
    parser.add_argument(
        "--model", "-m",
        default="google/gemini-2.0-pro-exp-02-05:free",
        help="AI model to use for generation"
    )
    
    return parser.parse_args()

def main():
    """
    Main function to run the script.
    """
    # Parse command line arguments
    args = parse_arguments()
    
    # Check for API key in environment variable
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable is not set.")
        print("Please set the environment variable with your OpenRouter API key:")
        print("  export OPENROUTER_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # Check if idea is provided
    if not args.idea:
        print("Error: No idea provided.")
        print("Please provide a vague idea to expand into a development plan:")
        print("  python development_plan.py 'Create an AI-powered chatbot that assists with coding questions.'")
        print("  python development_plan.py --output custom_plan.json 'Build a recipe recommendation system'")
        sys.exit(1)
    
    try:
        generate_development_plan(api_key, args.idea, args.output, args.model)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
