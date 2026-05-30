#!/usr/bin/env python3
"""
_io.py 边界测试

覆盖 _detect_format、_load_json_file、_load_env_file、_load_nested、
_apply_group_prefix、export、load、backup、restore、diff 的各种边界条件。
"""

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path

import pytest

from evm import (
    BackupError,
    EnvironmentManager,
    ExportError,
    ImportFailedError,
)
from evm.exceptions import GroupNotFoundError


class TestDetectFormat:
    """_detect_format: 文件格式自动检测与强制指定"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_force_format_overrides_extension(self):
        """强制指定 format 时忽略文件后缀"""
        path = Path(self.temp_dir) / 'data.json'
        path.write_text('{}')
        result = self.mgr._detect_format(path, 'env')
        assert result == 'env'

    def test_json_suffix_detected(self):
        """.json 后缀 → json"""
        path = Path(self.temp_dir) / 'data.json'
        path.write_text('{}')
        result = self.mgr._detect_format(path, None)
        assert result == 'json'

    def test_backup_suffix_detected(self):
        """.backup 后缀 → json"""
        path = Path(self.temp_dir) / 'data.backup'
        path.write_text('{}')
        result = self.mgr._detect_format(path, None)
        assert result == 'json'

    def test_env_suffix_detected(self):
        """.env 后缀 → env"""
        path = Path(self.temp_dir) / 'data.env'
        path.write_text('KEY=val')
        result = self.mgr._detect_format(path, None)
        assert result == 'env'

    def test_content_sniff_json(self):
        """无已知后缀，内容以 { 开头 → json"""
        path = Path(self.temp_dir) / 'data.txt'
        path.write_text('{"KEY": "val"}')
        result = self.mgr._detect_format(path, None)
        assert result == 'json'

    def test_content_sniff_env(self):
        """无已知后缀，内容不以 { 开头 → env"""
        path = Path(self.temp_dir) / 'data.txt'
        path.write_text('KEY=val\nFOO=bar')
        result = self.mgr._detect_format(path, None)
        assert result == 'env'

    def test_unreadable_file_defaults_to_json(self):
        """无法读取的文件默认返回 json（OSError 分支）"""
        path = Path(self.temp_dir) / 'unreadable.txt'
        path.write_text('{}')
        os.chmod(str(path), 0o000)
        try:
            result = self.mgr._detect_format(path, None)
            assert result == 'json'
        finally:
            os.chmod(str(path), 0o644)


class TestLoadJsonFile:
    """_load_json_file: JSON 加载边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_non_dict_json_raises(self):
        """JSON 文件内容不是 dict → ImportFailedError"""
        path = Path(self.temp_dir) / 'array.json'
        path.write_text('[1, 2, 3]')
        with pytest.raises(ImportFailedError, match='expected a dictionary'):
            self.mgr._load_json_file(path)

    def test_string_json_raises(self):
        """JSON 文件内容是字符串 → ImportFailedError"""
        path = Path(self.temp_dir) / 'string.json'
        path.write_text('"just a string"')
        with pytest.raises(ImportFailedError, match='expected a dictionary'):
            self.mgr._load_json_file(path)

    def test_malformed_json_raises(self):
        """损坏的 JSON → ImportFailedError"""
        path = Path(self.temp_dir) / 'bad.json'
        path.write_text('{invalid json content')
        with pytest.raises(ImportFailedError, match='JSON parse error'):
            self.mgr._load_json_file(path)

    def test_valid_dict_loads(self):
        """正常 dict JSON → 正确加载"""
        path = Path(self.temp_dir) / 'good.json'
        path.write_text('{"KEY": "val", "FOO": "bar"}')
        result = self.mgr._load_json_file(path)
        assert result == {"KEY": "val", "FOO": "bar"}


class TestLoadEnvFile:
    """_load_env_file: .env 解析边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_empty_file(self):
        """空文件 → 空 dict"""
        path = Path(self.temp_dir) / 'empty.env'
        path.write_text('')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {}
        assert skipped == []

    def test_only_comments(self):
        """只有注释 → 空 dict"""
        path = Path(self.temp_dir) / 'comments.env'
        path.write_text('# comment1\n# comment2\n')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {}

    def test_lines_without_equals_ignored(self):
        """没有 = 号的行被忽略"""
        path = Path(self.temp_dir) / 'no_equals.env'
        path.write_text('GOOD=val\nNOEQUALSSIGN\nANOTHER=val2')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {'GOOD': 'val', 'ANOTHER': 'val2'}
        assert skipped == []

    def test_value_with_equals_in_it(self):
        """值中包含 = 号"""
        path = Path(self.temp_dir) / 'equals.env'
        path.write_text('URL=http://host:3000/path?a=1&b=2')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {'URL': 'http://host:3000/path?a=1&b=2'}

    def test_empty_value(self):
        """空值"""
        path = Path(self.temp_dir) / 'empty_val.env'
        path.write_text('EMPTY=')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {'EMPTY': ''}

    def test_whitespace_lines_ignored(self):
        """空白行被忽略"""
        path = Path(self.temp_dir) / 'whitespace.env'
        path.write_text('\n\n  \nKEY=val\n\n')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {'KEY': 'val'}

    def test_multiple_invalid_keys_reported(self):
        """多个无效 key 全部报告"""
        path = Path(self.temp_dir) / 'multi_bad.env'
        path.write_text('1BAD=v1\n2BAD=v2\nGOOD=v3\n-ALSO_BAD=v4')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {'GOOD': 'v3'}
        assert len(skipped) == 3
        assert '1BAD' in skipped
        assert '2BAD' in skipped
        assert '-ALSO_BAD' in skipped

    def test_key_with_leading_trailing_spaces(self):
        """key 前后有空格会被 strip"""
        path = Path(self.temp_dir) / 'spaces.env'
        path.write_text('  GOOD  =val')
        loaded, skipped = self.mgr._load_env_file(path)
        assert loaded == {'GOOD': 'val'}


class TestLoadNested:
    """_load_nested: 嵌套 JSON 加载边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_mixed_nested_and_flat(self):
        """混合嵌套和扁平值"""
        data = {
            'dev': {'KEY1': 'v1'},
            'GLOBAL_VAL': 'flat',
            'prod': {'KEY2': 'v2'},
        }
        loaded, groups = self.mgr._load_nested(data)
        assert loaded == {
            'dev:KEY1': 'v1',
            'GLOBAL_VAL': 'flat',
            'prod:KEY2': 'v2',
        }
        assert groups == 2

    def test_numeric_values_converted_to_string(self):
        """非 dict 值转为字符串"""
        data = {'PORT': 3000, 'DEBUG': True, 'RATE': 1.5}
        loaded, groups = self.mgr._load_nested(data)
        assert loaded == {'PORT': '3000', 'DEBUG': 'True', 'RATE': '1.5'}
        assert groups == 0

    def test_empty_dict(self):
        """空 dict → 空结果"""
        loaded, groups = self.mgr._load_nested({})
        assert loaded == {}
        assert groups == 0


class TestApplyGroupPrefix:
    """_apply_group_prefix: 分组前缀边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_no_group_returns_unchanged(self):
        """group=None → 原样返回"""
        data = {'A': '1', 'B': '2'}
        result = self.mgr._apply_group_prefix(data, None)
        assert result == data

    def test_empty_group_returns_unchanged(self):
        """group='' → 原样返回"""
        data = {'A': '1'}
        result = self.mgr._apply_group_prefix(data, '')
        assert result == {'A': '1'}

    def test_prefix_added(self):
        """添加分组前缀"""
        data = {'KEY': 'val'}
        result = self.mgr._apply_group_prefix(data, 'dev')
        assert result == {'dev:KEY': 'val'}

    def test_existing_prefix_not_doubled(self):
        """已有前缀的 key 不重复添加"""
        data = {'dev:KEY': 'val', 'OTHER': 'val2'}
        result = self.mgr._apply_group_prefix(data, 'dev')
        assert result == {'dev:KEY': 'val', 'dev:OTHER': 'val2'}


class TestExportBoundaries:
    """export: 导出边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_export_empty_vars(self):
        """无变量时返回提示"""
        msg = self.mgr.export()
        assert 'No environment variables to export' in msg

    def test_export_unsupported_format(self):
        """不支持的格式 → ExportError"""
        self.mgr.set('KEY', 'val')
        with pytest.raises(ExportError, match='Unsupported format'):
            self.mgr.export(format_type='xml')

    def test_export_to_readonly_dir_raises(self):
        """导出到不可写目录 → ExportError"""
        self.mgr.set('KEY', 'val')
        readonly = Path(self.temp_dir) / 'readonly'
        readonly.mkdir()
        os.chmod(str(readonly), stat.S_IRUSR | stat.S_IXUSR)
        try:
            out = str(readonly / 'out.json')
            with pytest.raises(ExportError, match='Error exporting'):
                self.mgr.export(format_type='json', output_file=out)
        finally:
            os.chmod(str(readonly), 0o755)

    def test_export_group_no_vars(self):
        """导出空分组 → GroupNotFoundError"""
        self.mgr.set('OTHER', 'val')
        with pytest.raises(GroupNotFoundError):
            self.mgr.export(group='nonexistent')

    def test_export_env_format(self):
        """导出为 .env 格式"""
        self.mgr.set('A', '1')
        self.mgr.set('B', '2')
        out = os.path.join(self.temp_dir, 'out.env')
        msg = self.mgr.export(format_type='env', output_file=out)
        assert 'exported' in msg.lower() or 'exported' in msg
        content = Path(out).read_text()
        assert 'A=1' in content
        assert 'B=2' in content

    def test_export_sh_format(self):
        """导出为 .sh 格式"""
        self.mgr.set('MY_KEY', 'my val')
        out = os.path.join(self.temp_dir, 'out.sh')
        msg = self.mgr.export(format_type='sh', output_file=out)
        assert 'exported' in msg.lower() or 'exported' in msg
        content = Path(out).read_text()
        assert '#!/bin/bash' in content
        assert 'export' in content
        assert 'MY_KEY' in content

    def test_export_dry_run(self):
        """dry-run 不创建文件"""
        self.mgr.set('KEY', 'val')
        out = os.path.join(self.temp_dir, 'dryrun.json')
        msg = self.mgr.export(output_file=out, dry_run=True)
        assert 'DRY-RUN' in msg
        assert not os.path.exists(out)

    def test_export_default_output_path(self):
        """未指定 output_file 时使用默认路径"""
        self.mgr.set('KEY', 'val')
        msg = self.mgr.export(format_type='json')
        assert 'exported' in msg.lower() or 'exported' in msg


class TestLoadBoundaries:
    """load: 导入边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_load_nonexistent_file(self):
        """不存在的文件 → ImportFailedError"""
        with pytest.raises(ImportFailedError, match='File not found'):
            self.mgr.load('/nonexistent/path/data.json')

    def test_load_backup_format(self):
        """导入备份格式文件（含 timestamp + variables）"""
        backup_path = Path(self.temp_dir) / 'backup.json'
        backup_data = {
            'timestamp': '2026-01-01T00:00:00',
            'variables': {'B_KEY': 'b_val'},
        }
        backup_path.write_text(json.dumps(backup_data))
        msg = self.mgr.load(str(backup_path))
        assert 'Detected backup file' in msg
        assert '2026-01-01' in msg
        assert self.mgr.get('B_KEY') == 'b_val'

    def test_load_replace_mode(self):
        """replace 模式替换所有变量"""
        self.mgr.set('OLD', 'old_val')
        data_path = Path(self.temp_dir) / 'replace.json'
        data_path.write_text(json.dumps({'NEW': 'new_val'}))
        msg = self.mgr.load(str(data_path), replace=True)
        assert 'Replaced' in msg
        assert not self.mgr.exists('OLD')
        assert self.mgr.get('NEW') == 'new_val'

    def test_load_with_group_prefix(self):
        """导入时添加分组前缀"""
        data_path = Path(self.temp_dir) / 'grouped.json'
        data_path.write_text(json.dumps({'KEY': 'val'}))
        msg = self.mgr.load(str(data_path), group='staging')
        assert 'staging' in msg
        assert self.mgr.exists('staging:KEY')

    def test_load_dry_run(self):
        """dry-run 不修改环境变量"""
        self.mgr.set('EXISTING', 'old')
        data_path = Path(self.temp_dir) / 'dry.json'
        data_path.write_text(json.dumps({'NEW': 'val'}))
        msg = self.mgr.load(str(data_path), dry_run=True)
        assert 'DRY-RUN' in msg
        assert not self.mgr.exists('NEW')
        assert self.mgr.get('EXISTING') == 'old'

    def test_load_nested_with_groups(self):
        """nest=True 自动检测分组"""
        data_path = Path(self.temp_dir) / 'nested.json'
        data_path.write_text(json.dumps({
            'dev': {'A': '1'},
            'prod': {'B': '2'},
        }))
        msg = self.mgr.load(str(data_path), nest=True)
        assert 'Detected and imported 2 groups' in msg
        assert self.mgr.exists('dev:A')
        assert self.mgr.exists('prod:B')

    def test_load_dry_run_with_nest(self):
        """dry-run + nest 组合"""
        data_path = Path(self.temp_dir) / 'nested.json'
        data_path.write_text(json.dumps({'dev': {'A': '1'}}))
        msg = self.mgr.load(str(data_path), nest=True, dry_run=True)
        assert 'DRY-RUN' in msg

    def test_load_env_file_with_skipped_keys_message(self):
        """导入 .env 文件时报告跳过的无效 key"""
        env_path = Path(self.temp_dir) / 'bad.env'
        env_path.write_text('GOOD=v\n1BAD=v')
        msg = self.mgr.load(str(env_path))
        assert 'Skipped 1' in msg
        assert '1BAD' in msg


class TestRestoreBoundaries:
    """restore: 恢复边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_restore_nonexistent_file(self):
        """不存在的备份文件 → BackupError"""
        with pytest.raises(BackupError, match='not found'):
            self.mgr.restore('/nonexistent/backup.json')

    def test_restore_invalid_format(self):
        """缺少 'variables' 字段的备份文件 → BackupError"""
        path = Path(self.temp_dir) / 'bad_backup.json'
        path.write_text(json.dumps({'data': 'not_variables'}))
        with pytest.raises(BackupError, match='Invalid backup'):
            self.mgr.restore(str(path))

    def test_restore_merge_mode(self):
        """merge=True 合并而非替换"""
        self.mgr.set('EXISTING', 'old')
        path = Path(self.temp_dir) / 'merge_backup.json'
        path.write_text(json.dumps({
            'timestamp': '2026-01-01',
            'variables': {'NEW': 'val'},
        }))
        msg = self.mgr.restore(str(path), merge=True)
        assert 'Merged' in msg
        assert self.mgr.exists('EXISTING')
        assert self.mgr.exists('NEW')

    def test_restore_replace_mode(self):
        """默认 replace 模式替换所有"""
        self.mgr.set('OLD', 'old_val')
        path = Path(self.temp_dir) / 'replace_backup.json'
        path.write_text(json.dumps({
            'timestamp': '2026-06-01',
            'variables': {'FRESH': 'new'},
        }))
        msg = self.mgr.restore(str(path))
        assert 'Restored' in msg
        assert not self.mgr.exists('OLD')
        assert self.mgr.exists('FRESH')

    def test_restore_with_timestamp(self):
        """恢复时显示时间戳"""
        path = Path(self.temp_dir) / 'ts_backup.json'
        path.write_text(json.dumps({
            'timestamp': '2026-05-30T12:00:00',
            'variables': {'K': 'v'},
        }))
        msg = self.mgr.restore(str(path))
        assert '2026-05-30T12:00:00' in msg

    def test_restore_corrupted_json(self):
        """损坏的 JSON 备份 → BackupError"""
        path = Path(self.temp_dir) / 'corrupt.json'
        path.write_text('{broken json content')
        with pytest.raises(BackupError):
            self.mgr.restore(str(path))


class TestDiffBoundaries:
    """diff: 差异比较边界条件"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'env.json')
        self.mgr = EnvironmentManager(self.env_file)

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_diff_nonexistent_file(self):
        """不存在的文件 → BackupError"""
        with pytest.raises(BackupError, match='not found'):
            self.mgr.diff('/nonexistent/file.json')

    def test_diff_corrupted_json(self):
        """损坏的 JSON → BackupError"""
        path = Path(self.temp_dir) / 'bad.json'
        path.write_text('{bad json')
        with pytest.raises(BackupError):
            self.mgr.diff(str(path))

    def test_diff_with_backup_format(self):
        """diff 使用备份格式文件（含 'variables' key）"""
        self.mgr.set('A', 'new')
        path = Path(self.temp_dir) / 'backup.json'
        path.write_text(json.dumps({
            'timestamp': '2026-01-01',
            'variables': {'A': 'old', 'B': 'removed'},
        }))
        result = self.mgr.diff(str(path))
        assert 'A' in result['changed']
        assert 'B' in result['removed']
        assert result['backup_timestamp'] == '2026-01-01'

    def test_diff_with_plain_dict(self):
        """diff 使用纯 dict 文件（无 'variables' key）"""
        self.mgr.set('X', '1')
        path = Path(self.temp_dir) / 'plain.json'
        path.write_text(json.dumps({'X': '2', 'Y': '3'}))
        result = self.mgr.diff(str(path))
        assert 'X' in result['changed']
        assert 'Y' in result['removed']

    def test_diff_non_dict_format_raises(self):
        """非 dict 格式 → BackupError"""
        path = Path(self.temp_dir) / 'array.json'
        path.write_text(json.dumps([1, 2, 3]))
        with pytest.raises(BackupError, match='Invalid file format'):
            self.mgr.diff(str(path))

    def test_diff_no_differences(self):
        """无差异时返回空 added/removed/changed"""
        self.mgr.set('K', 'v')
        path = Path(self.temp_dir) / 'same.json'
        path.write_text(json.dumps({'K': 'v'}))
        result = self.mgr.diff(str(path))
        assert result['added'] == {}
        assert result['removed'] == {}
        assert result['changed'] == {}

    def test_diff_added_keys(self):
        """当前有但备份没有 → added"""
        self.mgr.set('NEW_KEY', 'val')
        path = Path(self.temp_dir) / 'old.json'
        path.write_text(json.dumps({}))
        result = self.mgr.diff(str(path))
        assert 'NEW_KEY' in result['added']
