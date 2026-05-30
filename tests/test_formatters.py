#!/usr/bin/env python3
"""
测试 formatters.py 的所有输出函数
"""

from evm.formatters import (
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


class TestPrintVarsTable:
    """测试 print_vars_table 函数"""

    def test_empty_dict(self, capsys):
        """测试空字典"""
        print_vars_table({})
        captured = capsys.readouterr()
        assert "No environment variables set" in captured.out

    def test_normal_dict(self, capsys):
        """测试正常字典"""
        vars_dict = {"API_KEY": "abc123", "DB_HOST": "localhost"}
        print_vars_table(vars_dict)
        captured = capsys.readouterr()
        assert "API_KEY" in captured.out
        assert "abc123" in captured.out
        assert "DB_HOST" in captured.out
        assert "localhost" in captured.out
        assert "Total: 2 variables" in captured.out

    def test_custom_title(self, capsys):
        """测试自定义标题"""
        print_vars_table({"KEY": "value"}, title="Custom Title")
        captured = capsys.readouterr()
        assert "Custom Title:" in captured.out

    def test_show_total_false(self, capsys):
        """测试隐藏总数"""
        print_vars_table({"KEY": "value"}, show_total=False)
        captured = capsys.readouterr()
        assert "Total:" not in captured.out

    def test_single_item(self, capsys):
        """测试单个项目"""
        print_vars_table({"SINGLE": "item"})
        captured = capsys.readouterr()
        assert "SINGLE" in captured.out
        assert "item" in captured.out
        assert "Total: 1 variables" in captured.out


class TestPrintVarsByGroup:
    """测试 print_vars_by_group 函数"""

    def test_empty_dict(self, capsys):
        """测试空字典"""
        print_vars_by_group({})
        captured = capsys.readouterr()
        assert "No environment variables to display" in captured.out

    def test_with_groups(self, capsys):
        """测试带分组的变量"""
        vars_dict = {
            "dev:API_KEY": "dev-key",
            "dev:DB_HOST": "localhost",
            "prod:API_KEY": "prod-key",
        }
        print_vars_by_group(vars_dict)
        captured = capsys.readouterr()
        assert "[dev]" in captured.out
        assert "[prod]" in captured.out
        assert "API_KEY" in captured.out
        assert "DB_HOST" in captured.out
        assert "Total: 2 groups" in captured.out

    def test_without_groups(self, capsys):
        """测试不带分组的变量（归入 default）"""
        vars_dict = {"API_KEY": "key", "DB_HOST": "host"}
        print_vars_by_group(vars_dict)
        captured = capsys.readouterr()
        assert "[default]" in captured.out
        assert "API_KEY" in captured.out

    def test_mixed_groups(self, capsys):
        """测试混合分组"""
        vars_dict = {
            "dev:KEY1": "val1",
            "GLOBAL": "val2",
            "prod:KEY2": "val3",
        }
        print_vars_by_group(vars_dict)
        captured = capsys.readouterr()
        assert "[default]" in captured.out
        assert "[dev]" in captured.out
        assert "[prod]" in captured.out


class TestPrintSearchResults:
    """测试 print_search_results 函数"""

    def test_empty_results(self, capsys):
        """测试空结果"""
        print_search_results({}, "pattern")
        captured = capsys.readouterr()
        assert "No environment variables match 'pattern' in key" in captured.out

    def test_empty_results_with_value_search(self, capsys):
        """测试空结果（值搜索）"""
        print_search_results({}, "pattern", search_value=True)
        captured = capsys.readouterr()
        assert "No environment variables match 'pattern' in key and value" in captured.out

    def test_with_results(self, capsys):
        """测试有结果"""
        results = {"API_KEY": "abc", "API_SECRET": "xyz"}
        print_search_results(results, "API")
        captured = capsys.readouterr()
        assert "Search results for 'API'" in captured.out
        assert "API_KEY" in captured.out
        assert "API_SECRET" in captured.out


class TestPrintGroups:
    """测试 print_groups 函数"""

    def test_empty_groups(self, capsys):
        """测试空分组"""
        print_groups({})
        captured = capsys.readouterr()
        assert "No groups found" in captured.out

    def test_with_groups(self, capsys):
        """测试有分组"""
        groups = {"dev": 5, "prod": 3, "staging": 2}
        print_groups(groups)
        captured = capsys.readouterr()
        assert "dev" in captured.out
        assert "prod" in captured.out
        assert "staging" in captured.out
        assert "5 variables" in captured.out
        assert "3 variables" in captured.out
        assert "2 variables" in captured.out
        assert "Total: 3 groups" in captured.out


class TestPrintInfo:
    """测试 print_info 函数"""

    def test_basic_info(self, capsys):
        """测试基本信息"""
        info = {
            "version": "2.2.0",
            "author": "EVM Team",
            "license": "MIT",
            "python": "3.13.9",
            "platform": "Darwin",
            "storage_path": "/tmp/env.json",
            "storage_exists": True,
            "total_variables": 10,
            "total_groups": 2,
            "secret_variables": 3,
            "repository": "https://github.com/evm/evm",
        }
        print_info(info)
        captured = capsys.readouterr()
        assert "EVM (Environment Variable Manager)" in captured.out
        assert "Version: 2.2.0" in captured.out
        assert "Author: EVM Team" in captured.out
        assert "License: MIT" in captured.out
        assert "Python: 3.13.9" in captured.out
        assert "Platform: Darwin" in captured.out
        assert "Storage: /tmp/env.json" in captured.out
        assert "Storage exists: True" in captured.out
        assert "Total variables: 10" in captured.out
        assert "Total groups: 2" in captured.out
        assert "Secret variables: 3" in captured.out
        assert "Repository: https://github.com/evm/evm" in captured.out

    def test_with_groups(self, capsys):
        """测试带分组信息"""
        info = {
            "version": "2.2.0",
            "author": "EVM Team",
            "license": "MIT",
            "python": "3.13.9",
            "platform": "Darwin",
            "storage_path": "/tmp/env.json",
            "storage_exists": True,
            "total_variables": 10,
            "total_groups": 2,
            "secret_variables": 3,
            "groups": {"dev": 5, "prod": 5},
            "repository": "https://github.com/evm/evm",
        }
        print_info(info)
        captured = capsys.readouterr()
        assert "Groups:" in captured.out
        assert "dev: 5 variables" in captured.out
        assert "prod: 5 variables" in captured.out


class TestPrintDiff:
    """测试 print_diff 函数"""

    def test_no_differences(self, capsys):
        """测试无差异"""
        print_diff({"added": {}, "removed": {}, "changed": {}})
        captured = capsys.readouterr()
        assert "No differences found" in captured.out

    def test_with_timestamp(self, capsys):
        """测试带时间戳"""
        print_diff({
            "added": {},
            "removed": {},
            "changed": {},
            "backup_timestamp": "2024-01-01T00:00:00",
        })
        captured = capsys.readouterr()
        assert "Comparing with backup (timestamp: 2024-01-01T00:00:00)" in captured.out

    def test_with_added(self, capsys):
        """测试有新增"""
        print_diff({
            "added": {"NEW_KEY": "new_value"},
            "removed": {},
            "changed": {},
        })
        captured = capsys.readouterr()
        assert "Added (1):" in captured.out
        assert "+ NEW_KEY = new_value" in captured.out
        assert "Total: 1 differences" in captured.out

    def test_with_removed(self, capsys):
        """测试有删除"""
        print_diff({
            "added": {},
            "removed": {"OLD_KEY": "old_value"},
            "changed": {},
        })
        captured = capsys.readouterr()
        assert "Removed (1):" in captured.out
        assert "- OLD_KEY = old_value" in captured.out

    def test_with_changed(self, capsys):
        """测试有修改"""
        print_diff({
            "added": {},
            "removed": {},
            "changed": {
                "KEY": {"backup": "old", "current": "new"},
            },
        })
        captured = capsys.readouterr()
        assert "Changed (1):" in captured.out
        assert "~ KEY" in captured.out
        assert "backup:  old" in captured.out
        assert "current: new" in captured.out

    def test_mixed_changes(self, capsys):
        """测试混合变化"""
        print_diff({
            "added": {"A": "1"},
            "removed": {"B": "2"},
            "changed": {"C": {"backup": "3", "current": "4"}},
        })
        captured = capsys.readouterr()
        assert "Added (1):" in captured.out
        assert "Removed (1):" in captured.out
        assert "Changed (1):" in captured.out
        assert "Total: 3 differences" in captured.out
        assert "+1 added" in captured.out
        assert "-1 removed" in captured.out
        assert "~1 changed" in captured.out


class TestPrintLoadMemoryResult:
    """测试 print_load_memory_result 函数"""

    def test_no_variables(self, capsys):
        """测试无变量"""
        print_load_memory_result(0, False, None)
        captured = capsys.readouterr()
        assert "No environment variables to load" in captured.out

    def test_no_variables_with_filter(self, capsys):
        """测试无变量但有过滤"""
        print_load_memory_result(0, False, "PREFIX")
        captured = capsys.readouterr()
        assert "No environment variables to load" in captured.out
        assert "No variables found with prefix 'PREFIX'" in captured.out

    def test_with_variables(self, capsys):
        """测试有变量"""
        print_load_memory_result(5, False, None)
        captured = capsys.readouterr()
        assert "Loaded 5 environment variables to memory" in captured.out

    def test_with_prefix(self, capsys):
        """测试带 EVM 前缀"""
        print_load_memory_result(3, True, None)
        captured = capsys.readouterr()
        assert "Loaded 3 environment variables to memory" in captured.out
        assert "Prefix 'EVM:' added to all variable names" in captured.out

    def test_with_filter(self, capsys):
        """测试带过滤"""
        print_load_memory_result(2, False, "DEV_")
        captured = capsys.readouterr()
        assert "Loaded 2 environment variables to memory" in captured.out
        assert "Filter: keys starting with 'DEV_'" in captured.out

    def test_with_prefix_and_filter(self, capsys):
        """测试同时带前缀和过滤"""
        print_load_memory_result(4, True, "TEST_")
        captured = capsys.readouterr()
        assert "Loaded 4 environment variables to memory" in captured.out
        assert "Prefix 'EVM:' added to all variable names" in captured.out
        assert "Filter: keys starting with 'TEST_'" in captured.out


class TestPrintHistory:
    """测试 print_history 函数"""

    def test_empty_history(self, capsys):
        """测试空历史"""
        print_history([])
        captured = capsys.readouterr()
        assert "No history entries found" in captured.out

    def test_with_entries(self, capsys):
        """测试有记录"""
        entries = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "operation": "set",
                "key": "API_KEY",
                "details": "value changed",
                "status": "success",
            },
            {
                "timestamp": "2024-01-01T13:00:00",
                "operation": "delete",
                "key": "OLD_KEY",
                "status": "success",
            },
        ]
        print_history(entries)
        captured = capsys.readouterr()
        assert "Operation History (latest 2 entries):" in captured.out
        assert "2024-01-01T12:00:00" in captured.out
        assert "set" in captured.out
        assert "API_KEY" in captured.out
        assert "value changed" in captured.out
        assert "✓" in captured.out  # success mark
        assert "2024-01-01T13:00:00" in captured.out
        assert "delete" in captured.out
        assert "OLD_KEY" in captured.out

    def test_with_failed_status(self, capsys):
        """测试失败状态"""
        entries = [
            {
                "timestamp": "2024-01-01T12:00:00",
                "operation": "set",
                "key": "KEY",
                "status": "failed",
            },
        ]
        print_history(entries)
        captured = capsys.readouterr()
        assert "✗" in captured.out  # failed mark


class TestPrintValidateResult:
    """测试 print_validate_result 函数"""

    def test_valid_result(self, capsys):
        """测试有效结果"""
        print_validate_result("API_URL", {
            "valid": True,
            "errors": [],
            "warnings": [],
        })
        captured = capsys.readouterr()
        assert "✓ API_URL: valid" in captured.out

    def test_invalid_result(self, capsys):
        """测试无效结果"""
        print_validate_result("API_URL", {
            "valid": False,
            "errors": ["Invalid URL format"],
            "warnings": [],
        })
        captured = capsys.readouterr()
        assert "✗ API_URL: INVALID" in captured.out
        assert "error: Invalid URL format" in captured.out

    def test_with_warnings(self, capsys):
        """测试带警告"""
        print_validate_result("API_URL", {
            "valid": True,
            "errors": [],
            "warnings": ["Consider using HTTPS"],
        })
        captured = capsys.readouterr()
        assert "✓ API_URL: valid" in captured.out
        assert "warning: Consider using HTTPS" in captured.out


class TestPrintValidateAll:
    """测试 print_validate_all 函数"""

    def test_empty_results(self, capsys):
        """测试空结果"""
        print_validate_all({})
        captured = capsys.readouterr()
        assert "No schema definitions found" in captured.out

    def test_all_valid(self, capsys):
        """测试全部有效"""
        results = {
            "API_URL": {"valid": True, "errors": [], "warnings": []},
            "DB_HOST": {"valid": True, "errors": [], "warnings": []},
        }
        print_validate_all(results)
        captured = capsys.readouterr()
        assert "Schema Validation (2/2 valid):" in captured.out
        assert "✓ API_URL: valid" in captured.out
        assert "✓ DB_HOST: valid" in captured.out
        assert "All variables passed validation" in captured.out

    def test_some_invalid(self, capsys):
        """测试部分无效"""
        results = {
            "API_URL": {"valid": True, "errors": [], "warnings": []},
            "DB_HOST": {
                "valid": False,
                "errors": ["Invalid host"],
                "warnings": [],
            },
        }
        print_validate_all(results)
        captured = capsys.readouterr()
        assert "Schema Validation (1/2 valid):" in captured.out
        assert "✓ API_URL: valid" in captured.out
        assert "✗ DB_HOST: INVALID" in captured.out
        assert "1 variable(s) failed validation" in captured.out


class TestPrintSchema:
    """测试 print_schema 函数"""

    def test_empty_schema(self, capsys):
        """测试空 schema"""
        print_schema({})
        captured = capsys.readouterr()
        assert "No schema definitions found" in captured.out

    def test_with_schema(self, capsys):
        """测试有 schema"""
        schema = {
            "API_URL": {
                "format": "url",
                "required": True,
                "description": "API endpoint",
            },
            "DB_HOST": {
                "format": "hostname",
                "pattern": r"^[a-z0-9.-]+$",
            },
        }
        print_schema(schema)
        captured = capsys.readouterr()
        assert "Schema Definitions:" in captured.out
        assert "API_URL" in captured.out
        assert "format=url" in captured.out
        assert "required=True" in captured.out
        assert "desc=API endpoint" in captured.out
        assert "DB_HOST" in captured.out
        assert "format=hostname" in captured.out
        assert r"pattern=^[a-z0-9.-]+$" in captured.out
        assert "Total: 2 definitions" in captured.out
