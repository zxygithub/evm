/**
 * EVM - Environment Variable Manager
 * C Language Implementation Header File
 * Version: 1.5.0
 */

#ifndef EVM_H
#define EVM_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <time.h>
#include <sys/stat.h>
#include <unistd.h>
#include <dirent.h>

#define EVM_VERSION "1.5.0"
#define MAX_KEY_LEN 256
#define MAX_VALUE_LEN 4096
#define MAX_LINE_LEN 8192
#define MAX_VARS 10000
#define DEFAULT_STORAGE "~/.evm/env.json"

/* Environment variable structure */
typedef struct {
    char key[MAX_KEY_LEN];
    char value[MAX_VALUE_LEN];
} EnvVar;

/* Environment manager structure */
typedef struct {
    EnvVar vars[MAX_VARS];
    int count;
    char storage_path[1024];
} EnvManager;

/* Core functions */
void evm_init(EnvManager *mgr, const char *storage_path);
bool evm_load(EnvManager *mgr);
bool evm_save(EnvManager *mgr);

/* Variable operations */
bool evm_set(EnvManager *mgr, const char *key, const char *value);
bool evm_get(EnvManager *mgr, const char *key, char *output);
bool evm_delete(EnvManager *mgr, const char *key);
bool evm_exists(EnvManager *mgr, const char *key);

/* List and search */
void evm_list(EnvManager *mgr, const char *pattern, bool show_groups);
void evm_list_group(EnvManager *mgr, const char *group, bool no_prefix);
void evm_search(EnvManager *mgr, const char *pattern, bool search_value);
void evm_list_groups(EnvManager *mgr);

/* Import/Export */
bool evm_export_json(EnvManager *mgr, const char *filename);
bool evm_export_env(EnvManager *mgr, const char *filename);
bool evm_export_sh(EnvManager *mgr, const char *filename);
bool evm_load_json(EnvManager *mgr, const char *filename, bool replace, const char *group);
bool evm_load_env(EnvManager *mgr, const char *filename, bool replace, const char *group);

/* Backup and restore */
bool evm_backup(EnvManager *mgr, const char *filename);
bool evm_restore(EnvManager *mgr, const char *filename, bool merge);

/* Group operations */
bool evm_set_grouped(EnvManager *mgr, const char *group, const char *key, const char *value);
bool evm_get_grouped(EnvManager *mgr, const char *group, const char *key, char *output);
bool evm_delete_grouped(EnvManager *mgr, const char *group, const char *key);
bool evm_delete_group(EnvManager *mgr, const char *group);
bool evm_move_to_group(EnvManager *mgr, const char *key, const char *group);

/* Utility functions */
bool evm_rename(EnvManager *mgr, const char *old_key, const char *new_key);
bool evm_copy(EnvManager *mgr, const char *src_key, const char *dst_key);
void evm_clear(EnvManager *mgr);
bool evm_execute(EnvManager *mgr, char **args, int argc);

/* String utilities */
void expand_path(const char *path, char *expanded);
bool ensure_dir(const char *path);
char *trim(char *str);
bool has_group_prefix(const char *key, const char *group);
void extract_group(const char *key, char *group, char *name);

/* JSON utilities */
char *json_escape(const char *str, char *output, size_t outlen);
char *json_unescape(const char *str, char *output, size_t outlen);

/* External compare function for sorting */
int compare_vars(const void *a, const void *b);

#endif /* EVM_H */
