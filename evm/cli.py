#!/usr/bin/env python3
"""
EVM 命令行接口

负责 argparse 解析、命令调度和输出格式化。
所有 print/sys.exit 逻辑集中在此模块。
"""

import argparse
import sys
from typing import List, Optional

from ._completion import SHELL_GENERATORS
from .exceptions import EVMError, GroupNotFoundError, OperationCancelledError
from .formatters import (
    print_diff,
    print_groups,
    print_history,
    print_info,
    print_load_memory_result,
    print_schema,
    print_search_results,
    print_validate_all,
    print_validate_result,
    print_vars_by_group,
    print_vars_table,
)
from .manager import EnvironmentManager

# 所有顶级命令（用于补全生成）
ALL_COMMANDS = [
    'set', 'get', 'delete', 'list', 'clear',
    'groups', 'setg', 'getg', 'deleteg', 'listg', 'delete-group', 'move-group',
    'export', 'load',
    'backup', 'restore',
    'search', 'rename', 'copy',
    'exec', 'loadmemory',
    'edit', 'info', 'diff', 'expand',
    'validate', 'history', 'schema', 'completion',
]


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog='evm',
        description='Environment Variable Manager - Manage environment variables easily',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  evm set API_KEY abc123           # Set a variable
  evm set --secret DB_PASS mypass  # Set an encrypted secret
  evm get API_KEY                  # Get a variable
  evm get --secret DB_PASS         # Get and decrypt a secret
  evm list                         # List all variables
  evm list --show-groups           # List by namespace
  evm export --format env          # Export to .env
  evm load config.json --nest      # Import nested JSON
  evm edit API_KEY                 # Edit in $EDITOR
  evm info                         # Show tool info
  evm diff backup.json             # Compare with backup
  evm expand URL                   # Expand {{VAR}} templates
  evm validate API_URL             # Validate against schema
  evm history                      # Show operation log
  evm schema set API_URL --format url
  evm completion bash              # Generate shell completion

Group Management:
  evm setg dev DB_URL localhost
  evm getg dev DB_URL
  evm listg dev
  evm groups
  evm delete-group dev

Options:
  --dry-run  Preview changes (set, delete, clear, rename, copy, export,
             load, setg, deleteg, delete-group, move-group, set --secret)
  --force    Skip confirmation for destructive operations (clear, delete-group)
        """,
    )

    parser.add_argument('--version', action='version', version='%(prog)s 1.8.0')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed version information')
    parser.add_argument('--env-file',
                        help='Path to storage file (default: ~/.evm/env.json)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without writing')
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation for destructive operations')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # ── 基本命令 ──────────────────────────────────────────

    set_p = subparsers.add_parser('set', help='Set a variable')
    set_p.add_argument('key', help='Variable name')
    set_p.add_argument('value', help='Variable value')
    set_p.add_argument('--secret', '-s', action='store_true',
                       help='Encrypt the value')

    get_p = subparsers.add_parser('get', help='Get a variable')
    get_p.add_argument('key', help='Variable name')
    get_p.add_argument('--secret', '-s', action='store_true',
                       help='Decrypt the value')

    del_p = subparsers.add_parser('delete', help='Delete a variable')
    del_p.add_argument('key', help='Variable name')

    list_p = subparsers.add_parser('list', help='List all variables')
    list_p.add_argument('pattern', nargs='?', help='Filter pattern')
    list_p.add_argument('--group', '-g', help='Filter by group')
    list_p.add_argument('--show-groups', action='store_true',
                        help='Group output by namespace')
    list_p.add_argument('--no-prefix', action='store_true',
                        help='Remove group prefix from display')

    subparsers.add_parser('clear', help='Clear all variables')

    # ── 分组命令 ──────────────────────────────────────────

    subparsers.add_parser('groups', help='List all groups')

    setg_p = subparsers.add_parser('setg', help='Set a grouped variable')
    setg_p.add_argument('group')
    setg_p.add_argument('key')
    setg_p.add_argument('value')

    getg_p = subparsers.add_parser('getg', help='Get a grouped variable')
    getg_p.add_argument('group')
    getg_p.add_argument('key')

    delg_p = subparsers.add_parser('deleteg', help='Delete a grouped variable')
    delg_p.add_argument('group')
    delg_p.add_argument('key')

    listg_p = subparsers.add_parser('listg', help='List variables in a group')
    listg_p.add_argument('group')
    listg_p.add_argument('--no-prefix', action='store_true')

    dg_p = subparsers.add_parser('delete-group', help='Delete an entire group')
    dg_p.add_argument('group')

    mg_p = subparsers.add_parser('move-group', help='Move variable to group')
    mg_p.add_argument('key')
    mg_p.add_argument('group')

    # ── 导入导出 ──────────────────────────────────────────

    exp_p = subparsers.add_parser('export', help='Export variables')
    exp_p.add_argument('--format', '-f', choices=['json', 'env', 'sh'],
                       default='json')
    exp_p.add_argument('--output', '-o', help='Output file path')
    exp_p.add_argument('--group', '-g', help='Export from group')

    ld_p = subparsers.add_parser('load', help='Load from file')
    ld_p.add_argument('file', help='Input file')
    ld_p.add_argument('--format', '-f', choices=['json', 'env', 'backup'])
    ld_p.add_argument('--replace', '-r', action='store_true')
    ld_p.add_argument('--group', '-g')
    ld_p.add_argument('--nest', '-n', action='store_true')

    # ── 备份恢复 ──────────────────────────────────────────

    bk_p = subparsers.add_parser('backup', help='Backup variables')
    bk_p.add_argument('--file', '-f', help='Backup file path')

    rs_p = subparsers.add_parser('restore', help='Restore from backup')
    rs_p.add_argument('file')
    rs_p.add_argument('--merge', '-m', action='store_true')

    # ── 搜索/重命名/复制 ──────────────────────────────────

    sr_p = subparsers.add_parser('search', help='Search variables')
    sr_p.add_argument('pattern')
    sr_p.add_argument('--value', '-v', action='store_true')

    rn_p = subparsers.add_parser('rename', help='Rename a variable')
    rn_p.add_argument('old_key')
    rn_p.add_argument('new_key')

    cp_p = subparsers.add_parser('copy', help='Copy a variable')
    cp_p.add_argument('src_key')
    cp_p.add_argument('dst_key')

    # ── 执行/内存 ─────────────────────────────────────────

    ex_p = subparsers.add_parser('exec', help='Execute with env vars')
    ex_p.add_argument('exec_args', nargs='+')

    lm_p = subparsers.add_parser('loadmemory', help='Load to os.environ')
    lm_p.add_argument('--prefix', '-p')
    lm_p.add_argument('--no-prefix', action='store_true')

    # ── 编辑/信息/Diff/展开 ───────────────────────────────

    ed_p = subparsers.add_parser('edit', help='Edit value in $EDITOR')
    ed_p.add_argument('key')

    subparsers.add_parser('info', help='Show tool information')

    df_p = subparsers.add_parser('diff', help='Compare with backup')
    df_p.add_argument('file')

    xp_p = subparsers.add_parser('expand', help='Expand {{VAR}} templates')
    xp_p.add_argument('key')

    # ── P2 新功能 ─────────────────────────────────────────

    # validate
    vl_p = subparsers.add_parser('validate', help='Validate against schema')
    vl_p.add_argument('key', nargs='?', help='Variable (omit for all)')

    # history
    hi_p = subparsers.add_parser('history', help='Show operation history')
    hi_p.add_argument('--limit', '-n', type=int, default=20,
                      help='Number of entries to show')
    hi_p.add_argument('--clear', action='store_true',
                      help='Clear all history')

    # schema
    sc_p = subparsers.add_parser('schema', help='Manage variable schemas')
    sc_sub = sc_p.add_subparsers(dest='schema_command', help='Schema subcommand')

    sc_set = sc_sub.add_parser('set', help='Set schema for a variable')
    sc_set.add_argument('key')
    sc_set.add_argument('--format', '-f',
                        choices=['url', 'email', 'port', 'integer',
                                 'boolean', 'path', 'ipv4', 'ipv6'],
                        help='Built-in format')
    sc_set.add_argument('--required', '-r', action='store_true',
                        help='Mark as required')
    sc_set.add_argument('--pattern', '-p', help='Custom regex pattern')
    sc_set.add_argument('--description', '-d', help='Description')

    sc_get = sc_sub.add_parser('get', help='Get schema definition')
    sc_get.add_argument('key', nargs='?', help='Variable (omit for all)')

    sc_del = sc_sub.add_parser('delete', help='Remove schema definition')
    sc_del.add_argument('key')

    sc_list = sc_sub.add_parser('list', help='List all schema definitions')

    sc_val = sc_sub.add_parser('validate', help='Validate against schema')
    sc_val.add_argument('key', nargs='?', help='Variable (omit for all)')

    # completion
    co_p = subparsers.add_parser('completion', help='Generate shell completion')
    co_p.add_argument('shell', choices=['bash', 'zsh', 'fish'],
                      help='Shell type')

    return parser


def _confirm(message: str) -> bool:
    """交互式确认（非交互模式或 stdin 非终端时返回 False）"""
    if not sys.stdin.isatty():
        return False
    try:
        response = input(f"{message} [y/N] ").strip().lower()
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def main(argv: Optional[List[str]] = None) -> int:
    """主入口"""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        mgr = EnvironmentManager(args.env_file)
        print_info(mgr.info())
        return 0

    if not args.command:
        parser.print_help()
        return 0

    dry_run = getattr(args, 'dry_run', False)
    force = getattr(args, 'force', False)

    try:
        mgr = EnvironmentManager(args.env_file)
        _dispatch(mgr, args, dry_run, force)
        return 0
    except OperationCancelledError:
        print("Operation cancelled.", file=sys.stderr)
        return 1
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


def _dispatch(mgr: EnvironmentManager, args, dry_run: bool, force: bool) -> None:
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
        if not dry_run and not force:
            count = len(mgr._env_vars)
            if count > 0 and not _confirm(
                f"This will clear all {count} variables. Continue?"
            ):
                raise OperationCancelledError("clear")
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
        if not dry_run and not force:
            if not _confirm(
                f"This will delete group '{args.group}' and all its variables. Continue?"
            ):
                raise OperationCancelledError("delete-group")
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

    # ── 搜索/重命名/复制 ──────────────────────────────────

    elif cmd == 'search':
        results = mgr.search(args.pattern, search_value=getattr(args, 'value', False))
        print_search_results(results, args.pattern, getattr(args, 'value', False))

    elif cmd == 'rename':
        print(mgr.rename(args.old_key, args.new_key, dry_run=dry_run))

    elif cmd == 'copy':
        print(mgr.copy(args.src_key, args.dst_key, dry_run=dry_run))

    # ── 执行/内存 ─────────────────────────────────────────

    elif cmd == 'exec':
        mgr.execute(args.exec_args)

    elif cmd == 'loadmemory':
        filter_prefix = getattr(args, 'prefix', None)
        add_evm_prefix = not getattr(args, 'no_prefix', False)
        loaded, prefix_used, filter_used = mgr.load_to_memory(
            filter_prefix=filter_prefix,
            add_evm_prefix=add_evm_prefix,
        )
        print_load_memory_result(loaded, prefix_used, filter_used)

    # ── 编辑/信息/Diff/展开 ───────────────────────────────

    elif cmd == 'edit':
        print(mgr.edit(args.key))

    elif cmd == 'info':
        print_info(mgr.info())

    elif cmd == 'diff':
        print_diff(mgr.diff(args.file))

    elif cmd == 'expand':
        print(mgr.expand(args.key))

    # ── P2 新功能 ─────────────────────────────────────────

    elif cmd == 'validate':
        key = getattr(args, 'key', None)
        if key:
            result = mgr.validate(key)
            print_validate_result(key, result)
        else:
            results = mgr.validate_all()
            print_validate_all(results)

    elif cmd == 'history':
        if getattr(args, 'clear', False):
            print(mgr.clear_history())
        else:
            entries = mgr.get_history(limit=args.limit)
            print_history(entries)

    elif cmd == 'schema':
        _dispatch_schema(mgr, args)

    elif cmd == 'completion':
        generator = SHELL_GENERATORS.get(args.shell)
        if generator:
            script = generator(ALL_COMMANDS)
            print(script, end='')
        else:
            print(f"Unsupported shell: {args.shell}", file=sys.stderr)
            raise SystemExit(1)

    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        raise SystemExit(1)


def _dispatch_schema(mgr: EnvironmentManager, args) -> None:
    """Schema 子命令调度"""
    sc_cmd = getattr(args, 'schema_command', None)

    if sc_cmd == 'set':
        required = None
        if getattr(args, 'required', False):
            required = True
        msg = mgr.set_schema(
            args.key,
            format=getattr(args, 'format', None),
            required=required,
            pattern=getattr(args, 'pattern', None),
            description=getattr(args, 'description', None),
        )
        print(msg)

    elif sc_cmd == 'get':
        key = getattr(args, 'key', None)
        schema = mgr.get_schema(key)
        print_schema(schema)

    elif sc_cmd == 'delete':
        print(mgr.delete_schema(args.key))

    elif sc_cmd == 'list':
        schema = mgr.get_schema()
        print_schema(schema)

    elif sc_cmd == 'validate':
        key = getattr(args, 'key', None)
        if key:
            result = mgr.validate(key)
            print_validate_result(key, result)
        else:
            results = mgr.validate_all()
            print_validate_all(results)

    else:
        # 无子命令时显示 schema 列表
        schema = mgr.get_schema()
        print_schema(schema)


__all__ = ['create_parser', 'main', 'ALL_COMMANDS']
