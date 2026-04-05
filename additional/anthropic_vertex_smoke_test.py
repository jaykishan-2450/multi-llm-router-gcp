"""Minimal Anthropic Vertex smoke test.

Set VERTEX_PROJECT_ID before running:
  PowerShell: $env:VERTEX_PROJECT_ID = "your-project-id"
Then run:
  python anthropic_vertex_smoke_test.py
"""

import os

from anthropic import AnthropicVertex


def main() -> None:
    project_id = os.getenv("VERTEX_PROJECT_ID", "YOUR_PROJECT_ID")
    region = os.getenv("ANTHROPIC_VERTEX_REGION", "global")
    model = os.getenv("ANTHROPIC_VERTEX_MODEL", "claude-sonnet-4-6")

    if project_id == "YOUR_PROJECT_ID":
        raise ValueError("Set VERTEX_PROJECT_ID environment variable before running this script.")

    client = AnthropicVertex(region=region, project_id=project_id)
    message = client.messages.create(
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello! Can you help me?"}],
        model=model,
    )
    print(message.content[0].text)


if __name__ == "__main__":
    main()
