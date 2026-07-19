"""
evm shell 集成测试

覆盖：
- _completion.py 的 install/uninstall/is_installed 辅助函数
- cli.py 的 evm init 命令（--install/--uninstall/--reinstall/--check）
- main() 启动时的 _ensure_shell_integration 自动检查（含 opt-out、幂等）
"""



from evm._completion import (
    INTEGRATION_MARKER_END,
    INTEGRATION_MARKER_START,
    install_integration,
    is_integration_installed,
    uninstall_integration,
)
from evm.cli import main

# ══════════════════════════════════════════════════════════════
# 辅助函数单元测试
# ══════════════════════════════════════════════════════════════


class TestInstallHelpers:
    """install_integration / uninstall_integration / is_integration_installed"""

    def test_install_creates_rc_with_marker(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        ok, msg = install_integration('zsh')
        assert ok, msg
        rc = tmp_path / '.zshrc'
        assert rc.exists()
        content = rc.read_text()
        assert INTEGRATION_MARKER_START in content
        assert INTEGRATION_MARKER_END in content
        assert 'eval "$(evm init zsh)"' in content

    def test_install_is_idempotent(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        install_integration('zsh')
        ok, msg = install_integration('zsh')
        assert ok
        assert 'Already' in msg
        # 只有一个 marker 块
        content = (tmp_path / '.zshrc').read_text()
        assert content.count(INTEGRATION_MARKER_START) == 1

    def test_is_installed_before_and_after(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        assert not is_integration_installed('zsh')
        install_integration('zsh')
        assert is_integration_installed('zsh')

    def test_install_fish_creates_nested_dir(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        ok, msg = install_integration('fish')
        assert ok, msg
        assert (tmp_path / '.config' / 'fish' / 'config.fish').exists()

    def test_install_unknown_shell_fails(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        ok, msg = install_integration('powershell')
        assert not ok
        assert 'Unknown' in msg

    def test_uninstall_removes_block(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        rc = tmp_path / '.zshrc'
        rc.write_text('alias ll="ls -la"\n\n# user content\n')
        install_integration('zsh')
        assert is_integration_installed('zsh')
        ok, msg = uninstall_integration('zsh')
        assert ok, msg
        assert not is_integration_installed('zsh')
        # 用户原有内容保留
        content = rc.read_text()
        assert 'alias ll="ls -la"' in content
        assert '# user content' in content
        assert INTEGRATION_MARKER_START not in content

    def test_uninstall_preserves_surrounding_content(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        rc = tmp_path / '.zshrc'
        before = 'export PATH=/usr/local/bin:$PATH\n# my stuff\n'
        rc.write_text(before)
        install_integration('zsh')
        uninstall_integration('zsh')
        after = rc.read_text()
        assert 'export PATH=/usr/local/bin:$PATH' in after
        assert '# my stuff' in after

    def test_uninstall_when_not_installed(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        ok, msg = uninstall_integration('zsh')
        assert ok
        assert 'Nothing to remove' in msg

    def test_uninstall_when_rc_missing(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        ok, msg = uninstall_integration('zsh')
        assert ok
        assert 'does not exist' in msg

    def test_uninstall_unknown_shell(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        ok, msg = uninstall_integration('tcsh')
        assert not ok
        assert 'Unknown' in msg

    def test_reinstall_replaces_block(self, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        install_integration('zsh')
        rc = tmp_path / '.zshrc'
        # 篡改块内容模拟旧版
        content = rc.read_text().replace('evm init zsh', 'evm init zsh --old')
        rc.write_text(content)
        # reinstall
        uninstall_integration('zsh')
        install_integration('zsh')
        content = rc.read_text()
        assert 'evm init zsh --old' not in content
        assert 'eval "$(evm init zsh)"' in content
        assert content.count(INTEGRATION_MARKER_START) == 1


# ══════════════════════════════════════════════════════════════
# evm init 命令
# ══════════════════════════════════════════════════════════════


class TestCmdInit:
    """evm init 子命令"""

    def test_init_outputs_script(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        code = main(['init', 'zsh'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'evm-load()' in out
        assert '--shell zsh' in out

    def test_init_detects_shell_from_env(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/bash')
        code = main(['init'])  # 不指定 shell，从 $SHELL 推断
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'evm-load()' in out

    def test_init_install_writes_rc(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        code = main(['init', 'zsh', '--install'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'Installed' in out
        assert is_integration_installed('zsh')

    def test_init_install_idempotent(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        main(['init', 'zsh', '--install'])
        capsys.readouterr()
        code = main(['init', 'zsh', '--install'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'Already' in out

    def test_init_uninstall_removes(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        main(['init', 'zsh', '--install'])
        capsys.readouterr()
        code = main(['init', 'zsh', '--uninstall'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'Removed' in out
        assert not is_integration_installed('zsh')

    def test_init_reinstall(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        main(['init', 'zsh', '--install'])
        capsys.readouterr()
        code = main(['init', 'zsh', '--reinstall'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert is_integration_installed('zsh')
        rc = tmp_path / '.zshrc'
        assert rc.read_text().count(INTEGRATION_MARKER_START) == 1

    def test_init_check_installed(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        main(['init', 'zsh', '--install'])
        capsys.readouterr()
        code = main(['init', 'zsh', '--check'])
        out, _ = capsys.readouterr()
        assert code == 0
        assert 'installed' in out

    def test_init_check_not_installed(self, capsys, monkeypatch, tmp_path):
        monkeypatch.setenv('HOME', str(tmp_path))
        code = main(['init', 'zsh', '--check'])
        out, _ = capsys.readouterr()
        assert code == 1
        assert 'not installed' in out

    def test_init_check_json(self, capsys, monkeypatch, tmp_path):
        import json as json_mod
        monkeypatch.setenv('HOME', str(tmp_path))
        code = main(['--json', 'init', 'zsh', '--check'])
        out, _ = capsys.readouterr()
        assert code == 1
        data = json_mod.loads(out)
        assert data['status'] == 'ok'
        assert data['data']['installed'] is False

    def test_init_install_json(self, capsys, monkeypatch, tmp_path):
        import json as json_mod
        monkeypatch.setenv('HOME', str(tmp_path))
        code = main(['--json', 'init', 'zsh', '--install'])
        out, _ = capsys.readouterr()
        assert code == 0
        data = json_mod.loads(out)
        assert data['data']['ok'] is True


# ══════════════════════════════════════════════════════════════
# 自动安装（main 启动时检查）
# ══════════════════════════════════════════════════════════════


class TestAutoInstall:
    """任意 evm 命令启动时自动安装 shell 集成"""

    def _env_file(self, tmp_path):
        return str(tmp_path / 'env.json')

    def test_auto_install_on_arbitrary_command(self, capsys, monkeypatch, tmp_path):
        """evm 命令触发自动安装——提示出现在触发安装的那次调用的 stderr"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        env_file = self._env_file(tmp_path)
        # 第一个命令触发安装，提示走 stderr
        main(['--env-file', env_file, 'set', 'K', 'v'])
        _, err = capsys.readouterr()
        assert is_integration_installed('zsh')
        assert 'Installed' in err or 'Restart' in err

    def test_auto_install_idempotent(self, capsys, monkeypatch, tmp_path):
        """第二次运行不再提示"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        env_file = self._env_file(tmp_path)
        # 第一次：安装 + 提示
        main(['--env-file', env_file, 'set', 'K', 'v'])
        _, err1 = capsys.readouterr()
        assert 'Installed' in err1 or 'Restart' in err1
        # 第二次：幂等跳过，无提示
        main(['--env-file', env_file, 'list'])
        _, err2 = capsys.readouterr()
        assert 'Installed' not in err2
        assert 'Restart' not in err2

    def test_auto_install_opt_out(self, capsys, monkeypatch, tmp_path):
        """EVM_NO_AUTO_INSTALL=1 跳过自动安装"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        monkeypatch.setenv('EVM_NO_AUTO_INSTALL', '1')
        env_file = self._env_file(tmp_path)
        main(['--env-file', env_file, 'set', 'K', 'v'])
        capsys.readouterr()
        main(['--env-file', env_file, 'list'])
        _, err = capsys.readouterr()
        assert not is_integration_installed('zsh')
        assert 'Installed' not in err

    def test_auto_install_quiet_suppresses_notice(
        self, capsys, monkeypatch, tmp_path
    ):
        """--quiet 静默提示但仍然安装"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        env_file = self._env_file(tmp_path)
        main(['--env-file', env_file, 'set', 'K', 'v'])
        capsys.readouterr()
        main(['--env-file', env_file, '--quiet', 'list'])
        _, err = capsys.readouterr()
        assert is_integration_installed('zsh')
        assert 'Installed' not in err
        assert 'Restart' not in err

    def test_auto_install_skips_for_init_command(
        self, capsys, monkeypatch, tmp_path
    ):
        """evm init 命令自身不触发自动安装"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        main(['init', 'zsh'])  # 只输出脚本，不应触发自动安装
        out, err = capsys.readouterr()
        assert 'Installed' not in err
        assert 'Restart' not in err
        assert not is_integration_installed('zsh')

    def test_auto_install_skips_for_completion_command(
        self, capsys, monkeypatch, tmp_path
    ):
        """evm completion 命令不触发自动安装"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/bin/zsh')
        main(['completion', 'zsh'])
        out, err = capsys.readouterr()
        assert 'Installed' not in err
        assert not is_integration_installed('zsh')

    def test_auto_install_unknown_shell_skips(
        self, capsys, monkeypatch, tmp_path
    ):
        """$SHELL 是未知 shell 时静默跳过"""
        monkeypatch.setenv('HOME', str(tmp_path))
        monkeypatch.setenv('SHELL', '/usr/bin/nushell')
        env_file = self._env_file(tmp_path)
        main(['--env-file', env_file, 'set', 'K', 'v'])
        capsys.readouterr()
        main(['--env-file', env_file, 'list'])
        _, err = capsys.readouterr()
        assert 'Installed' not in err
