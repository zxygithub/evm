#!/usr/bin/env python3
"""Tests for EVM (Environment Variable Manager)."""

import os
import sys
import json
import tempfile
import unittest
import shutil
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evm.python.main import EnvironmentManager  # noqa: E402


class TestEnvironmentManager(unittest.TestCase):
    """Test cases for EnvironmentManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, 'test_env.json')
        self.manager = EnvironmentManager(self.env_file)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_init_creates_directory(self):
        """Test that initialization creates the directory."""
        self.assertTrue(os.path.exists(os.path.dirname(self.env_file)))

    def test_set_and_get_variable(self):
        """Test setting and getting an environment variable."""
        self.manager.set('TEST_KEY', 'test_value')
        self.assertEqual(self.manager.get('TEST_KEY'), 'test_value')

    def test_get_nonexistent_variable(self):
        """Test getting a nonexistent variable."""
        with patch('sys.stdout'):
            with self.assertRaises(SystemExit):
                self.manager.get('NONEXISTENT_KEY')

    def test_delete_variable(self):
        """Test deleting an environment variable."""
        self.manager.set('TO_DELETE', 'value')
        self.manager.delete('TO_DELETE')
        with patch('sys.stdout'):
            with self.assertRaises(SystemExit):
                self.manager.get('TO_DELETE')

    def test_delete_nonexistent_variable(self):
        """Test deleting a nonexistent variable."""
        with patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                self.manager.delete('NONEXISTENT_KEY')

    def test_list_variables(self):
        """Test listing all variables."""
        self.manager.set('KEY1', 'value1')
        self.manager.set('KEY2', 'value2')
        self.manager.set('KEY3', 'value3')

        with patch('sys.stdout'):
            self.manager.list()

        # Check that variables are saved
        self.assertEqual(len(self.manager._env_vars), 3)

    def test_list_with_pattern(self):
        """Test listing variables with a pattern filter."""
        self.manager.set('API_KEY', '123')
        self.manager.set('API_URL', 'http://example.com')
        self.manager.set('DB_HOST', 'localhost')

        with patch('sys.stdout'):
            self.manager.list('API')

        # Pattern filtering should work
        filtered = {k: v for k, v in self.manager._env_vars.items()
                    if 'api'.lower() in k.lower()}
        self.assertEqual(len(filtered), 2)

    def test_clear_variables(self):
        """Test clearing all variables."""
        self.manager.set('KEY1', 'value1')
        self.manager.set('KEY2', 'value2')
        self.manager.clear()

        self.assertEqual(len(self.manager._env_vars), 0)

    def test_export_json(self):
        """Test exporting to JSON format."""
        self.manager.set('KEY1', 'value1')
        self.manager.set('KEY2', 'value2')

        export_file = os.path.join(self.temp_dir, 'export.json')
        with patch('sys.stdout'):
            self.manager.export('json', export_file)

        self.assertTrue(os.path.exists(export_file))
        with open(export_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(data['KEY1'], 'value1')
        self.assertEqual(data['KEY2'], 'value2')

    def test_export_env(self):
        """Test exporting to .env format."""
        self.manager.set('KEY1', 'value1')
        export_file = os.path.join(self.temp_dir, 'export.env')
        with patch('sys.stdout'):
            self.manager.export('env', export_file)

        self.assertTrue(os.path.exists(export_file))
        with open(export_file, 'r') as f:
            content = f.read()
        self.assertIn('KEY1=value1', content)

    def test_export_sh(self):
        """Test exporting to shell script format."""
        self.manager.set('KEY1', 'value1')
        export_file = os.path.join(self.temp_dir, 'export.sh')
        with patch('sys.stdout'):
            self.manager.export('sh', export_file)

        self.assertTrue(os.path.exists(export_file))
        with open(export_file, 'r') as f:
            content = f.read()
        self.assertIn('#!/bin/bash', content)
        self.assertIn('export KEY1=value1', content)

    def test_load_json(self):
        """Test loading from JSON file."""
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'IMPORT_KEY': 'import_value'}, f)

        with patch('sys.stdout'):
            self.manager.load(import_file)

        self.assertEqual(self.manager._env_vars['IMPORT_KEY'], 'import_value')

    def test_load_env(self):
        """Test loading from .env file."""
        import_file = os.path.join(self.temp_dir, 'import.env')
        with open(import_file, 'w') as f:
            f.write('IMPORT_KEY="import_value"\n')
            f.write('# Comment line\n')
            f.write('KEY2="value2"\n')

        with patch('sys.stdout'):
            self.manager.load(import_file)

        self.assertEqual(self.manager._env_vars['IMPORT_KEY'], 'import_value')
        self.assertEqual(self.manager._env_vars['KEY2'], 'value2')

    def test_rename_variable(self):
        """Test renaming an environment variable."""
        self.manager.set('OLD_KEY', 'value')
        self.manager.rename('OLD_KEY', 'NEW_KEY')

        self.assertNotIn('OLD_KEY', self.manager._env_vars)
        self.assertIn('NEW_KEY', self.manager._env_vars)
        self.assertEqual(self.manager._env_vars['NEW_KEY'], 'value')

    def test_rename_nonexistent(self):
        """Test renaming a nonexistent variable."""
        with patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                self.manager.rename('NONEXISTENT', 'NEW_KEY')

    def test_copy_variable(self):
        """Test copying an environment variable."""
        self.manager.set('SRC_KEY', 'value')
        self.manager.copy('SRC_KEY', 'DST_KEY')

        self.assertIn('SRC_KEY', self.manager._env_vars)
        self.assertIn('DST_KEY', self.manager._env_vars)
        self.assertEqual(self.manager._env_vars['DST_KEY'], 'value')

    def test_search_by_key(self):
        """Test searching variables by key."""
        self.manager.set('API_KEY', '123')
        self.manager.set('API_URL', 'http://example.com')
        self.manager.set('DB_HOST', 'localhost')

        with patch('sys.stdout'):
            self.manager.search('api')

    def test_search_by_value(self):
        """Test searching variables by value."""
        self.manager.set('KEY1', 'api_value')
        self.manager.set('KEY2', 'test_value')
        self.manager.set('KEY3', 'another_value')

        with patch('sys.stdout'):
            self.manager.search('value', search_value=True)

    def test_backup(self):
        """Test creating a backup."""
        self.manager.set('KEY1', 'value1')
        backup_file = os.path.join(self.temp_dir, 'backup.json')

        with patch('sys.stdout'):
            self.manager.backup(backup_file)

        self.assertTrue(os.path.exists(backup_file))
        with open(backup_file, 'r') as f:
            data = json.load(f)
        self.assertIn('variables', data)
        self.assertIn('timestamp', data)

    def test_restore_replace(self):
        """Test restoring from backup (replace mode)."""
        # Set up initial state
        self.manager.set('KEY1', 'value1')

        # Create backup
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        with patch('sys.stdout'):
            self.manager.backup(backup_file)

        # Modify current state
        self.manager.set('KEY2', 'value2')

        # Restore (should replace)
        with patch('sys.stdout'):
            self.manager.restore(backup_file, merge=False)

        self.assertIn('KEY1', self.manager._env_vars)
        self.assertNotIn('KEY2', self.manager._env_vars)

    def test_restore_merge(self):
        """Test restoring from backup (merge mode)."""
        # Set up initial state
        self.manager.set('KEY1', 'value1')

        # Create backup
        backup_file = os.path.join(self.temp_dir, 'backup.json')
        with patch('sys.stdout'):
            self.manager.backup(backup_file)

        # Modify current state
        self.manager.set('KEY2', 'value2')

        # Restore (should merge)
        with patch('sys.stdout'):
            self.manager.restore(backup_file, merge=True)

        self.assertIn('KEY1', self.manager._env_vars)
        self.assertIn('KEY2', self.manager._env_vars)

    # Group/namespace tests
    def test_set_grouped_variable(self):
        """Test setting a variable in a group."""
        self.manager.set_grouped('dev', 'DATABASE_URL', 'localhost')
        self.assertIn('dev:DATABASE_URL', self.manager._env_vars)
        self.assertEqual(
            self.manager._env_vars['dev:DATABASE_URL'], 'localhost'
        )

    def test_get_grouped_variable(self):
        """Test getting a variable from a group."""
        self.manager.set_grouped('dev', 'KEY', 'value')
        with patch('sys.stdout'):
            result = self.manager.get_grouped('dev', 'KEY')
        self.assertEqual(result, 'value')

    def test_delete_grouped_variable(self):
        """Test deleting a variable from a group."""
        self.manager.set_grouped('dev', 'KEY', 'value')
        with patch('sys.stdout'):
            self.manager.delete_grouped('dev', 'KEY')
        self.assertNotIn('dev:KEY', self.manager._env_vars)

    def test_list_groups(self):
        """Test listing all groups."""
        self.manager.set_grouped('dev', 'KEY1', 'value1')
        self.manager.set_grouped('dev', 'KEY2', 'value2')
        self.manager.set_grouped('prod', 'KEY3', 'value3')

        with patch('sys.stdout'):
            self.manager.list_groups()

    def test_list_group_variables(self):
        """Test listing variables in a specific group."""
        self.manager.set_grouped('dev', 'KEY1', 'value1')
        self.manager.set_grouped('dev', 'KEY2', 'value2')
        self.manager.set_grouped('prod', 'KEY3', 'value3')

        with patch('sys.stdout'):
            self.manager.list(group='dev')

        # Should have 2 dev variables
        dev_vars = {k: v for k, v in self.manager._env_vars.items()
                    if k.startswith('dev:')}
        self.assertEqual(len(dev_vars), 2)

    def test_list_with_show_groups(self):
        """Test listing variables grouped by namespace."""
        self.manager.set_grouped('dev', 'KEY1', 'value1')
        self.manager.set_grouped('prod', 'KEY2', 'value2')
        self.manager.set('KEY3', 'value3')

        with patch('sys.stdout'):
            self.manager.list(show_groups=True)

    def test_delete_group(self):
        """Test deleting an entire group."""
        self.manager.set_grouped('dev', 'KEY1', 'value1')
        self.manager.set_grouped('dev', 'KEY2', 'value2')
        self.manager.set_grouped('prod', 'KEY3', 'value3')

        with patch('sys.stdout'):
            self.manager.delete_group('dev')

        self.assertNotIn('dev:KEY1', self.manager._env_vars)
        self.assertNotIn('dev:KEY2', self.manager._env_vars)
        self.assertIn('prod:KEY3', self.manager._env_vars)

    def test_delete_default_group(self):
        """Test that deleting default group is not allowed."""
        with patch('sys.stderr'):
            with self.assertRaises(SystemExit):
                self.manager.delete_group('default')

    def test_move_to_group(self):
        """Test moving a variable to a group."""
        self.manager.set('KEY1', 'value1')

        with patch('sys.stdout'):
            self.manager.move_to_group('KEY1', 'dev')

        self.assertNotIn('KEY1', self.manager._env_vars)
        self.assertIn('dev:KEY1', self.manager._env_vars)
        self.assertEqual(self.manager._env_vars['dev:KEY1'], 'value1')

    def test_mixed_variables(self):
        """Test mixing grouped and non-grouped variables."""
        self.manager.set('GLOBAL_KEY', 'global_value')
        self.manager.set_grouped('dev', 'KEY1', 'dev_value')
        self.manager.set_grouped('prod', 'KEY2', 'prod_value')

        with patch('sys.stdout'):
            self.manager.list(show_groups=True)

        self.assertEqual(len(self.manager._env_vars), 3)

    # Enhanced load tests
    def test_load_with_format_json(self):
        """Test loading with explicit format specified."""
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'KEY1': 'value1', 'KEY2': 'value2'}, f)

        with patch('sys.stdout'):
            self.manager.load(import_file, format_type='json')

        self.assertEqual(self.manager._env_vars['KEY1'], 'value1')
        self.assertEqual(self.manager._env_vars['KEY2'], 'value2')

    def test_load_with_format_env(self):
        """Test loading .env file with explicit format."""
        import_file = os.path.join(self.temp_dir, 'import.txt')
        with open(import_file, 'w') as f:
            f.write('KEY1="value1"\nKEY2="value2"\n')

        with patch('sys.stdout'):
            self.manager.load(import_file, format_type='env')

        self.assertEqual(self.manager._env_vars['KEY1'], 'value1')
        self.assertEqual(self.manager._env_vars['KEY2'], 'value2')

    def test_load_replace_mode(self):
        """Test loading in replace mode."""
        # Set initial variables
        self.manager.set('OLD_KEY', 'old_value')

        # Create import file
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'NEW_KEY': 'new_value'}, f)

        # Load with replace mode
        with patch('sys.stdout'):
            self.manager.load(import_file, replace=True)

        self.assertNotIn('OLD_KEY', self.manager._env_vars)
        self.assertIn('NEW_KEY', self.manager._env_vars)

    def test_load_merge_mode(self):
        """Test loading in merge mode (default)."""
        # Set initial variables
        self.manager.set('OLD_KEY', 'old_value')

        # Create import file
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'NEW_KEY': 'new_value'}, f)

        # Load with merge mode
        with patch('sys.stdout'):
            self.manager.load(import_file, replace=False)

        self.assertIn('OLD_KEY', self.manager._env_vars)
        self.assertIn('NEW_KEY', self.manager._env_vars)

    def test_load_with_group(self):
        """Test loading variables into a specific group."""
        import_file = os.path.join(self.temp_dir, 'import.json')
        with open(import_file, 'w') as f:
            json.dump({'KEY1': 'value1', 'KEY2': 'value2'}, f)

        with patch('sys.stdout'):
            self.manager.load(import_file, group='dev')

        self.assertIn('dev:KEY1', self.manager._env_vars)
        self.assertIn('dev:KEY2', self.manager._env_vars)

    def test_load_backup_file(self):
        """Test loading a backup file."""
        # Create a backup-like file
        import_file = os.path.join(self.temp_dir, 'backup.json')
        backup_data = {
            'timestamp': '2024-01-01T00:00:00',
            'variables': {'KEY1': 'value1', 'KEY2': 'value2'}
        }
        with open(import_file, 'w') as f:
            json.dump(backup_data, f)

        with patch('sys.stdout'):
            self.manager.load(import_file, format_type='backup')

        self.assertIn('KEY1', self.manager._env_vars)
        self.assertIn('KEY2', self.manager._env_vars)

    def test_load_auto_detect_json(self):
        """Test auto-detection of JSON format."""
        import_file = os.path.join(self.temp_dir, 'config')
        with open(import_file, 'w') as f:
            json.dump({'KEY1': 'value1'}, f)

        with patch('sys.stdout'):
            self.manager.load(import_file, format_type=None)

        self.assertEqual(self.manager._env_vars['KEY1'], 'value1')

    def test_load_auto_detect_env(self):
        """Test auto-detection of .env format."""
        import_file = os.path.join(self.temp_dir, 'config')
        with open(import_file, 'w') as f:
            f.write('KEY1="value1"\n')

        with patch('sys.stdout'):
            self.manager.load(import_file, format_type=None)

        self.assertEqual(self.manager._env_vars['KEY1'], 'value1')


if __name__ == '__main__':
    unittest.main()
