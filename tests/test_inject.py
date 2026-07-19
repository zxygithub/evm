"""
evm inject 命令测试

覆盖：
- manager.inject() 核心逻辑（posix/fish/group/secrets/prefix/跳过）
- CLI 层 inject 命令（输出、--shell/--group/--include-secrets/--prefix/--json/--dry-run/--quiet）
- completion 脚本内附的 evm-load 便捷函数
"""

import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from evm._completion import (
    generate_bash_completion,
    generate_fish_completion,
    generate_zsh_completion,
)
from evm.cli import ALL_COMMANDS, main
from evm.manager import EnvironmentManager

# ══════════════════════════════════════════════════════════════
# manager.inject() 单元测试
# ══════════════════════════════════════════════════════════════


class TestManagerInject:
    """manager.inject() 核心逻辑"""

    def _setup(self, env_file):
        return EnvironmentManager(env_file)

    def test_posix_export_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('PUSHPLUS_TOKEN', 'abc123')
            result = mgr.inject(shell='sh')
            assert result['shell'] == 'sh'
            assert result['count'] == 1
            assert result['variables'] == {'PUSHPLUS_TOKEN': 'abc123'}
            assert result['output'] == "export PUSHPLUS_TOKEN=abc123\n"

    def test_bash_and_zsh_use_posix_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('KEY', 'val')
            for shell in ('bash', 'zsh', 'sh'):
                result = mgr.inject(shell=shell)
                assert result['output'] == 'export KEY=val\n', shell

    def test_fish_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('KEY', 'val')
            result = mgr.inject(shell='fish')
            assert result['output'] == 'set -gx KEY val\n'

    def test_unknown_shell_falls_back_to_posix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('KEY', 'val')
            result = mgr.inject(shell='powershell')
            assert result['shell'] == 'powershell'
            assert result['output'].startswith('export KEY=')

    def test_grouped_vars_skipped_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('PLAIN', 'p')
            mgr.set_grouped('dev', 'DB_URL', 'localhost')
            result = mgr.inject(shell='sh')
            assert result['count'] == 1
            assert 'PLAIN' in result['variables']
            assert 'dev:DB_URL' not in result['variables']
            # 分组变量在默认模式下被静默排除（非"跳过"，而是"未选中"）
            assert result['skipped'] == []

    def test_group_filter_strips_prefix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set_grouped('dev', 'DB_URL', 'localhost')
            mgr.set_grouped('prod', 'DB_URL', 'remote')
            mgr.set('PLAIN', 'p')
            result = mgr.inject(shell='sh', group='dev')
            assert result['count'] == 1
            assert result['variables'] == {'DB_URL': 'localhost'}
            assert 'PLAIN' not in result['variables']

    def test_group_filter_nonexistent_group_yields_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('PLAIN', 'p')
            result = mgr.inject(shell='sh', group='nonexistent')
            assert result['count'] == 0
            assert result['output'] == ''

    def test_secret_skipped_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set_secret('SECRET_VAR', 'topsecret')
            mgr.set('PLAIN', 'p')
            result = mgr.inject(shell='sh')
            assert 'SECRET_VAR' not in result['variables']
            assert 'SECRET_VAR' in result['skipped']
            # 密文绝不应出现在输出里
            assert 'topsecret' not in result['output']

    def test_include_secrets_decrypts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set_secret('SECRET_VAR', 'topsecret')
            result = mgr.inject(shell='sh', include_secrets=True)
            assert result['variables']['SECRET_VAR'] == 'topsecret'
            assert "export SECRET_VAR=topsecret\n" in result['output']
            assert 'SECRET_VAR' not in result['skipped']

    def test_invalid_shell_identifier_skipped(self):
        # 含冒号的 key 已被分组逻辑跳过；此处验证其它非法字符
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            # 直接操作内部存储，绕过 key 校验
            mgr._env_vars['1INVALID'] = 'v'
            mgr._env_vars['HAS-DASH'] = 'v'
            mgr._env_vars['VALID'] = 'ok'
            result = mgr.inject(shell='sh')
            assert result['variables'] == {'VALID': 'ok'}
            assert '1INVALID' in result['skipped']
            assert 'HAS-DASH' in result['skipped']

    def test_prefix_adds_prefix(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('KEY', 'val')
            result = mgr.inject(shell='sh', prefix='EVM_')
            assert result['variables'] == {'EVM_KEY': 'val'}
            assert result['output'] == 'export EVM_KEY=val\n'

    def test_prefix_group_combined(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set_grouped('dev', 'DB_URL', 'localhost')
            result = mgr.inject(shell='sh', group='dev', prefix='DEV_')
            assert result['variables'] == {'DEV_DB_URL': 'localhost'}
            assert result['output'] == 'export DEV_DB_URL=localhost\n'

    def test_empty_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            result = mgr.inject(shell='sh')
            assert result['count'] == 0
            assert result['output'] == ''
            assert result['variables'] == {}

    def test_value_with_spaces_quoted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('KEY', 'my value with spaces')
            result = mgr.inject(shell='sh')
            assert result['output'] == "export KEY='my value with spaces'\n"

    def test_value_with_single_quote_escaped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            val = "my'value"
            mgr.set('KEY', val)
            result = mgr.inject(shell='sh')
            expected = f'export KEY={shlex.quote(val)}\n'
            assert result['output'] == expected
            # 往返：解析后应得到原值
            parsed = shlex.split(result['output'].removeprefix('export ').strip())
            assert parsed[0] == f'KEY={val}'

    def test_value_with_dollar_sign_quoted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('KEY', '$HOME')
            result = mgr.inject(shell='sh')
            assert result['output'] == "export KEY='$HOME'\n"

    def test_output_sorted_by_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            mgr = self._setup(env_file)
            mgr.set('ZEBRA', 'z')
            mgr.set('ALPHA', 'a')
            mgr.set('MIKE', 'm')
            result = mgr.inject(shell='sh')
            lines = [ln for ln in result['output'].split('\n') if ln]
            assert lines == [
                'export ALPHA=a',
                'export MIKE=m',
                'export ZEBRA=z',
            ]


# ══════════════════════════════════════════════════════════════
# CLI inject 命令测试
# ══════════════════════════════════════════════════════════════


class TestCLIInject:
    """evm inject CLI 命令"""

    def _setup_env(self, tmpdir):
        env_file = os.path.join(tmpdir, 'env.json')
        return env_file

    def test_inject_default_outputs_export_lines(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'PUSHPLUS_TOKEN', 'abc123'])
            capsys.readouterr()
            code = main(['--env-file', env_file, 'inject', '--shell', 'sh'])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == 'export PUSHPLUS_TOKEN=abc123\n'

    def test_inject_fish_outputs_set_gx(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, 'inject', '--shell', 'fish'
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == 'set -gx KEY val\n'

    def test_inject_group_strips_prefix(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'setg', 'dev', 'DB_URL', 'localhost'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, 'inject', '--shell', 'sh',
                '--group', 'dev',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == 'export DB_URL=localhost\n'

    def test_inject_secret_skipped_by_default(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', '--secret', 'SEC', 'topsecret'])
            main(['--env-file', env_file, 'set', 'PLAIN', 'p'])
            capsys.readouterr()
            code = main(['--env-file', env_file, 'inject', '--shell', 'sh'])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == 'export PLAIN=p\n'

    def test_inject_include_secrets_decrypts(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', '--secret', 'SEC', 'topsecret'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, 'inject', '--shell', 'sh',
                '--include-secrets',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == 'export SEC=topsecret\n'

    def test_inject_prefix(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, 'inject', '--shell', 'sh',
                '--prefix', 'EVM_',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == 'export EVM_KEY=val\n'

    def test_inject_json_mode(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, '--json',
                'inject', '--shell', 'sh',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            data = json.loads(out)
            assert data['status'] == 'ok'
            assert data['data']['shell'] == 'sh'
            assert data['data']['count'] == 1
            assert data['data']['variables'] == {'KEY': 'val'}
            assert data['data']['output'] == 'export KEY=val\n'

    def test_inject_json_reports_skipped(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', '--secret', 'SEC', 'topsecret'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, '--json',
                'inject', '--shell', 'sh',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            data = json.loads(out)
            assert data['data']['count'] == 0
            # 加密变量默认跳过并记入 skipped
            assert 'SEC' in data['data']['skipped']

    def test_inject_dry_run_no_eval_output(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, '--dry-run',
                'inject', '--shell', 'sh',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            # 预览模式：人类可读，不含可 eval 的 export 行
            assert '[DRY-RUN]' in out
            assert 'export KEY=' not in out
            assert '  KEY' in out

    def test_inject_quiet_no_output(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            code = main([
                '--env-file', env_file, '--quiet',
                'inject', '--shell', 'sh',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == ''

    def test_inject_empty_storage(self, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            capsys.readouterr()
            code = main(['--env-file', env_file, 'inject', '--shell', 'sh'])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out == ''

    def test_inject_eval_roundtrip_actually_sets_env(self, capsys):
        """端到端：eval 输出后子进程能读到注入的变量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = self._setup_env(tmpdir)
            main(['--env-file', env_file, 'set', 'INJECT_TEST', 'injected!'])
            capsys.readouterr()
            main(['--env-file', env_file, 'inject', '--shell', 'sh'])
            inject_out, _ = capsys.readouterr()
            # 用 sh 实际 eval 注入语句，再读取变量
            import subprocess
            result = subprocess.run(
                ['sh', '-c', f'{inject_out} echo "INJECT_TEST=$INJECT_TEST"'],
                capture_output=True, text=True,
            )
            assert result.returncode == 0
            assert result.stdout.strip() == 'INJECT_TEST=injected!'

    def test_inject_help_lists_all_flags(self, capsys):
        """inject --help 列出所有选项"""
        with self._raises_system_exit(capsys):
            main(['inject', '--help'])
        out, _ = capsys.readouterr()
        for flag in ('--shell', '--group', '--include-secrets', '--prefix'):
            assert flag in out

    @staticmethod
    def _raises_system_exit(capsys):
        import pytest
        return pytest.raises(SystemExit)


# ══════════════════════════════════════════════════════════════
# Shell 自动检测
# ══════════════════════════════════════════════════════════════


class TestShellDetection:
    """_detect_shell 从 $SHELL 推断 shell 类型"""

    def test_detect_bash(self, monkeypatch):
        from evm.cli import _detect_shell
        monkeypatch.setenv('SHELL', '/bin/bash')
        assert _detect_shell() == 'bash'

    def test_detect_zsh(self, monkeypatch):
        from evm.cli import _detect_shell
        monkeypatch.setenv('SHELL', '/bin/zsh')
        assert _detect_shell() == 'zsh'

    def test_detect_fish(self, monkeypatch):
        from evm.cli import _detect_shell
        monkeypatch.setenv('SHELL', '/usr/local/bin/fish')
        assert _detect_shell() == 'fish'

    def test_detect_unknown_falls_back_to_sh(self, monkeypatch):
        from evm.cli import _detect_shell
        monkeypatch.setenv('SHELL', '/usr/bin/nushell')
        assert _detect_shell() == 'sh'

    def test_detect_empty_shell_falls_back_to_sh(self, monkeypatch):
        from evm.cli import _detect_shell
        monkeypatch.delenv('SHELL', raising=False)
        assert _detect_shell() == 'sh'

    def test_inject_auto_detects_from_shell(self, monkeypatch, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            monkeypatch.setenv('SHELL', '/bin/fish')
            code = main(['--env-file', env_file, 'inject'])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out.startswith('set -gx ')  # fish 格式

    def test_explicit_shell_overrides_detection(self, monkeypatch, capsys):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, 'env.json')
            main(['--env-file', env_file, 'set', 'KEY', 'val'])
            capsys.readouterr()
            monkeypatch.setenv('SHELL', '/bin/fish')
            code = main([
                '--env-file', env_file, 'inject', '--shell', 'bash',
            ])
            out, _ = capsys.readouterr()
            assert code == 0
            assert out.startswith('export ')  # posix 格式


# ══════════════════════════════════════════════════════════════
# evm-load 便捷函数（随 completion 脚本安装）
# ══════════════════════════════════════════════════════════════


class TestEvmLoadInCompletion:
    """completion 脚本应内附 evm-load 函数"""

    def test_bash_completion_contains_evm_load(self):
        script = generate_bash_completion(ALL_COMMANDS)
        assert 'evm-load()' in script
        assert '--shell bash' in script
        assert '--env-file' in script

    def test_zsh_completion_contains_evm_load(self):
        script = generate_zsh_completion(ALL_COMMANDS)
        assert 'evm-load()' in script
        assert '--shell zsh' in script
        assert '--env-file' in script

    def test_fish_completion_contains_evm_load(self):
        script = generate_fish_completion(ALL_COMMANDS)
        assert 'function evm-load' in script
        assert '--shell fish' in script
        assert '| source' in script

    def test_bash_evm_load_handles_env_file_arg(self):
        """evm-load 函数应把 --env-file 提取到 inject 之前"""
        script = generate_bash_completion(ALL_COMMANDS)
        # 函数体应包含对 --env-file 的 case 分支
        assert '--env-file)' in script or '--env-file)' in script

    def test_fish_evm_load_uses_argparse(self):
        script = generate_fish_completion(ALL_COMMANDS)
        assert 'argparse' in script
        assert '_flag_env_file' in script

    def test_completion_cli_includes_evm_load(self, capsys):
        """evm completion bash 输出应包含 evm-load 函数"""
        main(['completion', 'bash'])
        out, _ = capsys.readouterr()
        assert 'evm-load()' in out

    def test_completion_cli_zsh_includes_evm_load(self, capsys):
        main(['completion', 'zsh'])
        out, _ = capsys.readouterr()
        assert 'evm-load()' in out

    def test_completion_cli_fish_includes_evm_load(self, capsys):
        main(['completion', 'fish'])
        out, _ = capsys.readouterr()
        assert 'function evm-load' in out


# ── 端到端：实际 source + 调用 evm-load ───────────────────────
# 这些测试需要对应的 shell 和 evm 命令在 PATH 中，否则跳过。

_EVM_ON_PATH = shutil.which('evm') is not None


def _shell_available(shell):
    return shutil.which(shell) is not None


class TestEvmLoadEndToEnd:
    """端到端验证 evm-load 在真实 shell 中注入变量"""

    @pytest.mark.skipif(
        not (_EVM_ON_PATH and _shell_available('bash')),
        reason='bash 或 evm 不在 PATH',
    )
    def test_bash_evm_load_injects_vars(self, tmp_path):
        env_file = str(tmp_path / 'env.json')
        comp_file = str(tmp_path / 'comp.bash')
        main(['--env-file', env_file, 'set', 'E2E_BASH', 'injected'])
        Path(comp_file).write_text(generate_bash_completion(ALL_COMMANDS))
        result = subprocess.run(
            ['bash', '-c', (
                f'source {comp_file} 2>/dev/null; '
                f'evm-load --env-file {env_file} 2>/dev/null; '
                'echo "E2E_BASH=$E2E_BASH"'
            )],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert 'E2E_BASH=injected' in result.stdout

    @pytest.mark.skipif(
        not (_EVM_ON_PATH and _shell_available('zsh')),
        reason='zsh 或 evm 不在 PATH',
    )
    def test_zsh_evm_load_injects_vars(self, tmp_path):
        env_file = str(tmp_path / 'env.json')
        comp_file = str(tmp_path / 'comp.zsh')
        main(['--env-file', env_file, 'set', 'E2E_ZSH', 'injected'])
        Path(comp_file).write_text(generate_zsh_completion(ALL_COMMANDS))
        result = subprocess.run(
            ['zsh', '-c', (
                f'source {comp_file} 2>/dev/null; '
                f'evm-load --env-file {env_file} 2>/dev/null; '
                'echo "E2E_ZSH=$E2E_ZSH"'
            )],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert 'E2E_ZSH=injected' in result.stdout

    @pytest.mark.skipif(
        not (_EVM_ON_PATH and _shell_available('fish')),
        reason='fish 或 evm 不在 PATH',
    )
    def test_fish_evm_load_injects_vars(self, tmp_path):
        env_file = str(tmp_path / 'env.json')
        comp_file = str(tmp_path / 'comp.fish')
        main(['--env-file', env_file, 'set', 'E2E_FISH', 'injected'])
        Path(comp_file).write_text(generate_fish_completion(ALL_COMMANDS))
        result = subprocess.run(
            ['fish', '-c', (
                f'source {comp_file} 2>/dev/null; '
                f'evm-load --env-file {env_file} 2>/dev/null; '
                'echo "E2E_FISH=$E2E_FISH"'
            )],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, result.stderr
        assert 'E2E_FISH=injected' in result.stdout

