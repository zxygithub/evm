#!/usr/bin/env python3
"""
EVM - Environment Variable Manager
A command-line tool for managing environment variables.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class EnvironmentManager:
    """Core class for managing environment variables."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize the environment manager.
        
        Args:
            env_file: Path to the environment file (default: ~/.evm/env.json)
        """
        if env_file is None:
            self.env_file = Path.home() / '.evm' / 'env.json'
        else:
            self.env_file = Path(env_file)
        
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        self._env_vars = self._load_env_vars()

    def _load_env_vars(self) -> Dict[str, str]:
        """Load environment variables from storage file."""
        if not self.env_file.exists():
            return {}
        try:
            with open(self.env_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_env_vars(self) -> None:
        """Save environment variables to storage file."""
        try:
            with open(self.env_file, 'w', encoding='utf-8') as f:
                json.dump(self._env_vars, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving environment variables: {e}", file=sys.stderr)
            sys.exit(1)

    def set(self, key: str, value: str) -> None:
        """Set an environment variable."""
        self._env_vars[key] = value
        self._save_env_vars()
        print(f"Set: {key}={value}")

    def get(self, key: str) -> Optional[str]:
        """Get an environment variable."""
        value = self._env_vars.get(key)
        if value is None:
            print(f"Environment variable '{key}' not found", file=sys.stderr)
            sys.exit(1)
        print(value)
        return value

    def delete(self, key: str) -> None:
        """Delete an environment variable."""
        if key in self._env_vars:
            del self._env_vars[key]
            self._save_env_vars()
            print(f"Deleted: {key}")
        else:
            print(f"Environment variable '{key}' not found", file=sys.stderr)
            sys.exit(1)

    def exists(self, key: str) -> bool:
        """Check if an environment variable exists."""
        return key in self._env_vars

    def list(self, pattern: Optional[str] = None, group: Optional[str] = None,
             show_groups: bool = False, no_prefix: bool = False) -> None:
        """List all environment variables."""
        if not self._env_vars:
            print("No environment variables set")
            return

        # Filter by group if specified
        if group:
            prefix = f"{group}:"
            filtered_vars = {k: v for k, v in self._env_vars.items() if k.startswith(prefix)}
            if not filtered_vars:
                print(f"No environment variables in group '{group}'")
                return
        elif pattern:
            filtered_vars = {k: v for k, v in self._env_vars.items()
                           if pattern.lower() in k.lower()}
        else:
            filtered_vars = self._env_vars

        if not filtered_vars:
            if pattern:
                print(f"No environment variables match pattern '{pattern}'")
            return

        # If show_groups is True, group by namespace
        if show_groups:
            self._list_by_groups(filtered_vars)
            return

        # Remove group prefix if no_prefix is True
        if no_prefix and group:
            display_vars = {}
            prefix = f"{group}:"
            for key, value in filtered_vars.items():
                new_key = key[len(prefix):] if key.startswith(prefix) else key
                display_vars[new_key] = value
        else:
            display_vars = filtered_vars

        # Calculate column widths
        max_key_len = max(len(k) for k in display_vars.keys())
        
        print("\nEnvironment Variables:")
        print("-" * (max_key_len + 50))
        for key, value in sorted(display_vars.items()):
            print(f"{key:<{max_key_len}} = {value}")
        print("-" * (max_key_len + 50))
        print(f"Total: {len(display_vars)} variables")

    def _list_by_groups(self, vars_dict: Dict[str, str]) -> None:
        """List variables grouped by namespace."""
        groups = {}
        for key, value in vars_dict.items():
            if ':' in key:
                group, var_name = key.split(':', 1)
            else:
                group = 'default'
                var_name = key
            if group not in groups:
                groups[group] = {}
            groups[group][var_name] = value

        if not groups:
            print("No environment variables to display")
            return

        print("\nEnvironment Variables (by group):")
        print("=" * 70)
        for group_name in sorted(groups.keys()):
            print(f"\n[{group_name}]")
            print("-" * 70)
            group_vars = groups[group_name]
            max_key_len = max(len(k) for k in group_vars.keys()) if group_vars else 0
            for key, value in sorted(group_vars.items()):
                print(f"{key:<{max_key_len}} = {value}")
            print("-" * 70)
            print(f"{len(group_vars)} variables")
        print("\n+" * 70)
        print(f"Total: {len(groups)} groups, {len(vars_dict)} variables")

    def clear(self) -> None:
        """Clear all environment variables."""
        if self._env_vars:
            self._env_vars.clear()
            self._save_env_vars()
            print("All environment variables cleared")
        else:
            print("No environment variables to clear")

    def export(self, format_type: str = 'json', output_file: Optional[str] = None,
               group: Optional[str] = None) -> None:
        """Export environment variables to a file."""
        # Filter by group if specified
        if group:
            export_vars = {k: v for k, v in self._env_vars.items()
                         if k.startswith(f"{group}:")}
            if not export_vars:
                print(f"No environment variables in group '{group}'")
                return
        else:
            export_vars = self._env_vars

        if not export_vars:
            print("No environment variables to export")
            return

        if output_file:
            output_path = Path(output_file)
        else:
            output_path = Path.cwd() / f"env.{format_type}"

        try:
            if format_type == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(export_vars, f, indent=2, ensure_ascii=False)
            elif format_type == 'env':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for key, value in sorted(export_vars.items()):
                        f.write(f'{key}={value}\n')
            elif format_type == 'sh':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('#!/bin/bash\n\n')
                    for key, value in sorted(export_vars.items()):
                        f.write(f'export {key}={value}\n')
            else:
                print(f"Unsupported format: {format_type}", file=sys.stderr)
                sys.exit(1)
            print(f"Environment variables exported to: {output_path}")
        except IOError as e:
            print(f"Error exporting environment variables: {e}", file=sys.stderr)
            sys.exit(1)

    def load(self, input_file: str, format_type: Optional[str] = None,
             replace: bool = False, group: Optional[str] = None,
             nest: bool = False) -> None:
        """Load environment variables from a file.

        Args:
            input_file: Path to the input file
            format_type: Force format ('json', 'env', or 'backup')
            replace: Replace existing variables instead of merging
            group: Add imported variables to a specific group
            nest: Treat first-level keys as group names (for nested JSON)
        """
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"File not found: {input_file}", file=sys.stderr)
            sys.exit(1)

        try:
            # Determine format
            if format_type:
                fmt = format_type.lower()
            elif input_path.suffix in ['.json', '.backup']:
                fmt = 'json'
            elif input_path.suffix == '.env':
                fmt = 'env'
            else:
                # Try to detect format from content
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read(100)
                        if content.strip().startswith('{'):
                            fmt = 'json'
                        else:
                            fmt = 'env'
                except:
                    fmt = 'json'  # Default to JSON

            # Load based on format
            if fmt in ['json', 'backup']:
                with open(input_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle nested JSON with --nest option
                if nest and isinstance(data, dict):
                    # Check if data has nested objects (first-level keys are groups)
                    loaded_vars = {}
                    for group_name, group_data in data.items():
                        if isinstance(group_data, dict):
                            # This is a group - add all key-value pairs with group prefix
                            for key, value in group_data.items():
                                loaded_vars[f"{group_name}:{key}"] = value
                        else:
                            # This is a simple key-value pair, add as-is
                            loaded_vars[group_name] = group_data
                elif isinstance(data, dict) and 'variables' in data:
                    # It's a backup file (with 'variables' field)
                    loaded_vars = data['variables']
                    timestamp = data.get('timestamp', 'unknown')
                    print(f"Detected backup file (timestamp: {timestamp})")
                elif isinstance(data, dict):
                    loaded_vars = data
                else:
                    print("Invalid JSON format: expected a dictionary", file=sys.stderr)
                    sys.exit(1)
            elif fmt == 'env':
                loaded_vars = {}
                with open(input_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip().strip("'").strip('"')
                                loaded_vars[key] = value
            else:
                print(f"Unsupported format: {fmt}", file=sys.stderr)
                sys.exit(1)

            # Add group prefix if specified
            if group and not nest:
                grouped_vars = {}
                for key, value in loaded_vars.items():
                    if not key.startswith(f"{group}:"):
                        grouped_vars[f"{group}:{key}"] = value
                    else:
                        grouped_vars[key] = value
                loaded_vars = grouped_vars

            # Show summary for nested import
            if nest and isinstance(data, dict):
                groups_detected = sum(1 for v in data.values() if isinstance(v, dict))
                print(f"Detected and imported {groups_detected} groups from nested structure")

            # Apply to environment
            if replace:
                self._env_vars = loaded_vars
                print(f"Replaced environment variables ({len(loaded_vars)} total)")
            else:
                self._env_vars.update(loaded_vars)
                print(f"Loaded {len(loaded_vars)} environment variables from {input_file}")

            self._save_env_vars()

            # Show summary
            if group:
                print(f"Variables added to group '{group}'")
        except (json.JSONDecodeError, IOError, ValueError) as e:
            print(f"Error loading environment variables: {e}", file=sys.stderr)
            sys.exit(1)

    def execute(self, command: List[str]) -> None:
        """Execute a command with environment variables."""
        if not command:
            print("No command specified", file=sys.stderr)
            sys.exit(1)

        # Create a copy of current environment and update with our variables
        env_copy = os.environ.copy()
        
        # Convert all values to strings (os.environ requires string values)
        for key, value in self._env_vars.items():
            env_copy[key] = str(value)

        try:
            # Execute the command
            os.execvpe(command[0], command, env_copy)
        except FileNotFoundError:
            print(f"Command not found: {command[0]}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error executing command: {e}", file=sys.stderr)
            sys.exit(1)

    def rename(self, old_key: str, new_key: str) -> None:
        """Rename an environment variable."""
        if old_key not in self._env_vars:
            print(f"Environment variable '{old_key}' not found", file=sys.stderr)
            sys.exit(1)
        if new_key in self._env_vars:
            print(f"Environment variable '{new_key}' already exists", file=sys.stderr)
            sys.exit(1)
        value = self._env_vars.pop(old_key)
        self._env_vars[new_key] = value
        self._save_env_vars()
        print(f"Renamed: {old_key} -> {new_key}")

    def copy(self, src_key: str, dst_key: str) -> None:
        """Copy an environment variable."""
        if src_key not in self._env_vars:
            print(f"Environment variable '{src_key}' not found", file=sys.stderr)
            sys.exit(1)
        self._env_vars[dst_key] = self._env_vars[src_key]
        self._save_env_vars()
        print(f"Copied: {src_key} -> {dst_key}")

    def search(self, pattern: str, search_value: bool = False) -> None:
        """Search environment variables by key or value."""
        results = {}
        for key, value in self._env_vars.items():
            if pattern.lower() in key.lower():
                results[key] = value
            elif search_value and pattern.lower() in str(value).lower():
                results[key] = value

        if not results:
            search_text = "key and value" if search_value else "key"
            print(f"No environment variables match '{pattern}' in {search_text}")
            return

        max_key_len = max(len(k) for k in results.keys())
        print(f"\nSearch results for '{pattern}':")
        print("-" * (max_key_len + 50))
        for key, value in sorted(results.items()):
            print(f"{key:<{max_key_len}} = {value}")
        print("-" * (max_key_len + 50))
        print(f"Total: {len(results)} matches")

    def backup(self, backup_file: Optional[str] = None) -> None:
        """Backup environment variables to a file."""
        if backup_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = Path.home() / '.evm' / f"backup_{timestamp}.json"
        else:
            backup_file = Path(backup_file)

        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'variables': self._env_vars
        }

        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            print(f"Backup created: {backup_file}")
        except IOError as e:
            print(f"Error creating backup: {e}", file=sys.stderr)
            sys.exit(1)

    def restore(self, backup_file: str, merge: bool = False) -> None:
        """Restore environment variables from a backup file."""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"Backup file not found: {backup_file}", file=sys.stderr)
            sys.exit(1)

        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            if 'variables' not in backup_data:
                print("Invalid backup file format", file=sys.stderr)
                sys.exit(1)

            restored_vars = backup_data['variables']
            if merge:
                self._env_vars.update(restored_vars)
                print(f"Merged {len(restored_vars)} variables from backup")
            else:
                self._env_vars = restored_vars
                print(f"Restored {len(restored_vars)} variables from backup")

            self._save_env_vars()
            if 'timestamp' in backup_data:
                print(f"Backup timestamp: {backup_data['timestamp']}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error restoring from backup: {e}", file=sys.stderr)
            sys.exit(1)

    def set_grouped(self, group: str, key: str, value: str) -> None:
        """Set an environment variable in a specific group."""
        full_key = f"{group}:{key}" if group else key
        self._env_vars[full_key] = value
        self._save_env_vars()
        group_info = f"[{group}]" if group else ""
        print(f"Set: {group_info}{key} = {value}")

    def get_grouped(self, group: str, key: str) -> Optional[str]:
        """Get an environment variable from a specific group."""
        full_key = f"{group}:{key}" if group else key
        value = self._env_vars.get(full_key)
        if value is None:
            # Try without group prefix
            if group:
                value = self._env_vars.get(key)
            if value is None:
                var_name = f"{group}:{key}" if group else key
                print(f"Environment variable '{var_name}' not found", file=sys.stderr)
                sys.exit(1)
        print(value)
        return value

    def delete_grouped(self, group: str, key: str) -> None:
        """Delete an environment variable from a specific group."""
        full_key = f"{group}:{key}" if group else key
        if full_key in self._env_vars:
            del self._env_vars[full_key]
            self._save_env_vars()
            group_info = f"[{group}]" if group else ""
            print(f"Deleted: {group_info}{key}")
        else:
            var_name = f"{group}:{key}" if group else key
            print(f"Environment variable '{var_name}' not found", file=sys.stderr)
            sys.exit(1)

    def list_groups(self) -> None:
        """List all groups."""
        groups = set()
        for key in self._env_vars.keys():
            if ':' in key:
                group = key.split(':', 1)[0]
                groups.add(group)

        if not groups:
            print("No groups found. All variables are in the default namespace.")
            return

        print("\nAvailable Groups:")
        print("-" * 50)
        for group in sorted(groups):
            # Count variables in this group
            count = sum(1 for k in self._env_vars.keys() if k.startswith(f"{group}:"))
            print(f"{group:<30} ({count} variables)")
        print("-" * 50)
        print(f"Total: {len(groups)} groups")

    def list_group(self, group: str, no_prefix: bool = False) -> None:
        """List variables in a specific group."""
        self.list(group=group, no_prefix=no_prefix)

    def delete_group(self, group: str) -> None:
        """Delete all variables in a group."""
        if group == 'default':
            print("Cannot delete default namespace. Use 'clear' to remove all variables.", file=sys.stderr)
            sys.exit(1)

        prefix = f"{group}:"
        to_delete = [k for k in self._env_vars.keys() if k.startswith(prefix)]

        if not to_delete:
            print(f"Group '{group}' not found or has no variables", file=sys.stderr)
            sys.exit(1)

        for key in to_delete:
            del self._env_vars[key]
        self._save_env_vars()
        print(f"Deleted group '{group}' and all its variables ({len(to_delete)} total)")

    def move_to_group(self, key: str, new_group: str) -> None:
        """Move an existing variable to a different group."""
        if key not in self._env_vars:
            print(f"Environment variable '{key}' not found", file=sys.stderr)
            sys.exit(1)

        value = self._env_vars.pop(key)
        new_key = f"{new_group}:{key}"
        self._env_vars[new_key] = value
        self._save_env_vars()
        print(f"Moved: {key} -> {new_key}")

    def load_to_memory(self, filter_prefix: Optional[str] = None, add_evm_prefix: bool = True) -> None:
        """Load environment variables from file to system memory (os.environ).
        
        Args:
            filter_prefix: Only load variables with keys starting with this prefix
            add_evm_prefix: Whether to add 'EVM:' prefix to variable names (default: True)
        """
        import os
        loaded_count = 0
        
        for key, value in self._env_vars.items():
            # Skip if filter_prefix is specified and key doesn't match
            if filter_prefix and not key.startswith(filter_prefix):
                continue
            
            # Build final key name
            final_key = f"EVM:{key}" if add_evm_prefix else key
            
            # Convert value to string (os.environ requires string values)
            str_value = str(value)
            
            # Set in system environment
            os.environ[final_key] = str_value
            loaded_count += 1
        
        if loaded_count > 0:
            print(f"Loaded {loaded_count} environment variables to memory")
            if add_evm_prefix:
                print("Prefix 'EVM:' added to all variable names")
            if filter_prefix:
                print(f"Filter: keys starting with '{filter_prefix}'")
        else:
            print("No environment variables to load")
            if filter_prefix:
                print(f"No variables found with prefix '{filter_prefix}'")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='evm',
        description='Environment Variable Manager - Manage environment variables easily',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evm -v                           # Show detailed version information
  evm --verbose                    # Show detailed version information
  evm set API_KEY abc123           # Set an environment variable
  evm get API_KEY                  # Get an environment variable
  evm list                         # List all environment variables
  evm delete API_KEY               # Delete an environment variable
  evm export --format env          # Export to .env file
  evm load config.env              # Load from .env file (auto-detect)
  evm load config.json             # Load from JSON file (auto-detect)
  evm load backup.json --format backup  # Load backup file (force format)
  evm load config.json --replace   # Replace instead of merge
  evm load config.json --group prod  # Add to 'prod' group
  evm load config.json --nest      # Import nested JSON (groups from first-level keys)
  evm exec -- python script.py    # Execute command with env vars
  evm clear                        # Clear all environment variables
  evm list API                     # List variables matching API
  evm rename OLD_KEY NEW_KEY       # Rename a variable
  evm copy SRC_KEY DST_KEY         # Copy a variable
  evm search api                   # Search variables by key
  evm search api --value           # Search by key and value
  evm backup                       # Create backup with timestamp
  evm backup --file mybackup.json  # Create backup to specific file
  evm restore backup_20240101_120000.json  # Restore from backup
  evm restore backup.json --merge  # Merge backup with current

Group/Namespace Management:
  evm setg dev DATABASE_URL localhost  # Set variable in 'dev' group
  evm getg dev DATABASE_URL           # Get variable from 'dev' group
  evm listg dev                       # List all variables in 'dev' group
  evm listg dev --no-prefix           # List variables in 'dev' group (without group prefix)
  evm deleteg dev DATABASE_URL        # Delete variable from 'dev' group
  evm groups                          # List all groups
  evm delete-group dev                # Delete entire 'dev' group
  evm move-group API_KEY prod         # Move variable to 'prod' group
  evm list --group prod               # List variables in specific group
  evm list --show-groups              # Display variables grouped by namespace
        """
    )

    parser.add_argument('--version', action='version', version='%(prog)s 1.5.0')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show verbose version information')
    parser.add_argument('--env-file', help='Path to environment storage file (default: ~/.evm/env.json)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Set command
    set_parser = subparsers.add_parser('set', help='Set an environment variable')
    set_parser.add_argument('key', help='Variable name')
    set_parser.add_argument('value', help='Variable value')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get an environment variable')
    get_parser.add_argument('key', help='Variable name')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an environment variable')
    delete_parser.add_argument('key', help='Variable name')

    # List command
    list_parser = subparsers.add_parser('list', help='List all environment variables')
    list_parser.add_argument('pattern', nargs='?', help='Filter pattern')
    list_parser.add_argument('--group', '-g', help='List variables in a specific group')
    list_parser.add_argument('--show-groups', action='store_true',
                           help='Group output by namespace')
    list_parser.add_argument('--no-prefix', action='store_true',
                           help='Show only variable names without group prefix (when using --group)')

    # Clear command
    subparsers.add_parser('clear', help='Clear all environment variables')

    # Group management commands
    subparsers.add_parser('groups', help='List all groups')

    # Set variable in group
    setg_parser = subparsers.add_parser('setg', help='Set a variable in a specific group')
    setg_parser.add_argument('group', help='Group name')
    setg_parser.add_argument('key', help='Variable name')
    setg_parser.add_argument('value', help='Variable value')

    # Get variable from group
    getg_parser = subparsers.add_parser('getg', help='Get a variable from a specific group')
    getg_parser.add_argument('group', help='Group name')
    getg_parser.add_argument('key', help='Variable name')

    # Delete variable from group
    deleteg_parser = subparsers.add_parser('deleteg', help='Delete a variable from a specific group')
    deleteg_parser.add_argument('group', help='Group name')
    deleteg_parser.add_argument('key', help='Variable name')

    # List variables in group
    listg_parser = subparsers.add_parser('listg', help='List variables in a specific group')
    listg_parser.add_argument('group', help='Group name')

    # Delete entire group
    delete_group_parser = subparsers.add_parser('delete-group', help='Delete an entire group')
    delete_group_parser.add_argument('group', help='Group name')

    # Move variable to group
    move_group_parser = subparsers.add_parser('move-group', help='Move a variable to a different group')
    move_group_parser.add_argument('key', help='Variable name')
    move_group_parser.add_argument('group', help='Target group name')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export environment variables')
    export_parser.add_argument('--format', '-f', choices=['json', 'env', 'sh'],
                             default='json', help='Export format (default: json)')
    export_parser.add_argument('--output', '-o', help='Output file path')
    export_parser.add_argument('--group', '-g', help='Export variables from a specific group')

    # Load command
    load_parser = subparsers.add_parser('load', help='Load environment variables from file')
    load_parser.add_argument('file', help='Input file path')
    load_parser.add_argument('--format', '-f', choices=['json', 'env', 'backup'],
                           help='Force file format (default: auto-detect)')
    load_parser.add_argument('--replace', '-r', action='store_true',
                           help='Replace existing variables instead of merging')
    load_parser.add_argument('--group', '-g', help='Add imported variables to a specific group')
    load_parser.add_argument('--nest', '-n', action='store_true',
                           help='Treat first-level keys as group names (for nested JSON)')

    # Exec command
    exec_parser = subparsers.add_parser('exec', help='Execute command with environment variables')
    exec_parser.add_argument('exec_args', nargs='+', help='Command to execute')

    # Loadmemory command
    loadmem_parser = subparsers.add_parser('loadmemory', help='Load environment variables from file to system memory')
    loadmem_parser.add_argument('--prefix', '-p', help='Only load variables with keys starting with this prefix')
    loadmem_parser.add_argument('--no-prefix', action='store_true',
                               help='Do not add EVM: prefix to variable names')

    # Rename command
    rename_parser = subparsers.add_parser('rename', help='Rename an environment variable')
    rename_parser.add_argument('old_key', help='Current variable name')
    rename_parser.add_argument('new_key', help='New variable name')

    # Copy command
    copy_parser = subparsers.add_parser('copy', help='Copy an environment variable')
    copy_parser.add_argument('src_key', help='Source variable name')
    copy_parser.add_argument('dst_key', help='Destination variable name')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search environment variables')
    search_parser.add_argument('pattern', help='Search pattern')
    search_parser.add_argument('--value', '-v', action='store_true',
                              help='Search in values as well')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup environment variables')
    backup_parser.add_argument('--file', '-f',
                              help='Backup file path (default: ~/.evm/backup_<timestamp>.json)')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore environment variables from backup')
    restore_parser.add_argument('file', help='Backup file path')
    restore_parser.add_argument('--merge', '-m', action='store_true',
                               help='Merge with existing variables instead of replacing')

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle -v/--verbose flag for detailed version info
    if args.verbose:
        from evm import __version__
        print(f"EVM (Environment Variable Manager)")
        print(f"Version: {__version__}")
        print(f"Author: EVM Tool")
        print(f"License: MIT")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Storage: {Path.home() / '.evm' / 'env.json'}")
        print(f"\nRepository: https://github.com/zxygithub/evm")
        print(f"Documentation: https://github.com/zxygithub/evm/blob/main/README.md")
        return

    if not args.command:
        parser.print_help()
        return

    try:
        # Initialize environment manager
        env_manager = EnvironmentManager(args.env_file)

        # Execute command
        if args.command == 'set':
            env_manager.set(args.key, args.value)
        elif args.command == 'get':
            env_manager.get(args.key)
        elif args.command == 'delete':
            env_manager.delete(args.key)
        elif args.command == 'list':
            no_prefix = getattr(args, 'no_prefix', False)
            env_manager.list(args.pattern, args.group, args.show_groups, no_prefix)
        elif args.command == 'clear':
            env_manager.clear()
        elif args.command == 'export':
            env_manager.export(args.format, args.output, args.group)
        elif args.command == 'load':
            # Handle load command with optional parameters
            format_type = getattr(args, 'format', None)
            replace = getattr(args, 'replace', False)
            group = getattr(args, 'group', None)
            nest = getattr(args, 'nest', False)
            env_manager.load(args.file, format_type, replace, group, nest)
        elif args.command == 'exec':
            env_manager.execute(args.exec_args)
        elif args.command == 'loadmemory':
            filter_prefix = getattr(args, 'prefix', None)
            add_evm_prefix = not getattr(args, 'no_prefix', False)
            env_manager.load_to_memory(filter_prefix, add_evm_prefix)
        elif args.command == 'rename':
            env_manager.rename(args.old_key, args.new_key)
        elif args.command == 'copy':
            env_manager.copy(args.src_key, args.dst_key)
        elif args.command == 'search':
            env_manager.search(args.pattern, args.value)
        elif args.command == 'backup':
            env_manager.backup(args.file)
        elif args.command == 'restore':
            env_manager.restore(args.file, args.merge)
        elif args.command == 'groups':
            env_manager.list_groups()
        elif args.command == 'setg':
            env_manager.set_grouped(args.group, args.key, args.value)
        elif args.command == 'getg':
            env_manager.get_grouped(args.group, args.key)
        elif args.command == 'deleteg':
            env_manager.delete_grouped(args.group, args.key)
        elif args.command == 'listg':
            no_prefix = getattr(args, 'no_prefix', False)
            env_manager.list(group=args.group, no_prefix=no_prefix)
        elif args.command == 'delete-group':
            env_manager.delete_group(args.group)
        elif args.command == 'move-group':
            env_manager.move_to_group(args.key, args.group)
        else:
            parser.print_help()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
