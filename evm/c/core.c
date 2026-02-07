/**
 * EVM - Environment Variable Manager
 * Core Functions Implementation
 */

#ifdef _WIN32
#include "evm_win.h"
#else
#include "evm.h"
#endif
#include <ctype.h>

/* Initialize environment manager */
void evm_init(EnvManager *mgr, const char *storage_path) {
    memset(mgr, 0, sizeof(EnvManager));
    
    if (storage_path) {
        expand_path(storage_path, mgr->storage_path);
    } else {
        expand_path(DEFAULT_STORAGE, mgr->storage_path);
    }
    
    evm_load(mgr);
}

/* Load environment variables from storage */
bool evm_load(EnvManager *mgr) {
    FILE *fp = fopen(mgr->storage_path, "r");
    if (!fp) {
        /* File doesn't exist yet, that's ok */
        return true;
    }
    
    /* Simple JSON parser */
    char line[MAX_LINE_LEN];
    char content[65536] = {0};
    size_t total = 0;
    
    while (fgets(line, sizeof(line), fp) && total < sizeof(content) - 1) {
        size_t len = strlen(line);
        if (total + len < sizeof(content) - 1) {
            strcat(content, line);
            total += len;
        }
    }
    fclose(fp);
    
    /* Parse JSON content */
    char *p = content;
    while (*p && *p != '{') p++;
    if (*p == '{') p++;
    
    mgr->count = 0;
    
    while (*p && *p != '}' && mgr->count < MAX_VARS) {
        /* Skip whitespace and commas */
        while (*p && (isspace((unsigned char)*p) || *p == ',')) p++;
        if (*p == '}') break;
        
        /* Parse key */
        if (*p == '"') {
            p++;
            char key[MAX_KEY_LEN] = {0};
            size_t k = 0;
            
            while (*p && *p != '"' && k < MAX_KEY_LEN - 1) {
                if (*p == '\\' && *(p + 1)) {
                    p++;
                    switch (*p) {
                        case 'n': key[k++] = '\n'; break;
                        case 't': key[k++] = '\t'; break;
                        case 'r': key[k++] = '\r'; break;
                        case '"': key[k++] = '"'; break;
                        case '\\': key[k++] = '\\'; break;
                        default: key[k++] = *p; break;
                    }
                } else {
                    key[k++] = *p;
                }
                p++;
            }
            if (*p == '"') p++;
            
            /* Skip to colon */
            while (*p && *p != ':') p++;
            if (*p == ':') p++;
            
            /* Skip whitespace */
            while (*p && isspace((unsigned char)*p)) p++;
            
            /* Parse value */
            char value[MAX_VALUE_LEN] = {0};
            size_t v = 0;
            
            if (*p == '"') {
                p++;
                while (*p && *p != '"' && v < MAX_VALUE_LEN - 1) {
                    if (*p == '\\' && *(p + 1)) {
                        p++;
                        switch (*p) {
                            case 'n': value[v++] = '\n'; break;
                            case 't': value[v++] = '\t'; break;
                            case 'r': value[v++] = '\r'; break;
                            case '"': value[v++] = '"'; break;
                            case '\\': value[v++] = '\\'; break;
                            default: value[v++] = *p; break;
                        }
                    } else {
                        value[v++] = *p;
                    }
                    p++;
                }
                if (*p == '"') p++;
            }
            
            /* Store variable */
            strncpy(mgr->vars[mgr->count].key, key, MAX_KEY_LEN - 1);
            strncpy(mgr->vars[mgr->count].value, value, MAX_VALUE_LEN - 1);
            mgr->count++;
        } else {
            p++;
        }
    }
    
    return true;
}

/* Save environment variables to storage */
bool evm_save(EnvManager *mgr) {
    if (!ensure_dir(mgr->storage_path)) {
        fprintf(stderr, "Error: Cannot create directory for %s\n", mgr->storage_path);
        return false;
    }
    
    FILE *fp = fopen(mgr->storage_path, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot write to %s\n", mgr->storage_path);
        return false;
    }
    
    fprintf(fp, "{\n");
    
    for (int i = 0; i < mgr->count; i++) {
        char escaped_key[MAX_KEY_LEN * 2];
        char escaped_value[MAX_VALUE_LEN * 2];
        
        json_escape(mgr->vars[i].key, escaped_key, sizeof(escaped_key));
        json_escape(mgr->vars[i].value, escaped_value, sizeof(escaped_value));
        
        fprintf(fp, "  \"%s\": \"%s\"%s\n",
                escaped_key, escaped_value,
                (i < mgr->count - 1) ? "," : "");
    }
    
    fprintf(fp, "}\n");
    fclose(fp);
    
    return true;
}

/* Set environment variable */
bool evm_set(EnvManager *mgr, const char *key, const char *value) {
    if (!key || !key[0]) {
        fprintf(stderr, "Error: Key cannot be empty\n");
        return false;
    }
    
    /* Check if already exists */
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, key) == 0) {
            strncpy(mgr->vars[i].value, value, MAX_VALUE_LEN - 1);
            printf("Set: %s=%s\n", key, value);
            return evm_save(mgr);
        }
    }
    
    /* Add new variable */
    if (mgr->count >= MAX_VARS) {
        fprintf(stderr, "Error: Maximum number of variables reached\n");
        return false;
    }
    
    strncpy(mgr->vars[mgr->count].key, key, MAX_KEY_LEN - 1);
    strncpy(mgr->vars[mgr->count].value, value, MAX_VALUE_LEN - 1);
    mgr->count++;
    
    printf("Set: %s=%s\n", key, value);
    return evm_save(mgr);
}

/* Get environment variable */
bool evm_get(EnvManager *mgr, const char *key, char *output) {
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, key) == 0) {
            if (output) {
                strcpy(output, mgr->vars[i].value);
            }
            printf("%s\n", mgr->vars[i].value);
            return true;
        }
    }
    
    fprintf(stderr, "Error: Environment variable '%s' not found\n", key);
    return false;
}

/* Delete environment variable */
bool evm_delete(EnvManager *mgr, const char *key) {
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, key) == 0) {
            /* Shift remaining elements */
            for (int j = i; j < mgr->count - 1; j++) {
                mgr->vars[j] = mgr->vars[j + 1];
            }
            mgr->count--;
            printf("Deleted: %s\n", key);
            return evm_save(mgr);
        }
    }
    
    fprintf(stderr, "Error: Environment variable '%s' not found\n", key);
    return false;
}

/* Check if variable exists */
bool evm_exists(EnvManager *mgr, const char *key) {
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, key) == 0) {
            return true;
        }
    }
    return false;
}

/* Clear all environment variables */
void evm_clear(EnvManager *mgr) {
    mgr->count = 0;
    evm_save(mgr);
    printf("All environment variables cleared\n");
}

/* Rename environment variable */
bool evm_rename(EnvManager *mgr, const char *old_key, const char *new_key) {
    if (evm_exists(mgr, new_key)) {
        fprintf(stderr, "Error: Environment variable '%s' already exists\n", new_key);
        return false;
    }
    
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, old_key) == 0) {
            strncpy(mgr->vars[i].key, new_key, MAX_KEY_LEN - 1);
            printf("Renamed: %s -> %s\n", old_key, new_key);
            return evm_save(mgr);
        }
    }
    
    fprintf(stderr, "Error: Environment variable '%s' not found\n", old_key);
    return false;
}

/* Copy environment variable */
bool evm_copy(EnvManager *mgr, const char *src_key, const char *dst_key) {
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, src_key) == 0) {
            return evm_set(mgr, dst_key, mgr->vars[i].value);
        }
    }
    
    fprintf(stderr, "Error: Environment variable '%s' not found\n", src_key);
    return false;
}

/* Execute command with environment variables */
bool evm_execute(EnvManager *mgr, char **args, int argc) {
    if (argc == 0) {
        fprintf(stderr, "Error: No command specified\n");
        return false;
    }
    
    /* Set environment variables */
    for (int i = 0; i < mgr->count; i++) {
#ifdef _WIN32
        SetEnvironmentVariable(mgr->vars[i].key, mgr->vars[i].value);
#else
        setenv(mgr->vars[i].key, mgr->vars[i].value, 1);
#endif
    }
    
    /* Execute command */
    execvp(args[0], args);
    
    /* If we get here, exec failed */
    fprintf(stderr, "Error: Command not found: %s\n", args[0]);
    return false;
}
