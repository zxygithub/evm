#!/usr/bin/env python3
"""
EVM 输出格式化

将业务数据转换为人类可读的终端输出。
所有 print() 调用集中在此模块。
"""

from typing import Optional


def print_vars_table(
    vars_dict: dict[str, str],
    title: str = "Environment Variables",
    show_total: bool = True,
) -> None:
    """以表格形式打印变量字典"""
    if not vars_dict:
        print("No environment variables set")
        return

    max_key_len = max(len(k) for k in vars_dict.keys())

    print(f"\n{title}:")
    print("-" * (max_key_len + 50))
    for key, value in sorted(vars_dict.items()):
        print(f"{key:<{max_key_len}} = {value}")
    print("-" * (max_key_len + 50))
    if show_total:
        print(f"Total: {len(vars_dict)} variables")


def print_vars_by_group(vars_dict: dict[str, str]) -> None:
    """按分组打印变量"""
    groups: dict[str, dict[str, str]] = {}
    for key, value in vars_dict.items():
        if ':' in key:
            group, var_name = key.split(':', 1)
        else:
            group = 'default'
            var_name = key
        groups.setdefault(group, {})[var_name] = value

    if not groups:
        print("No environment variables to display")
        return

    print("\nEnvironment Variables (by group):")
    print("=" * 70)
    total_vars = 0
    for group_name in sorted(groups.keys()):
        print(f"\n[{group_name}]")
        print("-" * 70)
        group_vars = groups[group_name]
        max_key_len = max(len(k) for k in group_vars.keys()) if group_vars else 0
        for key, value in sorted(group_vars.items()):
            print(f"{key:<{max_key_len}} = {value}")
        print("-" * 70)
        print(f"{len(group_vars)} variables")
        total_vars += len(group_vars)
    print("\n+" * 70)
    print(f"Total: {len(groups)} groups, {total_vars} variables")


def print_search_results(
    results: dict[str, str],
    pattern: str,
    search_value: bool = False,
) -> None:
    """打印搜索结果"""
    if not results:
        search_text = "key and value" if search_value else "key"
        print(f"No environment variables match '{pattern}' in {search_text}")
        return

    print_vars_table(
        results,
        title=f"Search results for '{pattern}'",
    )


def print_groups(groups: dict[str, int]) -> None:
    """打印分组列表"""
    if not groups:
        print("No groups found. All variables are in the default namespace.")
        return

    print("\nAvailable Groups:")
    print("-" * 50)
    for group in sorted(groups):
        print(f"{group:<30} ({groups[group]} variables)")
    print("-" * 50)
    print(f"Total: {len(groups)} groups")


def print_info(info: dict) -> None:
    """打印工具信息"""
    print("EVM (Environment Variable Manager)")
    print(f"Version: {info['version']}")
    print(f"Author: {info['author']}")
    print(f"License: {info['license']}")
    print(f"Python: {info['python']}")
    print(f"Platform: {info['platform']}")
    print(f"Storage: {info['storage_path']}")
    print(f"Storage exists: {info['storage_exists']}")
    print(f"Total variables: {info['total_variables']}")
    print(f"Total groups: {info['total_groups']}")
    print(f"Secret variables: {info['secret_variables']}")
    if info.get('groups'):
        print("Groups:")
        for g, c in sorted(info['groups'].items()):
            print(f"  {g}: {c} variables")
    print(f"\nRepository: {info['repository']}")


def print_diff(diff_result: dict) -> None:
    """打印 diff 结果"""
    added = diff_result.get('added', {})
    removed = diff_result.get('removed', {})
    changed = diff_result.get('changed', {})
    timestamp = diff_result.get('backup_timestamp', '')

    if timestamp:
        print(f"Comparing with backup (timestamp: {timestamp})\n")

    if not added and not removed and not changed:
        print("No differences found.")
        return

    if added:
        print(f"Added ({len(added)}):")
        print("-" * 50)
        for key, value in sorted(added.items()):
            print(f"  + {key} = {value}")
        print()

    if removed:
        print(f"Removed ({len(removed)}):")
        print("-" * 50)
        for key, value in sorted(removed.items()):
            print(f"  - {key} = {value}")
        print()

    if changed:
        print(f"Changed ({len(changed)}):")
        print("-" * 50)
        for key, values in sorted(changed.items()):
            print(f"  ~ {key}")
            print(f"      backup:  {values['backup']}")
            print(f"      current: {values['current']}")
        print()

    total = len(added) + len(removed) + len(changed)
    print(f"Total: {total} differences "
          f"(+{len(added)} added, -{len(removed)} removed, ~{len(changed)} changed)")


def print_load_memory_result(
    loaded_count: int,
    add_evm_prefix: bool,
    filter_prefix: Optional[str],
) -> None:
    """打印 loadmemory 结果"""
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


def print_history(entries: list[dict]) -> None:
    """打印操作历史"""
    if not entries:
        print("No history entries found.")
        return

    print(f"\nOperation History (latest {len(entries)} entries):")
    print("-" * 80)
    for entry in entries:
        ts = entry.get('timestamp', '')[:19]
        op = entry.get('operation', '')
        key = entry.get('key', '')
        details = entry.get('details', '')
        status = entry.get('status', '')
        status_mark = '✓' if status == 'success' else '✗'
        line = f"  {ts}  {status_mark} {op:<12}"
        if key:
            line += f" {key}"
        if details:
            line += f"  ({details})"
        print(line)
    print("-" * 80)


def print_validate_result(key: str, result: dict) -> None:
    """打印单个变量的校验结果"""
    if result['valid']:
        print(f"  ✓ {key}: valid")
    else:
        print(f"  ✗ {key}: INVALID")
    for err in result.get('errors', []):
        print(f"      error: {err}")
    for warn in result.get('warnings', []):
        print(f"      warning: {warn}")


def print_validate_all(results: dict[str, dict]) -> None:
    """打印所有变量的校验结果"""
    if not results:
        print("No schema definitions found.")
        return

    valid_count = sum(1 for r in results.values() if r['valid'])
    total = len(results)

    print(f"\nSchema Validation ({valid_count}/{total} valid):")
    print("-" * 60)
    for key in sorted(results):
        print_validate_result(key, results[key])
    print("-" * 60)
    if valid_count == total:
        print("All variables passed validation.")
    else:
        print(f"{total - valid_count} variable(s) failed validation.")


def print_schema(schema: dict) -> None:
    """打印 schema 定义"""
    if not schema:
        print("No schema definitions found.")
        return

    print("\nSchema Definitions:")
    print("-" * 60)
    for key in sorted(schema):
        entry = schema[key]
        parts = []
        if 'format' in entry:
            parts.append(f"format={entry['format']}")
        if 'required' in entry:
            parts.append(f"required={entry['required']}")
        if 'pattern' in entry:
            parts.append(f"pattern={entry['pattern']}")
        if 'description' in entry:
            parts.append(f"desc={entry['description']}")
        print(f"  {key:<30} {', '.join(parts)}")
    print("-" * 60)
    print(f"Total: {len(schema)} definitions")


__all__ = [
    'print_vars_table',
    'print_vars_by_group',
    'print_search_results',
    'print_groups',
    'print_info',
    'print_diff',
    'print_load_memory_result',
    'print_history',
    'print_validate_result',
    'print_validate_all',
    'print_schema',
]
