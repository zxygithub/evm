#!/usr/bin/env python3
"""
EVM Shell 补全脚本生成

支持 bash, zsh, fish。
"""


def generate_bash_completion(commands: list) -> str:
    """生成 bash 补全脚本"""
    cmds = ' '.join(commands)
    return f'''# EVM bash completion
_evm_completions() {{
    local cur prev opts
    COMPREPLY=()
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"

    # Top-level commands
    local commands="{cmds}"
    local global_opts="--help --version --verbose --env-file --dry-run --force"

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
        get)
            COMPREPLY=( $(compgen -W "--secret --help" -- "${{cur}}") )
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

    COMPREPLY=( $(compgen -W "${{commands}} ${{global_opts}}" -- "${{cur}}") )
}}
complete -F _evm_completions evm
'''


def generate_zsh_completion(commands: list) -> str:
    """生成 zsh 补全脚本"""
    return f'''#compdef evm

_evm() {{
    local -a commands
    commands=(
        {chr(10).join(f"        '{c}:{c} command'" for c in commands)}
    )

    _arguments -C \\
        '--help[Show help]' \\
        '--version[Show version]' \\
        '(-v --verbose)'{{-v,--verbose}}'[Show detailed info]' \\
        '--env-file[Storage file path]:file:_files' \\
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
    """生成 fish 补全脚本"""
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
    lines.append("complete -c evm -l dry-run -d 'Preview changes'")
    lines.append("complete -c evm -l force -d 'Skip confirmation'")
    lines.append('')

    # Commands
    lines.append('# Commands')
    for cmd in commands:
        lines.append(f"complete -c evm -n '__fish_use_subcommand' -a '{cmd}' -d '{cmd}'")
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

    return '\n'.join(lines) + '\n'


SHELL_GENERATORS = {
    'bash': generate_bash_completion,
    'zsh': generate_zsh_completion,
    'fish': generate_fish_completion,
}
