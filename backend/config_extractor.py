import json
import re

def extract_client_config_from_readme(readme_text):
    """
    Look for JSON code blocks in the README and try to find one containing 'mcpServers'.
    """
    code_blocks = re.findall(r"```json(.*?)```", readme_text, re.DOTALL)

    for block in code_blocks:
        try:
            parsed = json.loads(block.strip())
            if "mcpServers" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue

    return None
