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
            "1. Explicitly mention the skill name in your response (e.g., 'I will use the file-size-classification skill')\n"
            "2. The full skill documentation will be provided to you automatically\n"
            "3. After reviewing the documentation, output commands using one of these formats:\n\n"
            "**Format 1 - Code Block (Recommended):**\n"
            "```bash\n"
            "python script.py /path/to/directory --arg1 value1 --arg2 value2\n"
            "```\n\n"
            "**Format 2 - Shell Prefix:**\n"
            "```\n"
            "$ ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4\n"
            "```\n\n"
            "**Important Notes:**\n"
            "- Commands will be executed automatically and their output will be provided back to you\n"
            "- When you first mention a skill, wait for the full skill documentation to be provided. Do not output commands until you have received and reviewed the complete documentation\n"
            "- When executing Python scripts, use the script name directly without path prefixes (e.g., 'python script.py' not 'python /path/to/script.py'). The system will locate the script automatically\n"
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
        Handles Python commands with automatic venv activation.
        
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
        
        logger.info(f"Executing command: {command}")
        logger.info(f"Working directory: {cwd}")
        
        try:
            # Check if it's a Python command
            if command.startswith('python '):
                # Activate venv and run Python command
                success, stdout, stderr = self._execute_python_command(command, cwd)
            else:
                # Execute as shell command
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
        # Parse the command to extract script name and arguments
        # Format: "python script.py arg1 arg2 ..."
        parts = command.split()
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
        
        # Build the command with absolute script path
        reconstructed_command = f"python {script_path} {' '.join(script_args)}"
        
        # Get absolute path to venv activate script
        project_root = Path(__file__).parent.parent
        venv_activate = project_root / self.venv_path / "bin" / "activate"
        
        if venv_activate.exists():
            # Use bash to source the venv and run the command
            full_command = f"source {venv_activate} && {reconstructed_command}"
            shell_cmd = ["/bin/bash", "-c", full_command]
        else:
            logger.warning(f"Virtual environment not found at {self.venv_path}, running without venv")
            shell_cmd = reconstructed_command.split()
        
        logger.info(f"Executing: {reconstructed_command}")
        logger.info(f"Working directory: {cwd}")
        
        return self._run_subprocess(shell_cmd, cwd)
    
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
                logger.info(f"Command succeeded (exit code: {result.returncode})")
            else:
                logger.error(f"Command failed (exit code: {result.returncode})")
            
            return success, stdout, stderr
            
        except subprocess.TimeoutExpired:
            logger.error("Command timed out after 300 seconds")
            return False, "", "Command timed out after 300 seconds"
        except Exception as e:
            logger.error(f"Subprocess execution failed: {e}")
            return False, "", str(e)
    
    def extract_commands_from_text(self, text: str) -> List[str]:
        """
        Extract command strings from model output.
        Follows the command format specified in the system prompt:
        - Code blocks with bash/shell/python/sh tags
        - Lines starting with $ or >
        
        Args:
            text: Text to search for commands
            
        Returns:
            List of extracted commands (deduplicated and ordered)
        """
        commands = []
        seen_commands = set()  # Track seen commands to avoid duplicates
        
        # Pattern 1: Code blocks with language tags (bash, shell, python, sh)
        # This is the recommended format from system prompt
        code_block_pattern = r'```(?:bash|shell|python|sh)\s*\n(.*?)```'
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            code = match.group(1).strip()
            # Split by newlines and filter out comments and empty lines
            for line in code.split('\n'):
                line = line.strip()
                # Remove shell prompt if present
                if line.startswith('$ ') or line.startswith('> '):
                    line = line[2:].strip()
                # Skip comments and empty lines
                if line and not line.startswith('#') and line not in seen_commands:
                    commands.append(line)
                    seen_commands.add(line)
        
        # Pattern 2: Generic code blocks (without language tag) containing shell prompts
        # Format: ```\n$ command\n```
        generic_block_pattern = r'```\s*\n(.*?)```'
        for match in re.finditer(generic_block_pattern, text, re.DOTALL):
            code = match.group(1).strip()
            for line in code.split('\n'):
                line = line.strip()
                # Only extract lines with shell prompt in generic blocks
                if line.startswith('$ ') or line.startswith('> '):
                    cmd = line[2:].strip()
                    if cmd and not cmd.startswith('#') and cmd not in seen_commands:
                        commands.append(cmd)
                        seen_commands.add(cmd)
        
        # Log extracted commands for debugging
        if commands:
            logger.debug(f"Extracted {len(commands)} command(s) from text")
            for i, cmd in enumerate(commands, 1):
                logger.debug(f"  Command {i}: {cmd}")
        else:
            logger.debug("No commands extracted from text")
        
        return commands

