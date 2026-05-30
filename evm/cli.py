#!/usr/bin/env python3
"""
EVM 命令行接口

负责 argparse 解析、命令调度和输出格式化。

输出模式:
  - 默认: 人类可读文本 (stdout)
  - --json: 结构化 JSON (stdout=数据, stderr=日志)
  - --quiet: 静默模式 (仅退出码)

退出码:
  0  — 成功
  1  — 通用错误 / 操作取消
  2  — 变量不存在 (KeyNotFoundError)
  3  — 存储错误 (StorageError / CorruptedStorageError / LockTimeoutError)
  4  — 输入格式错误 (ImportFailedError / ExportError)
  5  — 解密失败 (DecryptionError)
  6  — 校验失败 (ValidationError / SchemaError)
  7  — 分组错误 (GroupNotFoundError / GroupOperationError)
  8  — 备份错误 (BackupError)
  9  — 编辑器错误 (EditorError)
  10 — 命令未找到 (CommandNotFoundError)
"""

import argparse
import sys
from typing import Optional

from ._completion import SHELL_GENERATORS
from ._json import json_error, json_output
from .exceptions import (
    BackupError,
    CommandNotFoundError,
    CorruptedStorageError,
    DecryptionError,
    EditorError,
    EVMError,
    ExportError,
    GroupNotFoundError,
    GroupOperationError,
    ImportFailedError,
    KeyAlreadyExistsError,
    KeyNotFoundError,
    LockTimeoutError,
    OperationCancelledError,
    SchemaError,
    StorageError,
    ValidationError,
)
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

# 异常类型 → 退出码映射
EXIT_CODE_MAP = {
    KeyNotFoundError: 2,
    KeyAlreadyExistsError: 2,
    StorageError: 3,
    CorruptedStorageError: 3,
    LockTimeoutError: 3,
    ImportFailedError: 4,
    ExportError: 4,
    DecryptionError: 5,
    ValidationError: 6,
    SchemaError: 6,
    GroupNotFoundError: 7,
    GroupOperationError: 7,
    BackupError: 8,
    EditorError: 9,
    CommandNotFoundError: 10,
    OperationCancelledError: 1,
}

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


def _exit_code_for(exc: EVMError) -> int:
    """根据异常类型返回退出码"""
    for exc_type, code in EXIT_CODE_MAP.items():
        if isinstance(exc, exc_type):
            return code
    return 1


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
  evm get API_KEY --json           # Get as JSON: {"status":"ok","data":{"key":"API_KEY","value":"..."}}
  evm list --json                  # List all as JSON
  evm list --show-groups           # List by namespace
  evm export --format env          # Export to .env
  evm load config.json --nest      # Import nested JSON
  evm edit API_KEY                 # Edit in $EDITOR
  evm info --json                  # Tool info as JSON
  evm diff backup.json             # Compare with backup
  evm expand URL                   # Expand {{VAR}} templates
  evm validate API_URL             # Validate against schema
  evm history --json               # History as JSON
  evm schema set API_URL --format url
  evm completion bash              # Generate shell completion

Agent-friendly usage:
  evm get KEY --json               # stdout = JSON, stderr = errors
  evm list --json --quiet          # stdout = JSON only, no decoration
  evm --json info                  # All commands support --json

Group Management:
  evm setg dev DB_URL localhost
  evm getg dev DB_URL
  evm listg dev
  evm groups
  evm delete-group dev

Options:
  --json     Output structured JSON to stdout (agent-friendly)
  --quiet    Suppress all human-readable output
  --dry-run  Preview changes (set, delete, clear, rename, copy, export,
             load, setg, deleteg, delete-group, move-group, set --secret)
  --force    Skip confirmation for destructive operations (clear, delete-group)

Exit Codes:
  0  Success
  1  General error / cancelled
  2  Variable not found
  3  Storage error
  4  Import/export format error
  5  Decryption error
  6  Validation/schema error
  7  Group error
  8  Backup error
  9  Editor error
  10 Command not found
        """,
    )

    parser.add_argument('--version', action='version', version='%(prog)s 2.2.0')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Show detailed version information')
    parser.add_argument('--env-file',
                        help='Path to storage file (default: ~/.evm/env.json)')
    parser.add_argument('--json', dest='json_mode', action='store_true',
                        help='Output structured JSON (agent-friendly)')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress human-readable output')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without writing')
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation for destructive operations')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    def _sp(name, **kwargs):
        """Create a subparser with global args (--json/--quiet/--dry-run/--force).

        Uses default=argparse.SUPPRESS so subparser defaults don't overwrite
        values set on the parent parser (e.g. `evm --json get KEY`).
        """
        p = subparsers.add_parser(name, **kwargs)
        p.add_argument('--json', dest='json_mode', action='store_true',
                       default=argparse.SUPPRESS,
                       help='Output structured JSON (agent-friendly)')
        p.add_argument('--quiet', '-q', action='store_true',
                       default=argparse.SUPPRESS,
                       help='Suppress human-readable output')
        p.add_argument('--dry-run', action='store_true',
                       default=argparse.SUPPRESS,
                       help='Preview changes without writing')
        p.add_argument('--force', action='store_true',
                       default=argparse.SUPPRESS,
                       help='Skip confirmation for destructive operations')
        return p

    # ── 基本命令 ──────────────────────────────────────────

    set_p = _sp('set', help='Set a variable')
    set_p.add_argument('key', help='Variable name')
    set_p.add_argument('value', help='Variable value')
    set_p.add_argument('--secret', '-s', action='store_true',
                       help='Encrypt the value')

    get_p = _sp('get', help='Get a variable')
    get_p.add_argument('key', help='Variable name')
    get_p.add_argument('--secret', '-s', action='store_true',
                       help='Decrypt the value')

    del_p = _sp('delete', help='Delete a variable')
    del_p.add_argument('key', help='Variable name')

    list_p = _sp('list', help='List all variables')
    list_p.add_argument('pattern', nargs='?', help='Filter pattern')
    list_p.add_argument('--group', '-g', help='Filter by group')
    list_p.add_argument('--show-groups', action='store_true',
                        help='Group output by namespace')
    list_p.add_argument('--no-prefix', action='store_true',
                        help='Remove group prefix from display')

    _sp('clear', help='Clear all variables')

    # ── 分组命令 ──────────────────────────────────────────

    _sp('groups', help='List all groups')

    setg_p = _sp('setg', help='Set a grouped variable')
    setg_p.add_argument('group')
    setg_p.add_argument('key')
    setg_p.add_argument('value')

    getg_p = _sp('getg', help='Get a grouped variable')
    getg_p.add_argument('group')
    getg_p.add_argument('key')

    delg_p = _sp('deleteg', help='Delete a grouped variable')
    delg_p.add_argument('group')
    delg_p.add_argument('key')

    listg_p = _sp('listg', help='List variables in a group')
    listg_p.add_argument('group')
    listg_p.add_argument('--no-prefix', action='store_true')

    dg_p = _sp('delete-group', help='Delete an entire group')
    dg_p.add_argument('group')

    mg_p = _sp('move-group', help='Move variable to group')
    mg_p.add_argument('key')
    mg_p.add_argument('group')

    # ── 导入导出 ──────────────────────────────────────────

    exp_p = _sp('export', help='Export variables')
    exp_p.add_argument('--format', '-f', choices=['json', 'env', 'sh'],
                       default='json')
    exp_p.add_argument('--output', '-o', help='Output file path')
    exp_p.add_argument('--group', '-g', help='Export from group')

    ld_p = _sp('load', help='Load from file')
    ld_p.add_argument('file', help='Input file')
    ld_p.add_argument('--format', '-f', choices=['json', 'env', 'backup'])
    ld_p.add_argument('--replace', '-r', action='store_true')
    ld_p.add_argument('--group', '-g')
    ld_p.add_argument('--nest', '-n', action='store_true')

    # ── 备份恢复 ──────────────────────────────────────────

    bk_p = _sp('backup', help='Backup variables')
    bk_p.add_argument('--file', '-f', help='Backup file path')

    rs_p = _sp('restore', help='Restore from backup')
    rs_p.add_argument('file')
    rs_p.add_argument('--merge', '-m', action='store_true')

    # ── 搜索/重命名/复制 ──────────────────────────────────

    sr_p = _sp('search', help='Search variables')
    sr_p.add_argument('pattern')
    sr_p.add_argument('--value', '-v', action='store_true')

    rn_p = _sp('rename', help='Rename a variable')
    rn_p.add_argument('old_key')
    rn_p.add_argument('new_key')

    cp_p = _sp('copy', help='Copy a variable')
    cp_p.add_argument('src_key')
    cp_p.add_argument('dst_key')

    # ── 执行/内存 ─────────────────────────────────────────

    ex_p = _sp('exec', help='Execute with env vars')
    ex_p.add_argument('exec_args', nargs='+')

    lm_p = _sp('loadmemory', help='Load to os.environ')
    lm_p.add_argument('--prefix', '-p')
    lm_p.add_argument('--no-prefix', action='store_true')

    # ── 编辑/信息/Diff/展开 ───────────────────────────────

    ed_p = _sp('edit', help='Edit value in $EDITOR')
    ed_p.add_argument('key')

    _sp('info', help='Show tool information')

    df_p = _sp('diff', help='Compare with backup')
    df_p.add_argument('file')

    xp_p = _sp('expand', help='Expand {{VAR}} templates')
    xp_p.add_argument('key')

    # ── P2 新功能 ─────────────────────────────────────────

    # validate
    vl_p = _sp('validate', help='Validate against schema')
    vl_p.add_argument('key', nargs='?', help='Variable (omit for all)')

    # history
    hi_p = _sp('history', help='Show operation history')
    hi_p.add_argument('--limit', '-n', type=int, default=20,
                      help='Number of entries to show')
    hi_p.add_argument('--clear', action='store_true',
                      help='Clear all history')

    # schema
    sc_p = _sp('schema', help='Manage variable schemas')
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

    sc_sub.add_parser('list', help='List all schema definitions')

    sc_val = sc_sub.add_parser('validate', help='Validate against schema')
    sc_val.add_argument('key', nargs='?', help='Variable (omit for all)')

    # completion
    co_p = _sp('completion', help='Generate shell completion')
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


def main(argv: Optional[list[str]] = None) -> int:
    """主入口

    Returns:
        退出码 (0=成功, 1-10=按异常类型细分)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    json_mode = getattr(args, 'json_mode', False)
    quiet = getattr(args, 'quiet', False)

    if args.verbose:
        mgr = EnvironmentManager(args.env_file)
        info = mgr.info()
        if json_mode:
            json_output(info, quiet)
        else:
            print_info(info)
        return 0

    if not args.command:
        parser.print_help()
        return 0

    dry_run = getattr(args, 'dry_run', False)
    force = getattr(args, 'force', False)

    try:
        mgr = EnvironmentManager(args.env_file)
        return _dispatch(mgr, args, dry_run, force, json_mode, quiet)
    except OperationCancelledError:
        if json_mode:
            json_error("Operation cancelled.", 1, quiet)
        else:
            print("Operation cancelled.", file=sys.stderr)
        return 1
    except EVMError as e:
        code = _exit_code_for(e)
        if json_mode:
            json_error(str(e), code, quiet)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return code
    except KeyboardInterrupt:
        if not quiet:
            print("\nOperation cancelled", file=sys.stderr)
        return 1
    except Exception as e:
        if json_mode:
            json_error(f"Unexpected error: {e}", 1, quiet)
        else:
            print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


# ── 命令处理器函数 ──────────────────────────────────────────

def _cmd_set(mgr, args, dry_run, force, json_mode, quiet):
    """处理 set 命令"""
    if getattr(args, 'secret', False):
        msg = mgr.set_secret(args.key, args.value, dry_run=dry_run)
        if json_mode:
            json_output({
                "key": args.key, "encrypted": True, "message": msg,
            }, quiet)
        elif not quiet:
            print(msg)
    else:
        msg = mgr.set(args.key, args.value, dry_run=dry_run)
        if json_mode:
            json_output({
                "key": args.key, "value": args.value, "message": msg,
            }, quiet)
        elif not quiet:
            print(msg)
    return 0


def _cmd_get(mgr, args, dry_run, force, json_mode, quiet):
    """处理 get 命令"""
    is_secret = getattr(args, 'secret', False)
    if is_secret:
        value = mgr.get_secret(args.key)
    else:
        value = mgr.get(args.key)
    if json_mode:
        json_output({"key": args.key, "value": value}, quiet)
    elif not quiet:
        if is_secret and sys.stdout.isatty():
            print(
                "[WARNING] Decrypted secret displayed on terminal "
                "(visible in scrollback).",
                file=sys.stderr,
            )
        print(value)
    return 0


def _cmd_delete(mgr, args, dry_run, force, json_mode, quiet):
    """处理 delete 命令"""
    msg = mgr.delete(args.key, dry_run=dry_run)
    if json_mode:
        json_output({"key": args.key, "deleted": True, "message": msg}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_list(mgr, args, dry_run, force, json_mode, quiet):
    """处理 list 命令"""
    no_prefix = getattr(args, 'no_prefix', False)
    if getattr(args, 'show_groups', False):
        if args.group:
            filtered = mgr.list_vars(group=args.group)
        elif args.pattern:
            filtered = mgr.list_vars(pattern=args.pattern)
        else:
            filtered = mgr.list_vars()
        if json_mode:
            json_output(filtered, quiet)
        elif not quiet:
            print_vars_by_group(filtered)
    else:
        result = mgr.list_vars(
            pattern=args.pattern,
            group=args.group,
            no_prefix=no_prefix,
        )
        if json_mode:
            json_output(result, quiet)
        elif not quiet:
            print_vars_table(result)
    return 0


def _cmd_clear(mgr, args, dry_run, force, json_mode, quiet):
    """处理 clear 命令"""
    if not dry_run and not force:
        count = len(mgr._env_vars)
        if count > 0 and not _confirm(
            f"This will clear all {count} variables. Continue?"
        ):
            raise OperationCancelledError("clear")
    count = len(mgr._env_vars)
    msg = mgr.clear(dry_run=dry_run)
    if json_mode:
        json_output({"cleared": count, "message": msg}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_groups(mgr, args, dry_run, force, json_mode, quiet):
    """处理 groups 命令"""
    groups = mgr.list_groups()
    if json_mode:
        json_output({"groups": groups}, quiet)
    elif not quiet:
        print_groups(groups)
    return 0


def _cmd_setg(mgr, args, dry_run, force, json_mode, quiet):
    """处理 setg 命令"""
    msg = mgr.set_grouped(args.group, args.key, args.value, dry_run=dry_run)
    if json_mode:
        json_output({
            "group": args.group, "key": args.key,
            "value": args.value, "message": msg,
        }, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_getg(mgr, args, dry_run, force, json_mode, quiet):
    """处理 getg 命令"""
    value = mgr.get_grouped(args.group, args.key)
    if json_mode:
        json_output({
            "group": args.group, "key": args.key, "value": value,
        }, quiet)
    elif not quiet:
        print(value)
    return 0


def _cmd_deleteg(mgr, args, dry_run, force, json_mode, quiet):
    """处理 deleteg 命令"""
    msg = mgr.delete_grouped(args.group, args.key, dry_run=dry_run)
    if json_mode:
        json_output({
            "group": args.group, "key": args.key,
            "deleted": True, "message": msg,
        }, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_listg(mgr, args, dry_run, force, json_mode, quiet):
    """处理 listg 命令"""
    no_prefix = getattr(args, 'no_prefix', False)
    result = mgr.list_vars(group=args.group, no_prefix=no_prefix)
    if json_mode:
        json_output(result, quiet)
    elif not quiet:
        print_vars_table(result)
    return 0


def _cmd_delete_group(mgr, args, dry_run, force, json_mode, quiet):
    """处理 delete-group 命令"""
    if not dry_run and not force:
        if not _confirm(
            f"This will delete group '{args.group}' and all its variables. Continue?"
        ):
            raise OperationCancelledError("delete-group")
    msg = mgr.delete_group(args.group, dry_run=dry_run)
    if json_mode:
        json_output({
            "group": args.group, "deleted": True, "message": msg,
        }, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_move_group(mgr, args, dry_run, force, json_mode, quiet):
    """处理 move-group 命令"""
    msg = mgr.move_to_group(args.key, args.group, dry_run=dry_run)
    if json_mode:
        json_output({
            "key": args.key, "target_group": args.group, "message": msg,
        }, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_export(mgr, args, dry_run, force, json_mode, quiet):
    """处理 export 命令"""
    msg = mgr.export(
        format_type=args.format,
        output_file=args.output,
        group=args.group,
        dry_run=dry_run,
    )
    if json_mode:
        json_output({"message": msg, "format": args.format}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_load(mgr, args, dry_run, force, json_mode, quiet):
    """处理 load 命令"""
    msg = mgr.load(
        input_file=args.file,
        format_type=getattr(args, 'format', None),
        replace=getattr(args, 'replace', False),
        group=getattr(args, 'group', None),
        nest=getattr(args, 'nest', False),
        dry_run=dry_run,
    )
    if json_mode:
        json_output({"message": msg, "file": args.file}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_backup(mgr, args, dry_run, force, json_mode, quiet):
    """处理 backup 命令"""
    msg = mgr.backup(args.file)
    if json_mode:
        json_output({"message": msg}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_restore(mgr, args, dry_run, force, json_mode, quiet):
    """处理 restore 命令"""
    msg = mgr.restore(args.file, merge=getattr(args, 'merge', False))
    if json_mode:
        json_output({"message": msg, "file": args.file}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_search(mgr, args, dry_run, force, json_mode, quiet):
    """处理 search 命令"""
    results = mgr.search(
        args.pattern, search_value=getattr(args, 'value', False)
    )
    if json_mode:
        json_output(results, quiet)
    elif not quiet:
        print_search_results(
            results, args.pattern, getattr(args, 'value', False)
        )
    return 0


def _cmd_rename(mgr, args, dry_run, force, json_mode, quiet):
    """处理 rename 命令"""
    msg = mgr.rename(args.old_key, args.new_key, dry_run=dry_run)
    if json_mode:
        json_output({
            "old_key": args.old_key, "new_key": args.new_key,
            "message": msg,
        }, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_copy(mgr, args, dry_run, force, json_mode, quiet):
    """处理 copy 命令"""
    msg = mgr.copy(args.src_key, args.dst_key, dry_run=dry_run)
    if json_mode:
        json_output({
            "src_key": args.src_key, "dst_key": args.dst_key,
            "message": msg,
        }, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_exec(mgr, args, dry_run, force, json_mode, quiet):
    """处理 exec 命令 - 返回子进程退出码"""
    return mgr.execute(args.exec_args)


def _cmd_loadmemory(mgr, args, dry_run, force, json_mode, quiet):
    """处理 loadmemory 命令"""
    filter_prefix = getattr(args, 'prefix', None)
    add_evm_prefix = not getattr(args, 'no_prefix', False)
    loaded, prefix_used, filter_used = mgr.load_to_memory(
        filter_prefix=filter_prefix,
        add_evm_prefix=add_evm_prefix,
    )
    if json_mode:
        json_output({
            "loaded": loaded,
            "evm_prefix": prefix_used,
            "filter_prefix": filter_used,
        }, quiet)
    elif not quiet:
        print_load_memory_result(loaded, prefix_used, filter_used)
    return 0


def _cmd_edit(mgr, args, dry_run, force, json_mode, quiet):
    """处理 edit 命令"""
    msg = mgr.edit(args.key)
    changed = "Updated" in msg
    if json_mode:
        json_output({"key": args.key, "changed": changed, "message": msg}, quiet)
    elif not quiet:
        print(msg)
    return 0


def _cmd_info(mgr, args, dry_run, force, json_mode, quiet):
    """处理 info 命令"""
    info = mgr.info()
    if json_mode:
        json_output(info, quiet)
    elif not quiet:
        print_info(info)
    return 0


def _cmd_diff(mgr, args, dry_run, force, json_mode, quiet):
    """处理 diff 命令"""
    result = mgr.diff(args.file)
    if json_mode:
        json_output(result, quiet)
    elif not quiet:
        print_diff(result)
    return 0


def _cmd_expand(mgr, args, dry_run, force, json_mode, quiet):
    """处理 expand 命令"""
    expanded = mgr.expand(args.key)
    if json_mode:
        json_output({"key": args.key, "expanded": expanded}, quiet)
    elif not quiet:
        print(expanded)
    return 0


def _cmd_validate(mgr, args, dry_run, force, json_mode, quiet):
    """处理 validate 命令"""
    key = getattr(args, 'key', None)
    if key:
        result = mgr.validate(key)
        if json_mode:
            json_output({"key": key, **result}, quiet)
        elif not quiet:
            print_validate_result(key, result)
    else:
        results = mgr.validate_all()
        if json_mode:
            json_output(results, quiet)
        elif not quiet:
            print_validate_all(results)
    return 0


def _cmd_history(mgr, args, dry_run, force, json_mode, quiet):
    """处理 history 命令"""
    if getattr(args, 'clear', False):
        msg = mgr.clear_history()
        if json_mode:
            json_output({"message": msg}, quiet)
        elif not quiet:
            print(msg)
    else:
        entries = mgr.get_history(limit=args.limit)
        if json_mode:
            json_output(entries, quiet)
        elif not quiet:
            print_history(entries)
    return 0


def _cmd_schema(mgr, args, dry_run, force, json_mode, quiet):
    """处理 schema 命令"""
    return _dispatch_schema(mgr, args, json_mode, quiet)


def _cmd_completion(mgr, args, dry_run, force, json_mode, quiet):
    """处理 completion 命令"""
    generator = SHELL_GENERATORS.get(args.shell)
    if generator:
        script = generator(ALL_COMMANDS)
        print(script, end='')
    else:
        raise EVMError(f"Unsupported shell: {args.shell}")
    return 0


# ── 命令注册表 ──────────────────────────────────────────────

COMMAND_HANDLERS = {
    'set': _cmd_set,
    'get': _cmd_get,
    'delete': _cmd_delete,
    'list': _cmd_list,
    'clear': _cmd_clear,
    'groups': _cmd_groups,
    'setg': _cmd_setg,
    'getg': _cmd_getg,
    'deleteg': _cmd_deleteg,
    'listg': _cmd_listg,
    'delete-group': _cmd_delete_group,
    'move-group': _cmd_move_group,
    'export': _cmd_export,
    'load': _cmd_load,
    'backup': _cmd_backup,
    'restore': _cmd_restore,
    'search': _cmd_search,
    'rename': _cmd_rename,
    'copy': _cmd_copy,
    'exec': _cmd_exec,
    'loadmemory': _cmd_loadmemory,
    'edit': _cmd_edit,
    'info': _cmd_info,
    'diff': _cmd_diff,
    'expand': _cmd_expand,
    'validate': _cmd_validate,
    'history': _cmd_history,
    'schema': _cmd_schema,
    'completion': _cmd_completion,
}


def _dispatch(
    mgr: EnvironmentManager,
    args,
    dry_run: bool,
    force: bool,
    json_mode: bool,
    quiet: bool,
) -> int:
    """命令调度（注册表模式）

    Returns:
        退出码（通常为 0，exec 命令透传子进程退出码）
    """
    cmd = args.command
    handler = COMMAND_HANDLERS.get(cmd)

    if handler is None:
        raise EVMError(f"Unknown command: {cmd}")

    return handler(mgr, args, dry_run, force, json_mode, quiet)  # type: ignore[no-any-return]


def _dispatch_schema(
    mgr: EnvironmentManager, args, json_mode: bool, quiet: bool
) -> int:
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
        if json_mode:
            json_output({"key": args.key, "message": msg}, quiet)
        elif not quiet:
            print(msg)

    elif sc_cmd == 'get':
        key = getattr(args, 'key', None)
        schema = mgr.get_schema(key)
        if json_mode:
            json_output(schema, quiet)
        elif not quiet:
            print_schema(schema)

    elif sc_cmd == 'delete':
        msg = mgr.delete_schema(args.key)
        if json_mode:
            json_output({"key": args.key, "message": msg}, quiet)
        elif not quiet:
            print(msg)

    elif sc_cmd == 'list':
        schema = mgr.get_schema()
        if json_mode:
            json_output(schema, quiet)
        elif not quiet:
            print_schema(schema)

    elif sc_cmd == 'validate':
        key = getattr(args, 'key', None)
        if key:
            result = mgr.validate(key)
            if json_mode:
                json_output({"key": key, **result}, quiet)
            elif not quiet:
                print_validate_result(key, result)
        else:
            results = mgr.validate_all()
            if json_mode:
                json_output(results, quiet)
            elif not quiet:
                print_validate_all(results)

    else:
        # 无子命令时显示 schema 列表
        schema = mgr.get_schema()
        if json_mode:
            json_output(schema, quiet)
        elif not quiet:
            print_schema(schema)

    return 0


__all__ = ['create_parser', 'main', 'ALL_COMMANDS', 'EXIT_CODE_MAP', 'COMMAND_HANDLERS']
