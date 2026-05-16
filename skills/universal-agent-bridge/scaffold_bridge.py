# /// script
# requires-python = ">=3.11"
# ///
import argparse
import os
import sys
from pathlib import Path

def generate_extension(ext_type: str, name: str, dest_dir: str):
    script_dir = Path(__file__).parent.absolute()
    templates_dir = script_dir / "templates"
    dest_path = Path(dest_dir)
    
    # Ensure destination directory exists
    dest_path.mkdir(parents=True, exist_ok=True)
    
    if ext_type == "skill":
        template_file = templates_dir / "skill_template.md"
        output_file = dest_path / "SKILL.md"
    elif ext_type == "command":
        template_file = templates_dir / "command_template.sh"
        output_file = dest_path / f"{name}.sh"
    elif ext_type == "mcp":
        template_file = templates_dir / "mcp_server_template.py"
        output_file = dest_path / f"{name}_server.py"
    else:
        print(f"Error: Unknown extension type '{ext_type}'")
        sys.exit(1)
        
    if not template_file.exists():
        print(f"Error: Template file not found at {template_file}")
        sys.exit(1)
        
    with open(template_file, "r") as f:
        content = f.read()
        
    # Replace placeholders
    content = content.replace("{{NAME}}", name)
    
    with open(output_file, "w") as f:
        f.write(content)
        
    if ext_type == "command":
        # Make shell script executable
        os.chmod(output_file, 0o755)
        
    print(f"Successfully generated {ext_type} '{name}' at {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scaffold cross-platform agent extensions.")
    parser.add_argument("--type", choices=["skill", "command", "mcp"], required=True, help="Type of extension to scaffold")
    parser.add_argument("--name", required=True, help="Name of the extension")
    parser.add_argument("--dest", required=True, help="Destination directory")
    
    args = parser.parse_args()
    
    generate_extension(args.type, args.name, args.dest)
