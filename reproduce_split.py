import script_reproducer
import sys

command = 'python find_commit.py mcpmark-eval-enigma build-your-own-x --query "RAG for Document Search" --limit 200'

parts = command.split()
script_name = parts[1]
script_args = parts[2:]
reconstructed_command = f"python {script_name} {' '.join(script_args)}"

print(f"Original: {command}")
print(f"Parts: {parts}")
print(f"Reconstructed: {reconstructed_command}")

# python find_commit.py mcpmark-eval-enigma build-your-own-x --query "RAG for Document Search" --limit 200
# Parts: ['python', 'find_commit.py', 'mcpmark-eval-enigma', 'build-your-own-x', '--query', '"RAG', 'for', 'Document', 'Search"', '--limit', '200']
# Reconstructed: python find_commit.py mcpmark-eval-enigma build-your-own-x --query "RAG for Document Search" --limit 200

# It seems identical string.
