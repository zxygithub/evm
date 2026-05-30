#!/usr/bin/env python3
"""
EVM Shell 补全脚本生成

支持 bash, zsh, fish。
M3: 为 get/delete/edit/expand/validate/rename/copy 等命令
提供动态变量名补全（通过 evm list --json --quiet 获取 key 列表）。
"""


def generate_bash_completion(commands: list) -> str:
    """生成 bash 补全脚本（含动态变量名补全）"""
    cmds = ' '.join(commands)
    # 需要变量名补全的命令
    key_cmds = ' '.join([
        'get', 'delete', 'edit', 'expand', 'validate',
        'rename', 'copy', 'setg', 'getg', 'deleteg', 'listg',
    ])
    return f'''# EVM bash completion
_evm_completions() {{
    local cur prev opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Top-level commands
    local commands="{cmds}"
    local global_opts="--help --version --verbose --env-file --json --quiet --dry-run --force"
    local key_cmds="{key_cmds}"

    # 动态获取变量名列表
    _evm_keys() {{
        evm list --json --quiet 2>/dev/null | \\
            python3 -c "import sys,json; d=json.load(sys.stdin); print(' '.join(d.get('data',{{}}).keys()))" 2>/dev/null
    }}

    case "${{prev}}" in
        evm)
            COMPREPLY=( $(compgen -W "${{commands}} ${{global_opts}}" -- "${{cur}}") )
            return 0
            ;;
        --env-file)
            COMPREPLY=( $(compgen -f -- "${{cur}}") )
            return 0
            ;;
        --format|-f)
            COMPREPLY=( $(compgen -W "json env sh backup" -- "${{cur}}") )
            return 0
            ;;
        set)
            COMPREPLY=( $(compgen -W "--secret --help" -- "${{cur}}") )
            return 0
            ;;
        get|delete|edit|expand|validate|rename|copy)
            COMPREPLY=( $(compgen -W "$(_evm_keys) --secret --help" -- "${{cur}}") )
            return 0
            ;;
        setg|getg|deleteg|listg)
            # 分组名补全（从现有 key 中提取分组前缀）
            local groups
            groups=$(evm groups --json --quiet 2>/dev/null | \\
                python3 -c "import sys,json; d=json.load(sys.stdin); print(' '.join(d.get('data',{{}}).get('groups',{{}}).keys()))" 2>/dev/null)
            COMPREPLY=( $(compgen -W "${{groups}} --help" -- "${{cur}}") )
            return 0
            ;;
        export)
            COMPREPLY=( $(compgen -W "--format --output --group --help" -- "${{cur}}") )
            return 0
            ;;
        load)
            COMPREPLY=( $(compgen -W "--format --replace --group --nest --help" -- "${{cur}}") )
            return 0
            ;;
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- "${{cur}}") )
            return 0
            ;;
    esac

    # 如果前一个词是需要 key 补全的命令，尝试补全变量名
    for kc in ${{key_cmds}}; do
        if [[ "${{COMP_WORDS[1]}}" == "$kc" ]]; then
            COMPREPLY=( $(compgen -W "$(_evm_keys)" -- "${{cur}}") )
            return 0
        fi
    done

    COMPREPLY=( $(compgen -W "${{commands}} ${{global_opts}}" -- "${{cur}}") )
}}
complete -F _evm_completions evm
'''


def generate_zsh_completion(commands: list) -> str:
    """生成 zsh 补全脚本（含动态变量名补全）"""
    return f'''#compdef evm

_evm() {{
    local -a commands
    commands=(
        {chr(10).join(f"        '{c}:{c} command'" for c in commands)}
    )

    # 动态获取变量名列表
    _evm_keys() {{
        local keys
        keys=(${{(f)"$(evm list --json --quiet 2>/dev/null | \\
            python3 -c "import sys,json; d=json.load(sys.stdin); print('\\n'.join(d.get('data',{{}}).keys()))" 2>/dev/null)"}})
        _describe 'variable' keys
    }}

    # 动态获取分组名列表
    _evm_groups() {{
        local groups
        groups=(${{(f)"$(evm groups --json --quiet 2>/dev/null | \\
            python3 -c "import sys,json; d=json.load(sys.stdin); print('\\n'.join(d.get('data',{{}}).get('groups',{{}}).keys()))" 2>/dev/null)"}})
        _describe 'group' groups
    }}

    _arguments -C \\
        '--help[Show help]' \\
        '--version[Show version]' \\
        '(-v --verbose)'{{-v,--verbose}}'[Show detailed info]' \\
        '--env-file[Storage file path]:file:_files' \\
        '--json[Output structured JSON]' \\
        '--quiet[Suppress output]' \\
        '--dry-run[Preview changes]' \\
        '--force[Skip confirmation]' \\
        '1: :->command' \\
        '*:: :->args'

    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                get|delete|edit|expand|validate)
                    _evm_keys
                    ;;
                rename|copy)
                    _evm_keys
                    ;;
                setg|getg|deleteg|listg)
                    _evm_groups
                    ;;
                completion)
                    _values 'shell' bash zsh fish
                    ;;
                export)
                    _arguments \\
                        '(-f --format)'{{-f,--format}}'[Format]:format:(json env sh)' \\
                        '(-o --output)'{{-o,--output}}'[Output file]:file:_files' \\
                        '(-g --group)'{{-g,--group}}'[Group name]:group'
                    ;;
            esac
            ;;
    esac
}}

_evm "$@"
'''


def generate_fish_completion(commands: list) -> str:
    """生成 fish 补全脚本（含动态变量名补全）"""
    lines = ['# EVM fish completion', '']

    # Disable file completion by default
    lines.append('complete -c evm -f')
    lines.append('')

    # Global options
    lines.append('# Global options')
    lines.append("complete -c evm -l help -d 'Show help'")
    lines.append("complete -c evm -l version -d 'Show version'")
    lines.append("complete -c evm -s v -l verbose -d 'Show detailed info'")
    lines.append("complete -c evm -l env-file -d 'Storage file path' -r -F")
    lines.append("complete -c evm -l json -d 'Output structured JSON'")
    lines.append("complete -c evm -l quiet -s q -d 'Suppress output'")
    lines.append("complete -c evm -l dry-run -d 'Preview changes'")
    lines.append("complete -c evm -l force -d 'Skip confirmation'")
    lines.append('')

    # Commands
    lines.append('# Commands')
    for cmd in commands:
        lines.append(f"complete -c evm -n '__fish_use_subcommand' -a '{cmd}' -d '{cmd}'")
    lines.append('')

    # Dynamic variable name completion helper
    lines.append('# Dynamic variable name completion')
    lines.append('function __evm_keys')
    lines.append('    evm list --json --quiet 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(k) for k in d.get(\'data\',{})]" 2>/dev/null')
    lines.append('end')
    lines.append('')

    # Dynamic group name completion helper
    lines.append('function __evm_groups')
    lines.append('    evm groups --json --quiet 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); [print(k) for k in d.get(\'data\',{}).get(\'groups\',{})]" 2>/dev/null')
    lines.append('end')
    lines.append('')

    # Sub-options
    lines.append('# Sub-options')
    lines.append("complete -c evm -n '__fish_seen_subcommand_from set' -l secret -d 'Encrypt value'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from get' -l secret -d 'Decrypt value'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from export' -s f -l format -d 'Format' -xa 'json env sh'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from export' -s o -l output -d 'Output file' -r -F")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from load' -s f -l format -d 'Format' -xa 'json env backup'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from load' -s r -l replace -d 'Replace mode'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from load' -s n -l nest -d 'Nested JSON'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from completion' -xa 'bash zsh fish'")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from history' -s n -l limit -d 'Number of entries' -x")
    lines.append("complete -c evm -n '__fish_seen_subcommand_from schema' -xa 'set get delete validate list'")
    lines.append('')

    # Variable name completion for relevant commands
    lines.append('# Variable name completion')
    for cmd in ['get', 'delete', 'edit', 'expand', 'validate', 'rename', 'copy']:
        lines.append(f"complete -c evm -n '__fish_seen_subcommand_from {cmd}' -a '(__evm_keys)'")
    lines.append('')

    # Group name completion
    lines.append('# Group name completion')
    for cmd in ['setg', 'getg', 'deleteg', 'listg']:
        lines.append(f"complete -c evm -n '__fish_seen_subcommand_from {cmd}' -a '(__evm_groups)'")

    return '\n'.join(lines) + '\n'


SHELL_GENERATORS = {
    'bash': generate_bash_completion,
    'zsh': generate_zsh_completion,
    'fish': generate_fish_completion,
}
