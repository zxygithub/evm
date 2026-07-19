#!/usr/bin/env python3
"""
evm upgrade 命令测试

覆盖：
- evm._upgrade 模块的纯函数（版本比较、PyPI 查询、升级执行）
- cli.py 的 evm upgrade 命令（--check / --dry-run / --json / --quiet / --force）
- upgrade 命令不触发 shell 集成自动安装
"""

import json
import subprocess
import urllib.error
from unittest.mock import patch

import pytest

from evm import __version__, _upgrade
from evm.cli import main

# ══════════════════════════════════════════════════════════════
# 辅助
# ══════════════════════════════════════════════════════════════

class _FakeUrllibResponse:
    """模拟 urllib.request.urlopen 返回的上下文管理器"""

    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._payload


def _pypi_payload(version: str) -> bytes:
    return json.dumps({'info': {'version': version}}).encode('utf-8')


def _env_file(tmp_path):
    return str(tmp_path / 'env.json')


# ══════════════════════════════════════════════════════════════
# 纯函数单元测试
# ══════════════════════════════════════════════════════════════

class TestVersionCompare:
    """_parse_version / is_newer"""

    @pytest.mark.parametrize('remote,local,expected', [
        ('2.6.0', '2.5.0', True),
        ('2.5.0', '2.5.0', False),
        ('2.4.0', '2.5.0', False),
        ('2.5.1', '2.5.0', True),
        ('3.0.0', '2.9.9', True),
        ('2.5', '2.5.0', False),       # 短版本补零后相等
        ('2.5.0.1', '2.5.0', True),    # 多一段更新
        ('2.5.0', '2.5.0.1', False),
    ])
    def test_is_newer(self, remote, local, expected):
        assert _upgrade.is_newer(remote, local) is expected

    def test_parse_version_non_numeric_segments_become_zero(self):
        assert _upgrade._parse_version('1.2.x') == (1, 2, 0)
        assert _upgrade._parse_version('1') == (1,)


class TestGetCurrentVersion:
    def test_returns_package_version(self):
        assert _upgrade.get_current_version() == __version__


# ══════════════════════════════════════════════════════════════
# fetch_latest_version — 网络层
# ══════════════════════════════════════════════════════════════

class TestFetchLatestVersion:
    def test_success_returns_version(self):
        with patch('evm._upgrade.urllib.request.urlopen') as mock_open:
            mock_open.return_value = _FakeUrllibResponse(_pypi_payload('9.9.9'))
            assert _upgrade.fetch_latest_version() == '9.9.9'

    def test_url_error_returns_none(self):
        with patch('evm._upgrade.urllib.request.urlopen',
                   side_effect=urllib.error.URLError('boom')):
            assert _upgrade.fetch_latest_version() is None

    def test_oserror_returns_none(self):
        with patch('evm._upgrade.urllib.request.urlopen',
                   side_effect=OSError('boom')):
            assert _upgrade.fetch_latest_version() is None

    def test_bad_json_returns_none(self):
        with patch('evm._upgrade.urllib.request.urlopen') as mock_open:
            mock_open.return_value = _FakeUrllibResponse(b'not json')
            assert _upgrade.fetch_latest_version() is None

    def test_missing_version_key_returns_none(self):
        with patch('evm._upgrade.urllib.request.urlopen') as mock_open:
            mock_open.return_value = _FakeUrllibResponse(b'{"info": {}}')
            assert _upgrade.fetch_latest_version() is None


# ══════════════════════════════════════════════════════════════
# check_for_update
# ══════════════════════════════════════════════════════════════

class TestCheckForUpdate:
    def test_update_available(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        latest, available = _upgrade.check_for_update()
        assert latest == '9.9.9'
        assert available is True

    def test_already_latest(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        latest, available = _upgrade.check_for_update()
        assert latest == __version__
        assert available is False

    def test_network_unavailable(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: None)
        latest, available = _upgrade.check_for_update()
        assert latest is None
        assert available is None


# ══════════════════════════════════════════════════════════════
# perform_upgrade — 子进程层
# ══════════════════════════════════════════════════════════════

def _completed(returncode=0, stdout='', stderr=''):
    return subprocess.CompletedProcess(
        args=['pip'], returncode=returncode,
        stdout=stdout, stderr=stderr,
    )


class TestPerformUpgrade:
    def test_already_latest(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        action, msg, new_ver = _upgrade.perform_upgrade()
        assert action == 'already_latest'
        assert __version__ in msg
        assert new_ver == __version__

    def test_network_error(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: None)
        action, msg, new_ver = _upgrade.perform_upgrade()
        assert action == 'network_error'
        assert new_ver == ''

    def test_dry_run_with_update(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        action, msg, new_ver = _upgrade.perform_upgrade(dry_run=True)
        assert action == 'dry_run'
        assert '[DRY-RUN]' in msg
        assert 'pip' in msg
        assert new_ver == ''

    def test_dry_run_force_skips_check(self, monkeypatch):
        # force=True 应跳过 check_for_update，直接 dry-run
        called = {'check': False}

        def fake_check(timeout=10.0):
            called['check'] = True
            return None, None

        monkeypatch.setattr(_upgrade, 'check_for_update', fake_check)
        action, msg, new_ver = _upgrade.perform_upgrade(force=True, dry_run=True)
        assert action == 'dry_run'
        assert called['check'] is False

    def test_upgrade_success(self, monkeypatch):
        # 第一次 fetch（预检查）返回更新版本，第二次（升级后）也返回该版本
        versions = iter(['9.9.9', '9.9.9'])
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: next(versions))
        monkeypatch.setattr(_upgrade.subprocess, 'run',
                            lambda *a, **kw: _completed(returncode=0))
        action, msg, new_ver = _upgrade.perform_upgrade()
        assert action == 'upgraded'
        assert '9.9.9' in msg
        assert new_ver == '9.9.9'

    def test_upgrade_pip_failure(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        monkeypatch.setattr(_upgrade.subprocess, 'run',
                            lambda *a, **kw: _completed(
                                returncode=1, stderr='nope'))
        action, msg, new_ver = _upgrade.perform_upgrade()
        assert action == 'failed'
        assert 'exit 1' in msg
        assert 'nope' in msg
        assert new_ver == ''

    def test_upgrade_oserror(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')

        def raise_oserror(*a, **kw):
            raise OSError('pip missing')

        monkeypatch.setattr(_upgrade.subprocess, 'run', raise_oserror)
        action, msg, new_ver = _upgrade.perform_upgrade()
        assert action == 'failed'
        assert 'pip missing' in msg

    def test_upgrade_timeout(self, monkeypatch):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')

        def raise_timeout(*a, **kw):
            raise subprocess.TimeoutExpired(cmd='pip', timeout=1)

        monkeypatch.setattr(_upgrade.subprocess, 'run', raise_timeout)
        action, msg, new_ver = _upgrade.perform_upgrade()
        assert action == 'failed'

    def test_force_runs_pip_without_precheck(self, monkeypatch):
        called = {'check': False, 'pip': False}

        def fake_check(timeout=10.0):
            called['check'] = True
            return None, None

        def fake_run(*a, **kw):
            called['pip'] = True
            return _completed(returncode=0)

        monkeypatch.setattr(_upgrade, 'check_for_update', fake_check)
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        monkeypatch.setattr(_upgrade.subprocess, 'run', fake_run)
        action, msg, new_ver = _upgrade.perform_upgrade(force=True)
        assert action == 'upgraded'
        assert called['check'] is False
        assert called['pip'] is True


# ══════════════════════════════════════════════════════════════
# CLI: evm upgrade --check
# ══════════════════════════════════════════════════════════════

class TestCmdUpgradeCheck:
    """evm upgrade --check 子命令"""

    def test_check_up_to_date(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        code = main(['--env-file', _env_file(tmp_path), 'upgrade', '--check'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'Already up to date.' in out
        assert __version__ in out

    def test_check_update_available(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        code = main(['--env-file', _env_file(tmp_path), 'upgrade', '--check'])
        out, _ = capsys.readouterr()
        assert code == 1
        assert 'Update available!' in out
        assert '9.9.9' in out

    def test_check_network_error(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: None)
        code = main(['--env-file', _env_file(tmp_path), 'upgrade', '--check'])
        out, _ = capsys.readouterr()
        assert code == 1
        assert 'unknown' in out

    def test_check_json_up_to_date(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        code = main(['--json', '--env-file', _env_file(tmp_path),
                     'upgrade', '--check'])
        out, _ = capsys.readouterr()
        assert code == 0
        data = json.loads(out)
        assert data['status'] == 'ok'
        assert data['data']['current'] == __version__
        assert data['data']['update_available'] is False

    def test_check_json_update_available(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        code = main(['--json', '--env-file', _env_file(tmp_path),
                     'upgrade', '--check'])
        out, _ = capsys.readouterr()
        assert code == 1
        data = json.loads(out)
        assert data['data']['update_available'] is True
        assert data['data']['latest'] == '9.9.9'

    def test_check_json_network_error(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: None)
        code = main(['--json', '--env-file', _env_file(tmp_path),
                     'upgrade', '--check'])
        out, err = capsys.readouterr()
        assert code == 1
        assert out == ''
        data = json.loads(err)
        assert data['status'] == 'error'

    def test_check_quiet_no_output(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        code = main(['--quiet', '--env-file', _env_file(tmp_path),
                     'upgrade', '--check'])
        out, _ = capsys.readouterr()
        assert code == 1
        assert out == ''


# ══════════════════════════════════════════════════════════════
# CLI: evm upgrade（实际升级 / dry-run）
# ══════════════════════════════════════════════════════════════

class TestCmdUpgrade:
    """evm upgrade（非 --check）"""

    def test_dry_run(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        ran = {'pip': False}

        def fake_run(*a, **kw):
            ran['pip'] = True
            return _completed(returncode=0)

        monkeypatch.setattr(_upgrade.subprocess, 'run', fake_run)
        code = main(['--env-file', _env_file(tmp_path),
                     'upgrade', '--dry-run'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert '[DRY-RUN]' in out
        assert 'pip' in out
        assert ran['pip'] is False  # dry-run 不能真正调用 pip

    def test_already_latest(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        ran = {'pip': False}

        def fake_run(*a, **kw):
            ran['pip'] = True
            return _completed(returncode=0)

        monkeypatch.setattr(_upgrade.subprocess, 'run', fake_run)
        code = main(['--env-file', _env_file(tmp_path), 'upgrade'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'Already up to date' in out
        assert ran['pip'] is False  # 已最新则不调用 pip

    def test_upgrade_success(self, capsys, monkeypatch, tmp_path):
        versions = iter(['9.9.9', '9.9.9'])
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: next(versions))
        monkeypatch.setattr(_upgrade.subprocess, 'run',
                            lambda *a, **kw: _completed(returncode=0))
        code = main(['--env-file', _env_file(tmp_path), 'upgrade'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'Upgraded' in out
        assert '9.9.9' in out

    def test_upgrade_pip_failure(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        monkeypatch.setattr(_upgrade.subprocess, 'run',
                            lambda *a, **kw: _completed(
                                returncode=1, stderr='permission denied'))
        code = main(['--env-file', _env_file(tmp_path), 'upgrade'])
        out, _ = capsys.readouterr()
        assert code == 1
        assert 'failed' in out.lower()

    def test_upgrade_network_error(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: None)
        code = main(['--env-file', _env_file(tmp_path), 'upgrade'])
        out, _ = capsys.readouterr()
        assert code == 1
        assert 'Unable' in out

    def test_force_skips_precheck(self, capsys, monkeypatch, tmp_path):
        called = {'check': False, 'pip': False}

        def fake_check(timeout=10.0):
            called['check'] = True
            return None, None

        def fake_run(*a, **kw):
            called['pip'] = True
            return _completed(returncode=0)

        monkeypatch.setattr(_upgrade, 'check_for_update', fake_check)
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        monkeypatch.setattr(_upgrade.subprocess, 'run', fake_run)
        code = main(['--env-file', _env_file(tmp_path),
                     'upgrade', '--force'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert called['check'] is False
        assert called['pip'] is True

    def test_upgrade_json_success(self, capsys, monkeypatch, tmp_path):
        versions = iter(['9.9.9', '9.9.9'])
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: next(versions))
        monkeypatch.setattr(_upgrade.subprocess, 'run',
                            lambda *a, **kw: _completed(returncode=0))
        code = main(['--json', '--env-file', _env_file(tmp_path), 'upgrade'])
        out, _ = capsys.readouterr()
        assert code == 0
        data = json.loads(out)
        assert data['status'] == 'ok'
        assert data['data']['action'] == 'upgraded'
        assert data['data']['upgraded'] is True
        assert data['data']['new_version'] == '9.9.9'

    def test_upgrade_json_failure(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: '9.9.9')
        monkeypatch.setattr(_upgrade.subprocess, 'run',
                            lambda *a, **kw: _completed(returncode=1))
        code = main(['--json', '--env-file', _env_file(tmp_path), 'upgrade'])
        out, err = capsys.readouterr()
        assert code == 1
        assert out == ''
        data = json.loads(err)
        assert data['status'] == 'error'

    def test_upgrade_quiet_no_output(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        code = main(['--quiet', '--env-file', _env_file(tmp_path), 'upgrade'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert out == ''


# ══════════════════════════════════════════════════════════════
# upgrade 不触发 shell 集成自动安装
# ══════════════════════════════════════════════════════════════

class TestUpgradeSkipsAutoInstall:
    """evm upgrade 命令自身不应触发 shell 集成自动安装"""

    def test_no_auto_install_on_check(self, capsys, monkeypatch, tmp_path):
        from evm._completion import is_integration_installed
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        main(['--env-file', _env_file(tmp_path), 'upgrade', '--check'])
        _, err = capsys.readouterr()
        assert 'Installed' not in err
        assert not is_integration_installed('zsh')

    def test_no_auto_install_on_upgrade(self, capsys, monkeypatch, tmp_path):
        from evm._completion import is_integration_installed
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        monkeypatch.setattr(_upgrade, 'fetch_latest_version',
                            lambda timeout=10.0: __version__)
        main(['--env-file', _env_file(tmp_path), 'upgrade'])
        _, err = capsys.readouterr()
        assert 'Installed' not in err
        assert not is_integration_installed('zsh')
