#!/usr/bin/env python3
"""
EVM 命令行接口

负责 argparse 解析、命令调度和输出格式化。
所有 print/sys.exit 逻辑集中在此模块。
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .exceptions import EVMError, GroupNotFoundError
from .formatters import (
    print_diff,
    print_groups,
    print_info,
    print_load_memory_result,
    print_search_results,
    print_vars_by_group,
    print_vars_table,
)
from .manager import EnvironmentManager


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='evm',
        description='Environment Variable Manager - Manage environment variables easily',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evm set API_KEY abc123           # Set an environment variable
  evm set --secret DB_PASS mypass  # Set an encrypted secret variable
  evm get API_KEY                  # Get a variable
  evm get --secret DB_PASS         # Get and decrypt a secret
  evm list                         # List all variables
  evm list --show-groups           # List variables grouped by namespace
  evm delete API_KEY               # Delete a variable
  evm export --format env          # Export to .env file
  evm load config.json             # Load from JSON file (auto-detect)
  evm load config.json --nest      # Import nested JSON (groups from first-level keys)
  evm exec -- python script.py    # Execute command with env vars
  evm edit API_KEY                 # Edit variable in $EDITOR
  evm info                         # Show tool and storage info
  evm diff backup.json             # Compare current state with backup
  evm expand URL                   # Expand template references in variable value

Group Management:
  evm setg dev DATABASE_URL localhost  # Set variable in 'dev' group
  evm getg dev DATABASE_URL           # Get variable from 'dev' group
  evm listg dev                       # List variables in 'dev' group
  evm deleteg dev DATABASE_URL        # Delete variable from 'dev' group
  evm groups                          # List all groups
  evm delete-group dev                # Delete entire group
  evm move-group API_KEY prod         # Move variable to 'prod' group

Options:
  --dry-run  Preview changes without writing (supported by: set, delete, clear,
             rename, copy, export, load, setg, deleteg, delete-group, move-group,
             set --secret)
        """,
    )

    parser.add_argument(
        '--version', action='version', version='%(prog)s 1.7.0'
    )
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='Show detailed version information',
    )
    parser.add_argument(
        '--env-file',
        help='Path to environment storage file (default: ~/.evm/env.json)',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview changes without writing to storage',
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ── 基本命令 ──────────────────────────────────────────

    set_parser = subparsers.add_parser('set', help='Set an environment variable')
    set_parser.add_argument('key', help='Variable name')
    set_parser.add_argument('value', help='Variable value')
    set_parser.add_argument(
        '--secret', '-s', action='store_true',
        help='Encrypt the value before storing',
    )

    get_parser = subparsers.add_parser('get', help='Get an environment variable')
    get_parser.add_argument('key', help='Variable name')
    get_parser.add_argument(
        '--secret', '-s', action='store_true',
        help='Decrypt the value before displaying',
    )

    delete_parser = subparsers.add_parser(
        'delete', help='Delete an environment variable'
    )
    delete_parser.add_argument('key', help='Variable name')

    list_parser = subparsers.add_parser(
        'list', help='List all environment variables'
    )
    list_parser.add_argument('pattern', nargs='?', help='Filter pattern')
    list_parser.add_argument(
        '--group', '-g', help='List variables in a specific group'
    )
    list_parser.add_argument(
        '--show-groups', action='store_true',
        help='Group output by namespace',
    )
    list_parser.add_argument(
        '--no-prefix', action='store_true',
        help='Show only variable names without group prefix',
    )

    subparsers.add_parser('clear', help='Clear all environment variables')

    # ── 分组命令 ──────────────────────────────────────────

    subparsers.add_parser('groups', help='List all groups')

    setg_parser = subparsers.add_parser(
        'setg', help='Set a variable in a specific group'
    )
    setg_parser.add_argument('group', help='Group name')
    setg_parser.add_argument('key', help='Variable name')
    setg_parser.add_argument('value', help='Variable value')

    getg_parser = subparsers.add_parser(
        'getg', help='Get a variable from a specific group'
    )
    getg_parser.add_argument('group', help='Group name')
    getg_parser.add_argument('key', help='Variable name')

    deleteg_parser = subparsers.add_parser(
        'deleteg', help='Delete a variable from a specific group'
    )
    deleteg_parser.add_argument('group', help='Group name')
    deleteg_parser.add_argument('key', help='Variable name')

    listg_parser = subparsers.add_parser(
        'listg', help='List variables in a specific group'
    )
    listg_parser.add_argument('group', help='Group name')
    listg_parser.add_argument(
        '--no-prefix', action='store_true',
        help='Show only variable names without group prefix',
    )

    delete_group_parser = subparsers.add_parser(
        'delete-group', help='Delete an entire group'
    )
    delete_group_parser.add_argument('group', help='Group name')

    move_group_parser = subparsers.add_parser(
        'move-group', help='Move a variable to a different group'
    )
    move_group_parser.add_argument('key', help='Variable name')
    move_group_parser.add_argument('group', help='Target group name')

    # ── 导入导出 ──────────────────────────────────────────

    export_parser = subparsers.add_parser(
        'export', help='Export environment variables'
    )
    export_parser.add_argument(
        '--format', '-f', choices=['json', 'env', 'sh'],
        default='json', help='Export format (default: json)',
    )
    export_parser.add_argument('--output', '-o', help='Output file path')
    export_parser.add_argument(
        '--group', '-g', help='Export variables from a specific group'
    )

    load_parser = subparsers.add_parser(
        'load', help='Load environment variables from file'
    )
    load_parser.add_argument('file', help='Input file path')
    load_parser.add_argument(
        '--format', '-f', choices=['json', 'env', 'backup'],
        help='Force file format (default: auto-detect)',
    )
    load_parser.add_argument(
        '--replace', '-r', action='store_true',
        help='Replace existing variables instead of merging',
    )
    load_parser.add_argument(
        '--group', '-g', help='Add imported variables to a specific group'
    )
    load_parser.add_argument(
        '--nest', '-n', action='store_true',
        help='Treat first-level keys as group names (for nested JSON)',
    )

    # ── 备份恢复 ──────────────────────────────────────────

    backup_parser = subparsers.add_parser(
        'backup', help='Backup environment variables'
    )
    backup_parser.add_argument(
        '--file', '-f',
        help='Backup file path (default: ~/.evm/backup_<timestamp>.json)',
    )

    restore_parser = subparsers.add_parser(
        'restore', help='Restore environment variables from backup'
    )
    restore_parser.add_argument('file', help='Backup file path')
    restore_parser.add_argument(
        '--merge', '-m', action='store_true',
        help='Merge with existing variables instead of replacing',
    )

    # ── 搜索 ──────────────────────────────────────────────

    search_parser = subparsers.add_parser(
        'search', help='Search environment variables'
    )
    search_parser.add_argument('pattern', help='Search pattern')
    search_parser.add_argument(
        '--value', '-v', action='store_true', help='Search in values as well'
    )

    # ── 其他命令 ──────────────────────────────────────────

    rename_parser = subparsers.add_parser(
        'rename', help='Rename an environment variable'
    )
    rename_parser.add_argument('old_key', help='Current variable name')
    rename_parser.add_argument('new_key', help='New variable name')

    copy_parser = subparsers.add_parser(
        'copy', help='Copy an environment variable'
    )
    copy_parser.add_argument('src_key', help='Source variable name')
    copy_parser.add_argument('dst_key', help='Destination variable name')

    exec_parser = subparsers.add_parser(
        'exec', help='Execute command with environment variables'
    )
    exec_parser.add_argument('exec_args', nargs='+', help='Command to execute')

    loadmem_parser = subparsers.add_parser(
        'loadmemory',
        help='Load environment variables from file to system memory',
    )
    loadmem_parser.add_argument(
        '--prefix', '-p',
        help='Only load variables with keys starting with this prefix',
    )
    loadmem_parser.add_argument(
        '--no-prefix', action='store_true',
        help='Do not add EVM: prefix to variable names',
    )

    # ── P2 新功能 ─────────────────────────────────────────

    edit_parser = subparsers.add_parser(
        'edit', help='Edit a variable value in $EDITOR'
    )
    edit_parser.add_argument('key', help='Variable name to edit')

    subparsers.add_parser('info', help='Show tool and storage information')

    diff_parser = subparsers.add_parser(
        'diff', help='Compare current state with a backup file'
    )
    diff_parser.add_argument('file', help='Backup file to compare with')

    expand_parser = subparsers.add_parser(
        'expand', help='Expand template references in a variable value'
    )
    expand_parser.add_argument('key', help='Variable name to expand')

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """主入口

    Args:
        argv: 命令行参数（None 时使用 sys.argv）

    Returns:
        退出码（0=成功，1=错误）
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # --verbose: 显示详细信息
    if args.verbose:
        mgr = EnvironmentManager(args.env_file)
        print_info(mgr.info())
        return 0

    if not args.command:
        parser.print_help()
        return 0

    dry_run = getattr(args, 'dry_run', False)

    try:
        mgr = EnvironmentManager(args.env_file)
        _dispatch(mgr, args, dry_run)
        return 0
    except GroupNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except EVMError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def _dispatch(mgr: EnvironmentManager, args, dry_run: bool) -> None:
    """命令调度"""
    cmd = args.command

    # ── 基本命令 ──────────────────────────────────────────

    if cmd == 'set':
        if getattr(args, 'secret', False):
            print(mgr.set_secret(args.key, args.value, dry_run=dry_run))
        else:
            print(mgr.set(args.key, args.value, dry_run=dry_run))

    elif cmd == 'get':
        if getattr(args, 'secret', False):
            print(mgr.get_secret(args.key))
        else:
            print(mgr.get(args.key))

    elif cmd == 'delete':
        print(mgr.delete(args.key, dry_run=dry_run))

    elif cmd == 'list':
        no_prefix = getattr(args, 'no_prefix', False)
        if getattr(args, 'show_groups', False):
            # show_groups 需要获取所有变量然后按组展示
            if args.group:
                filtered = mgr.list_vars(group=args.group)
            elif args.pattern:
                filtered = mgr.list_vars(pattern=args.pattern)
            else:
                filtered = mgr.list_vars()
            print_vars_by_group(filtered)
        else:
            result = mgr.list_vars(
                pattern=args.pattern,
                group=args.group,
                no_prefix=no_prefix,
            )
            print_vars_table(result)

    elif cmd == 'clear':
        print(mgr.clear(dry_run=dry_run))

    # ── 分组命令 ──────────────────────────────────────────

    elif cmd == 'groups':
        print_groups(mgr.list_groups())

    elif cmd == 'setg':
        print(mgr.set_grouped(args.group, args.key, args.value, dry_run=dry_run))

    elif cmd == 'getg':
        print(mgr.get_grouped(args.group, args.key))

    elif cmd == 'deleteg':
        print(mgr.delete_grouped(args.group, args.key, dry_run=dry_run))

    elif cmd == 'listg':
        no_prefix = getattr(args, 'no_prefix', False)
        result = mgr.list_vars(group=args.group, no_prefix=no_prefix)
        print_vars_table(result)

    elif cmd == 'delete-group':
        print(mgr.delete_group(args.group, dry_run=dry_run))

    elif cmd == 'move-group':
        print(mgr.move_to_group(args.key, args.group, dry_run=dry_run))

    # ── 导入导出 ──────────────────────────────────────────

    elif cmd == 'export':
        print(mgr.export(
            format_type=args.format,
            output_file=args.output,
            group=args.group,
            dry_run=dry_run,
        ))

    elif cmd == 'load':
        print(mgr.load(
            input_file=args.file,
            format_type=getattr(args, 'format', None),
            replace=getattr(args, 'replace', False),
            group=getattr(args, 'group', None),
            nest=getattr(args, 'nest', False),
            dry_run=dry_run,
        ))

    # ── 备份恢复 ──────────────────────────────────────────

    elif cmd == 'backup':
        print(mgr.backup(args.file))

    elif cmd == 'restore':
        print(mgr.restore(args.file, merge=getattr(args, 'merge', False)))

    # ── 搜索 ──────────────────────────────────────────────

    elif cmd == 'search':
        results = mgr.search(args.pattern, search_value=getattr(args, 'value', False))
        print_search_results(results, args.pattern, getattr(args, 'value', False))

    # ── 其他命令 ──────────────────────────────────────────

    elif cmd == 'rename':
        print(mgr.rename(args.old_key, args.new_key, dry_run=dry_run))

    elif cmd == 'copy':
        print(mgr.copy(args.src_key, args.dst_key, dry_run=dry_run))

    elif cmd == 'exec':
        mgr.execute(args.exec_args)

    elif cmd == 'loadmemory':
        filter_prefix = getattr(args, 'prefix', None)
        add_evm_prefix = not getattr(args, 'no_prefix', False)
        loaded_count, prefix_used, filter_used = mgr.load_to_memory(
            filter_prefix=filter_prefix,
            add_evm_prefix=add_evm_prefix,
        )
        print_load_memory_result(loaded_count, prefix_used, filter_used)

    # ── P2 新功能 ─────────────────────────────────────────

    elif cmd == 'edit':
        print(mgr.edit(args.key))

    elif cmd == 'info':
        print_info(mgr.info())

    elif cmd == 'diff':
        print_diff(mgr.diff(args.file))

    elif cmd == 'expand':
        expanded = mgr.expand(args.key)
        print(expanded)

    else:
        # 未知命令（不应到达此处）
        print(f"Unknown command: {cmd}", file=sys.stderr)
        raise SystemExit(1)


__all__ = ['create_parser', 'main']
