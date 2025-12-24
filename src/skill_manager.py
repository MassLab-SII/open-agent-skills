"""
Skill Manager Module
====================

This module manages skills that can be dynamically loaded and used by agents.
Skills are defined in the skill/ directory with SKILL.md files containing
YAML frontmatter and usage instructions.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SkillMetadata:
    """Metadata extracted from SKILL.md YAML frontmatter"""
    name: str
    description: str
    skill_path: Path
    full_content: str


class SkillManager:
    """
    Manages skill discovery, loading, and execution.
    
    Skills are Python scripts or commands that can be invoked by the agent
    to perform specialized tasks. Each skill has a SKILL.md file with:
    - YAML frontmatter: name and description
    - Full documentation: usage examples and parameters
    """
    
    def __init__(self, skill_dir: str = "skills", venv_path: Optional[str] = None):
        """
        Initialize the skill manager.
        
        Args:
            skill_dir: Directory containing skill folders
            venv_path: Path to virtual environment (default: .venv)
        """
        self.skill_dir = Path(skill_dir)
        self.venv_path = Path(venv_path) if venv_path else Path(".venv")
        self.skills: Dict[str, SkillMetadata] = {}
        self._scan_skills()
    
    def _scan_skills(self):
        """Scan the skill directory and load all SKILL.md files"""
        if not self.skill_dir.exists():
            logger.warning(f"Skill directory not found: {self.skill_dir}")
            return
        
        for skill_folder in self.skill_dir.iterdir():
            if not skill_folder.is_dir():
                continue
            
            skill_md_path = skill_folder / "SKILL.md"
            if not skill_md_path.exists():
                continue
            
            try:
                metadata = self._parse_skill_md(skill_md_path, skill_folder)
                if metadata:
                    self.skills[metadata.name] = metadata
                    logger.debug(f"Loaded skill: {metadata.name}")
            except Exception as e:
                logger.error(f"Failed to load skill from {skill_folder}: {e}")
    
    def _parse_skill_md(self, md_path: Path, skill_folder: Path) -> Optional[SkillMetadata]:
        """
        Parse SKILL.md file to extract metadata and full content.
        
        Args:
            md_path: Path to SKILL.md file
            skill_folder: Path to the skill folder
            
        Returns:
            SkillMetadata object or None if parsing fails
        """
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if not frontmatter_match:
            logger.warning(f"No YAML frontmatter found in {md_path}")
            return None
        
        frontmatter = frontmatter_match.group(1)
        
        # Parse YAML frontmatter (simple parsing for name and description)
        name_match = re.search(r'^name:\s*(.+)$', frontmatter, re.MULTILINE)
        desc_match = re.search(r'^description:\s*(.+)$', frontmatter, re.MULTILINE)
        
        if not name_match or not desc_match:
            logger.warning(f"Missing name or description in {md_path}")
            return None
        
        return SkillMetadata(
            name=name_match.group(1).strip(),
            description=desc_match.group(1).strip(),
            skill_path=skill_folder,
            full_content=content
        )
    
    def get_skill_summary_prompt(self) -> str:
        """
        Generate a summary prompt containing all skill metadata.
        This is added to the system prompt to inform the agent about available skills.
        
        Returns:
            Formatted string with skill summaries
        """
        if not self.skills:
            return ""
        
        prompt_parts = [
            "\n## Available Skills\n",
            "You are equipped with the following specialized skills. "
            "When a task aligns with a specific skill, adopt the methodology described within that skill. "
            "For tasks that do not fall under any specific skill, proceed by using your own reasoning and inherent knowledge.\n"
        ]
        
        for skill_name, metadata in self.skills.items():
            prompt_parts.append(f"\n- **{skill_name}**: {metadata.description}")
        
        prompt_parts.append(
            "\n\n### Skill Usage Protocol\n\n"
            "When you identify that a task requires a skill:\n"
            "1. Explicitly mention the skill name in your response (e.g., 'I will use the file-size-classification skill') and stop this response IMMEDIATELY.\n"
            "2. The full skill documentation will be provided to you automatically\n"
            "3. After reviewing the documentation, output commands using one of these formats:\n\n"
            "**Format - Code Block:**\n"
            "```bash\n"
            "python script.py /path/to/directory --arg1 value1 --arg2 value2\n"
            "```\n\n"
            "**Important Notes:**\n"
            "- Commands will be executed automatically and their output will be provided back to you\n"
            "- After mentioning a skill by name, STOP your current response immediately. Do NOT output ANY commands until the next turn, when you receive and review the complete skill specification (including name, description, and usage instructions).\n"
            "- When executing Python scripts, use the script name directly without path prefixes (e.g., 'python script.py' not 'python /path/to/script.py'). The system will locate the script automatically\n"
            "Now, in this turn, please output ONLY the skill you have selected. Use the following format: 'I will use the [skill name] skill'. Do NOT output any code or commands besides this statement.\n"
        )
        
        return "".join(prompt_parts)
    
    def detect_skill_trigger(self, text: str) -> Optional[str]:
        """
        Detect if the agent's response mentions a skill.
        
        Args:
            text: Text to search for skill mentions
            
        Returns:
            Skill name if detected, None otherwise
        """
        text_lower = text.lower()
        
        for skill_name in self.skills.keys():
            # Check for exact skill name mention
            if skill_name.lower() in text_lower:
                return skill_name
            
            # Check for skill name with spaces replaced by hyphens/underscores
            normalized_name = skill_name.replace('-', ' ').replace('_', ' ')
            if normalized_name.lower() in text_lower:
                return skill_name
        
        return None
    
    def get_skill_full_content(self, skill_name: str) -> Optional[str]:
        """
        Get the full SKILL.md content for a specific skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Full SKILL.md content or None if skill not found
        """
        metadata = self.skills.get(skill_name)
        if not metadata:
            return None
        
        return metadata.full_content
    
    def _locate_skill_script(self, script_name: str) -> Optional[Path]:
        """
        Locate a skill script by searching in all skill directories.
        
        Args:
            script_name: Name of the script file (e.g., "classify_files_by_size.py")
            
        Returns:
            Absolute path to the script if found, None otherwise
        """
        
        # Search in all skill subdirectories
        for skill_folder in self.skill_dir.iterdir():
            if not skill_folder.is_dir():
                continue
            
            script_path = skill_folder / script_name
            if script_path.exists():
                logger.debug(f"Located script '{script_name}' in {skill_folder.name}: {script_path}")
                return script_path.resolve()
        
        logger.warning(f"Script '{script_name}' not found in any skill directory")
        return None
    
    def parse_and_execute_command(
        self, 
        command: str, 
        working_dir: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Parse and execute a command from the model's output.
        Handles Python commands with automatic venv environment.
        
        Args:
            command: Command string to execute
            working_dir: Working directory for command execution
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        command = command.strip()
        
        # Determine working directory
        if working_dir:
            cwd = Path(working_dir)
        else:
            cwd = Path.cwd()
        
        logger.debug(f"Executing command: {command}")
        logger.debug(f"Working directory: {cwd}")
        
        try:
            # Check if it's a Python command
            if command.startswith('python '):
                # Activate venv and run Python command
                success, stdout, stderr = self._execute_python_command(command, cwd)
            else:
                # Execute as shell command. We do not use this in this project.
                success, stdout, stderr = self._execute_shell_command(command, cwd)
            
            return success, stdout, stderr
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return False, "", str(e)
    
    def _execute_python_command(self, command: str, cwd: Path) -> Tuple[bool, str, str]:
        """
        Execute a Python command with venv activation.
        Automatically locates skill scripts in the skill directory.
        
        Args:
            command: Python command (e.g., "python script.py arg1 arg2")
            cwd: Working directory
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        import shlex
        
        # Special handling for run_fs_ops.py -c "..." commands containing write_file
        # These often contain complex strings that break shlex parsing
        if 'run_fs_ops.py' in command and ' -c ' in command and 'write_file' in command:
            return self._execute_write_file_command(command, cwd)
        
        # Parse the command to extract script name and arguments
        # Use shlex to properly handle quoted arguments with special characters
        try:
            parts = shlex.split(command)
        except ValueError as e:
            logger.error(f"Failed to parse command: {command}, error: {e}")
            return False, "", f"Failed to parse command: {e}"
        
        if len(parts) < 2:
            logger.error(f"Invalid python command format: {command}")
            return False, "", "Invalid command format"
        
        script_name = parts[1]  # e.g., "classify_files_by_size.py"
        script_args = parts[2:] if len(parts) > 2 else []
        
        # Check if script_name is already an absolute path
        script_path = Path(script_name)
        if not script_path.is_absolute():
            # Try to locate the script in skill directories
            script_path = self._locate_skill_script(script_name)
            if not script_path:
                logger.error(f"Could not locate script: {script_name}")
                return False, "", f"Script not found: {script_name}"
        
        # Verify script exists
        if not script_path.exists():
            logger.error(f"Script does not exist: {script_path}")
            return False, "", f"Script not found: {script_path}"
        
        # Get absolute path to venv activate script
        project_root = Path(__file__).parent.parent
        venv_activate = project_root / self.venv_path / "bin" / "activate"
        
        # Determine the Python executable to use
        if venv_activate.exists():
            # Use the venv's Python executable directly (avoids shell escaping issues)
            python_executable = project_root / self.venv_path / "bin" / "python"
            if not python_executable.exists():
                python_executable = "python"  # Fallback
        else:
            logger.warning(f"Virtual environment not found at {self.venv_path}, running without venv")
            python_executable = "python"
        
        # Build command as a list (NOT a string) to preserve newlines in arguments
        # This avoids shell interpretation issues entirely
        shell_cmd = [str(python_executable), str(script_path)] + script_args
        
        logger.debug(f"Executing (list form): {shell_cmd}")
        logger.debug(f"Working directory: {cwd}")
        
        return self._run_subprocess(shell_cmd, cwd)
    
    def _execute_write_file_command(self, command: str, cwd: Path) -> Tuple[bool, str, str]:
        """
        Special handler for run_fs_ops.py -c "..." commands.
        
        These commands often contain complex strings (especially write_file with multi-line content)
        that break standard shlex parsing. This method uses manual parsing to extract the -c argument.
        
        Args:
            command: Full command string like 'python run_fs_ops.py -c "await fs.write_file(...)"'
            cwd: Working directory
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        # Locate run_fs_ops.py script
        script_path = self._locate_skill_script("run_fs_ops.py")
        if not script_path:
            logger.error("Could not locate run_fs_ops.py")
            return False, "", "Script not found: run_fs_ops.py"
        
        # Extract the -c argument manually
        # Pattern: python run_fs_ops.py -c "..." or python run_fs_ops.py -c '...'
        c_flag_pos = command.find(' -c ')
        if c_flag_pos == -1:
            logger.error("Could not find -c flag in run_fs_ops.py command")
            return False, "", "Invalid run_fs_ops.py command format"
        
        # Get everything after -c (skip the space after -c)
        after_c = command[c_flag_pos + 4:].strip()
        
        if not after_c:
            logger.error("No argument found after -c flag")
            return False, "", "No argument after -c flag"
        
        quote_char = after_c[0]
        if quote_char not in ('"', "'"):
            # Not quoted, just use the rest as-is
            code_arg = after_c
        else:
            # Find the matching closing quote using manual parsing
            code_arg = self._extract_quoted_string(after_c, quote_char)
            if code_arg is None:
                logger.error("Could not extract quoted argument from -c flag")
                return False, "", "Failed to parse -c argument"
        
        logger.debug(f"Extracted -c argument (length={len(code_arg)})")
        
        # Get Python executable
        project_root = Path(__file__).parent.parent
        venv_activate = project_root / self.venv_path / "bin" / "activate"
        
        if venv_activate.exists():
            python_executable = project_root / self.venv_path / "bin" / "python"
            if not python_executable.exists():
                python_executable = "python"
        else:
            python_executable = "python"
        
        # Build command - pass the code as a single argument
        shell_cmd = [str(python_executable), str(script_path), "-c", code_arg]
        
        logger.debug(f"Executing fs_ops command with -c argument")
        logger.debug(f"Working directory: {cwd}")
        
        return self._run_subprocess(shell_cmd, cwd)
    
    def _extract_quoted_string(self, s: str, quote_char: str) -> Optional[str]:
        """
        Extract the content of a quoted string from the beginning of s.
        
        Does NOT process escape sequences - keeps them as-is for passing to run_fs_ops.py
        which will handle them via Python's eval().
        
        Args:
            s: String starting with a quote character
            quote_char: The quote character (" or ')
            
        Returns:
            The content inside the quotes (escapes preserved), or None if parsing fails
        """
        if not s or s[0] != quote_char:
            return None
        
        result = []
        i = 1  # Start after opening quote
        
        while i < len(s):
            char = s[i]
            
            if char == '\\' and i + 1 < len(s):
                # Escape sequence - keep as-is (don't process)
                next_char = s[i + 1]
                result.append(char)
                result.append(next_char)
                i += 2
            elif char == quote_char:
                # Found closing quote
                return ''.join(result)
            else:
                result.append(char)
                i += 1
        
        # No closing quote found - return what we have (best effort)
        logger.warning("No closing quote found, using best-effort extraction")
        return ''.join(result)
    
    def _execute_shell_command(self, command: str, cwd: Path) -> Tuple[bool, str, str]:
        """
        Execute a shell command.
        
        Args:
            command: Shell command
            cwd: Working directory
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        shell_cmd = ["/bin/bash", "-c", command]
        return self._run_subprocess(shell_cmd, cwd)
    
    def _run_subprocess(self, cmd: List[str], cwd: Path) -> Tuple[bool, str, str]:
        """
        Run a subprocess and capture output.
        
        Args:
            cmd: Command as list of strings
            cwd: Working directory
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            stdout = result.stdout
            stderr = result.stderr
            
            if success:
                logger.debug(f"Command succeeded (exit code: {result.returncode})")
            else:
                logger.error(f"Command failed (exit code: {result.returncode})")
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            logger.error("Command timed out after 300 seconds")
            return False, "", "Command timed out after 300 seconds"
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            return False, "", str(e)
    
    def _check_quotes_balanced(self, s: str) -> bool:
        """
        Check if quotes are balanced in a string.
        
        This is a manual implementation that handles escaped quotes and
        works correctly with strings containing \\n escape sequences
        (which shlex.split() fails on).
        
        Args:
            s: String to check
            
        Returns:
            True if quotes are balanced, False otherwise
        """
        in_single_quote = False
        in_double_quote = False
        i = 0
        
        while i < len(s):
            char = s[i]
            
            # Handle escape sequences
            if char == '\\' and i + 1 < len(s):
                # Skip escaped character
                i += 2
                continue
            
            # Toggle quote state
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            
            i += 1
        
        # Quotes are balanced if we're not inside any quote
        return not in_single_quote and not in_double_quote
    
    def extract_commands_from_text(self, text: str) -> List[str]:
        """
        Extract command strings from model output.
        Follows the command format specified in the system prompt: Code blocks with bash/shell/python/sh tags
        
        Args:
            text: Text to search for commands
            
        Returns:
            List of extracted commands (deduplicated and ordered)
        """
        import shlex
        
        command = []
        
        def extract_commands_from_code(code: str) -> List[str]:
            """
            Extract commands from a code block, handling multi-line quoted strings.
            
            Args:
                code: The code block content
                
            Returns:
                List of complete commands
            """
            result = []
            lines = code.split('\n')
            current_command = []
            in_quotes = False
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines and comments when not in a quoted string
                if not in_quotes:
                    if not stripped or stripped.startswith('#'):
                        continue
                    
                
                # Add this line to current command
                if current_command:
                    current_command.append(line)  # Keep original whitespace for multi-line
                else:
                    current_command.append(stripped)
                
                # Check quote state by scanning the accumulated command
                full_cmd = '\n'.join(current_command)
                
                # Special handling for fs.write_file commands - use manual quote matching
                # because shlex.split() fails on long strings with \n escape sequences
                if 'fs.write_file' in full_cmd or 'write_file' in full_cmd:
                    # Use manual quote balance check
                    if self._check_quotes_balanced(full_cmd):
                        complete_cmd = full_cmd.strip()
                        if complete_cmd:
                            result.append(complete_cmd)
                        current_command = []
                        in_quotes = False
                    else:
                        in_quotes = True
                else:
                    # Use shlex to check if quotes are balanced
                    try:
                        shlex.split(full_cmd)
                        # If no exception, quotes are balanced - command is complete
                        complete_cmd = full_cmd.strip()
                        if complete_cmd:
                            result.append(complete_cmd)
                        current_command = []
                        in_quotes = False
                    except ValueError:
                        # Unbalanced quotes - continue accumulating
                        in_quotes = True
            
            # Handle any remaining accumulated command (even if quotes unbalanced)
            if current_command:
                complete_cmd = '\n'.join(current_command).strip()
                if complete_cmd:
                    result.append(complete_cmd)
            
            return result
        
        # This is the recommended format from system prompt
        code_block_pattern = r'```(?:bash|shell|python|sh)\s*\n(.*?)```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            command = extract_commands_from_code(code)
        
        # Log extracted command for debugging
        if command:
            logger.debug(f"Extracted {len(command)} command(s) from text")
        else:
            logger.debug("No commands extracted from text")
        
        return command
