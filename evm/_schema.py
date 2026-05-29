#!/usr/bin/env python3
"""
EVM Schema Mixin

变量 schema 定义和校验功能。
支持格式：url, email, port, integer, boolean, path, ipv4, ipv6
"""

import ipaddress
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

from .exceptions import SchemaError


# 内置格式校验正则
FORMAT_PATTERNS = {
    'url': re.compile(
        r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE
    ),
    'email': re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    ),
    'port': re.compile(r'^[0-9]{1,5}$'),
    'integer': re.compile(r'^-?[0-9]+$'),
    'boolean': re.compile(r'^(true|false|yes|no|1|0)$', re.IGNORECASE),
    'path': re.compile(r'^[/~.].*|^[a-zA-Z]:\\.*'),
    'ipv4': re.compile(
        r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'
    ),
}

# 环境变量 key 名校验正则
VALID_KEY_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*(?::[A-Za-z_][A-Za-z0-9_]*)*$')


def validate_ipv6(value: str) -> bool:
    """#7: 使用标准库 ipaddress 校验 IPv6 地址"""
    try:
        ipaddress.IPv6Address(value)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


class SchemaMixin:
    """Schema mixin — 变量格式定义和校验"""

    def _get_schema_file(self) -> Path:
        """获取 schema 文件路径"""
        return self.env_file.parent / 'schema.json'

    def _load_schema(self) -> Dict:
        """加载 schema 定义

        #10: 损坏时打印警告到 stderr，而非静默丢弃。
        """
        schema_file = self._get_schema_file()
        if not schema_file.exists():
            return {}
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(
                f"Warning: Schema file is corrupted ({e}). "
                f"All schema definitions will be ignored until fixed.",
                file=sys.stderr,
            )
            return {}
        except OSError as e:
            print(
                f"Warning: Cannot read schema file ({e}). "
                f"All schema definitions will be ignored.",
                file=sys.stderr,
            )
            return {}

    def _save_schema(self, schema: Dict) -> None:
        """保存 schema 定义"""
        schema_file = self._get_schema_file()
        try:
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=2, ensure_ascii=False)
            os.chmod(str(schema_file), 0o600)
        except OSError as e:
            raise SchemaError(f"Failed to save schema: {e}")

    def set_schema(
        self,
        key: str,
        format: Optional[str] = None,
        required: Optional[bool] = None,
        pattern: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """为变量设置 schema 定义

        Args:
            key: 变量名
            format: 内置格式 (url/email/port/integer/boolean/path/ipv4/ipv6)
            required: 是否必填
            pattern: 自定义正则
            description: 描述

        Returns:
            确认消息
        """
        available_formats = list(FORMAT_PATTERNS.keys()) + ['ipv6']
        if format and format not in available_formats:
            raise SchemaError(
                f"Unknown format '{format}'. "
                f"Available: {', '.join(sorted(available_formats))}",
                key,
            )

        schema = self._load_schema()
        entry = schema.get(key, {})

        if format is not None:
            entry['format'] = format
        if required is not None:
            entry['required'] = required
        if pattern is not None:
            # 验证正则是否合法
            try:
                re.compile(pattern)
            except re.error as e:
                raise SchemaError(f"Invalid regex pattern: {e}", key)
            entry['pattern'] = pattern
        if description is not None:
            entry['description'] = description

        if not entry:
            raise SchemaError("No schema properties specified", key)

        schema[key] = entry
        self._save_schema(schema)
        return f"Schema set for '{key}': {json.dumps(entry, ensure_ascii=False)}"

    def get_schema(self, key: Optional[str] = None) -> Dict:
        """获取 schema 定义

        Args:
            key: 指定变量名（None 返回全部）
        """
        schema = self._load_schema()
        if key is not None:
            if key not in schema:
                raise SchemaError(f"No schema defined for '{key}'", key)
            return {key: schema[key]}
        return schema

    def delete_schema(self, key: str) -> str:
        """删除变量的 schema 定义"""
        schema = self._load_schema()
        if key not in schema:
            raise SchemaError(f"No schema defined for '{key}'", key)
        del schema[key]
        self._save_schema(schema)
        return f"Schema removed for '{key}'"

    def validate(
        self, key: str, value: Optional[str] = None
    ) -> Dict:
        """校验变量值是否符合 schema

        Args:
            key: 变量名
            value: 待校验值（None 则使用当前存储的值）

        Returns:
            {'valid': bool, 'errors': [...], 'warnings': [...]}
        """
        schema = self._load_schema()
        if key not in schema:
            raise SchemaError(f"No schema defined for '{key}'", key)

        if value is None:
            if key not in self._env_vars:
                entry = schema[key]
                if entry.get('required', False):
                    return {
                        'valid': False,
                        'errors': [f"Required variable '{key}' is not set"],
                        'warnings': [],
                    }
                return {
                    'valid': True, 'errors': [],
                    'warnings': ['Variable not set (not required)'],
                }
            value = self._env_vars[key]

        return self._validate_value(key, str(value), schema[key])

    def validate_all(self) -> Dict[str, Dict]:
        """校验所有有 schema 定义的变量"""
        schema = self._load_schema()
        results = {}

        for key, entry in schema.items():
            if key in self._env_vars:
                results[key] = self._validate_value(
                    key, str(self._env_vars[key]), entry
                )
            elif entry.get('required', False):
                results[key] = {
                    'valid': False,
                    'errors': [f"Required variable '{key}' is not set"],
                    'warnings': [],
                }
            else:
                results[key] = {
                    'valid': True,
                    'errors': [],
                    'warnings': ['Variable not set (not required)'],
                }

        return results

    def _validate_value(
        self, key: str, value: str, entry: Dict
    ) -> Dict:
        """内部：校验单个值"""
        errors = []
        warnings = []

        # 格式校验
        fmt = entry.get('format')
        if fmt == 'ipv6':
            # #7: 使用 ipaddress 标准库校验
            if not validate_ipv6(value):
                errors.append(
                    f"Value '{value}' does not match format 'ipv6'"
                )
        elif fmt and fmt in FORMAT_PATTERNS:
            if not FORMAT_PATTERNS[fmt].match(value):
                errors.append(
                    f"Value '{value}' does not match format '{fmt}'"
                )

        # 自定义正则校验
        pattern = entry.get('pattern')
        if pattern:
            try:
                if not re.match(pattern, value):
                    errors.append(
                        f"Value '{value}' does not match pattern '{pattern}'"
                    )
            except re.error:
                errors.append(f"Invalid schema regex: '{pattern}'")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
        }
