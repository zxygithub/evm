/**
 * EVM - Environment Variable Manager
 * Import/Export and Backup Functions Implementation
 */

#include "evm.h"
#include <ctype.h>

/* External compare function from list.c */
extern int compare_vars(const void *a, const void *b);

/* Export to JSON format */
bool evm_export_json(EnvManager *mgr, const char *filename) {
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot write to %s\n", filename);
        return false;
    }
    
    /* Sort first */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
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
    
    printf("Environment variables exported to: %s\n", filename);
    return true;
}

/* Export to .env format */
bool evm_export_env(EnvManager *mgr, const char *filename) {
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot write to %s\n", filename);
        return false;
    }
    
    /* Sort first */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
    for (int i = 0; i < mgr->count; i++) {
        fprintf(fp, "%s=%s\n", mgr->vars[i].key, mgr->vars[i].value);
    }
    
    fclose(fp);
    printf("Environment variables exported to: %s\n", filename);
    return true;
}

/* Export to shell script format */
bool evm_export_sh(EnvManager *mgr, const char *filename) {
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot write to %s\n", filename);
        return false;
    }
    
    /* Sort first */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
    fprintf(fp, "#!/bin/bash\n\n");
    fprintf(fp, "# EVM Environment Variables Export\n");
    fprintf(fp, "# Generated on: %s\n\n", __DATE__);
    
    for (int i = 0; i < mgr->count; i++) {
        fprintf(fp, "export %s=%s\n", mgr->vars[i].key, mgr->vars[i].value);
    }
    
    fclose(fp);
    chmod(filename, 0755);
    
    printf("Environment variables exported to: %s\n", filename);
    return true;
}

/* Load from JSON file */
bool evm_load_json(EnvManager *mgr, const char *filename, bool replace, const char *group) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error: File not found: %s\n", filename);
        return false;
    }
    
    /* Read entire file */
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    char *content = malloc(size + 1);
    if (!content) {
        fclose(fp);
        fprintf(stderr, "Error: Out of memory\n");
        return false;
    }
    
    fread(content, 1, size, fp);
    content[size] = '\0';
    fclose(fp);
    
    /* Clear existing if replace */
    if (replace) {
        mgr->count = 0;
    }
    
    /* Parse JSON */
    char *p = content;
    while (*p && *p != '{') p++;
    if (*p == '{') p++;
    
    int loaded = 0;
    
    while (*p && *p != '}' && mgr->count < MAX_VARS) {
        while (*p && (isspace((unsigned char)*p) || *p == ',')) p++;
        if (*p == '}') break;
        
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
            
            while (*p && *p != ':') p++;
            if (*p == ':') p++;
            while (*p && isspace((unsigned char)*p)) p++;
            
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
            
            /* Add group prefix if specified */
            char final_key[MAX_KEY_LEN];
            if (group && group[0] && !has_group_prefix(key, group)) {
                snprintf(final_key, sizeof(final_key), "%s:%s", group, key);
            } else {
                strncpy(final_key, key, MAX_KEY_LEN - 1);
            }
            
            /* Check if already exists */
            bool exists = false;
            for (int i = 0; i < mgr->count; i++) {
                if (strcmp(mgr->vars[i].key, final_key) == 0) {
                    strncpy(mgr->vars[i].value, value, MAX_VALUE_LEN - 1);
                    exists = true;
                    break;
                }
            }
            
            if (!exists) {
                strncpy(mgr->vars[mgr->count].key, final_key, MAX_KEY_LEN - 1);
                strncpy(mgr->vars[mgr->count].value, value, MAX_VALUE_LEN - 1);
                mgr->count++;
            }
            
            loaded++;
        } else {
            p++;
        }
    }
    
    free(content);
    
    printf("Loaded %d environment variables from %s\n", loaded, filename);
    if (group && group[0]) {
        printf("Variables added to group '%s'\n", group);
    }
    
    return evm_save(mgr);
}

/* Load from .env file */
bool evm_load_env(EnvManager *mgr, const char *filename, bool replace, const char *group) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error: File not found: %s\n", filename);
        return false;
    }
    
    if (replace) {
        mgr->count = 0;
    }
    
    char line[MAX_LINE_LEN];
    int loaded = 0;
    
    while (fgets(line, sizeof(line), fp) && mgr->count < MAX_VARS) {
        char *trimmed = trim(line);
        
        /* Skip empty lines and comments */
        if (!trimmed[0] || trimmed[0] == '#') continue;
        
        /* Find equals sign */
        char *eq = strchr(trimmed, '=');
        if (!eq) continue;
        
        *eq = '\0';
        char *key = trim(trimmed);
        char *value = trim(eq + 1);
        
        /* Remove quotes */
        size_t val_len = strlen(value);
        if (val_len >= 2) {
            if ((value[0] == '"' && value[val_len - 1] == '"') ||
                (value[0] == '\'' && value[val_len - 1] == '\'')) {
                value[val_len - 1] = '\0';
                value++;
            }
        }
        
        /* Add group prefix if specified */
        char final_key[MAX_KEY_LEN];
        if (group && group[0] && !has_group_prefix(key, group)) {
            snprintf(final_key, sizeof(final_key), "%s:%s", group, key);
        } else {
            strncpy(final_key, key, MAX_KEY_LEN - 1);
        }
        
        /* Check if already exists */
        bool exists = false;
        for (int i = 0; i < mgr->count; i++) {
            if (strcmp(mgr->vars[i].key, final_key) == 0) {
                strncpy(mgr->vars[i].value, value, MAX_VALUE_LEN - 1);
                exists = true;
                break;
            }
        }
        
        if (!exists) {
            strncpy(mgr->vars[mgr->count].key, final_key, MAX_KEY_LEN - 1);
            strncpy(mgr->vars[mgr->count].value, value, MAX_VALUE_LEN - 1);
            mgr->count++;
        }
        
        loaded++;
    }
    
    fclose(fp);
    
    printf("Loaded %d environment variables from %s\n", loaded, filename);
    if (group && group[0]) {
        printf("Variables added to group '%s'\n", group);
    }
    
    return evm_save(mgr);
}

/* Create backup */
bool evm_backup(EnvManager *mgr, const char *filename) {
    FILE *fp = fopen(filename, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot write to %s\n", filename);
        return false;
    }
    
    /* Get current timestamp */
    time_t now = time(NULL);
    struct tm *tm_info = localtime(&now);
    char timestamp[64];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%S", tm_info);
    
    fprintf(fp, "{\n");
    fprintf(fp, "  \"timestamp\": \"%s\",\n", timestamp);
    fprintf(fp, "  \"variables\": {\n");
    
    /* Sort first */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
    for (int i = 0; i < mgr->count; i++) {
        char escaped_key[MAX_KEY_LEN * 2];
        char escaped_value[MAX_VALUE_LEN * 2];
        
        json_escape(mgr->vars[i].key, escaped_key, sizeof(escaped_key));
        json_escape(mgr->vars[i].value, escaped_value, sizeof(escaped_value));
        
        fprintf(fp, "    \"%s\": \"%s\"%s\n",
                escaped_key, escaped_value,
                (i < mgr->count - 1) ? "," : "");
    }
    
    fprintf(fp, "  }\n");
    fprintf(fp, "}\n");
    fclose(fp);
    
    printf("Backup created: %s\n", filename);
    return true;
}

/* Restore from backup */
bool evm_restore(EnvManager *mgr, const char *filename, bool merge) {
    FILE *fp = fopen(filename, "r");
    if (!fp) {
        fprintf(stderr, "Error: Backup file not found: %s\n", filename);
        return false;
    }
    
    /* Read entire file */
    fseek(fp, 0, SEEK_END);
    long size = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    
    char *content = malloc(size + 1);
    if (!content) {
        fclose(fp);
        fprintf(stderr, "Error: Out of memory\n");
        return false;
    }
    
    fread(content, 1, size, fp);
    content[size] = '\0';
    fclose(fp);
    
    /* Check if it's a backup format with variables field */
    bool is_backup = strstr(content, "\"variables\"") != NULL;
    
    if (!is_backup) {
        /* Treat as regular JSON */
        free(content);
        return evm_load_json(mgr, filename, !merge, NULL);
    }
    
    /* Parse backup format */
    if (!merge) {
        mgr->count = 0;
    }
    
    /* Find variables section */
    char *vars_start = strstr(content, "\"variables\"");
    if (!vars_start) {
        free(content);
        fprintf(stderr, "Error: Invalid backup format\n");
        return false;
    }
    
    /* Find timestamp */
    char *ts_start = strstr(content, "\"timestamp\"");
    char timestamp[64] = "unknown";
    if (ts_start) {
        char *ts_val = strchr(ts_start, '"');
        if (ts_val) {
            ts_val = strchr(ts_val + 1, '"');
            if (ts_val) {
                ts_val++;
                char *ts_end = strchr(ts_val, '"');
                if (ts_end) {
                    size_t len = ts_end - ts_val;
                    if (len < sizeof(timestamp)) {
                        strncpy(timestamp, ts_val, len);
                        timestamp[len] = '\0';
                    }
                }
            }
        }
    }
    
    /* Find opening brace of variables */
    char *p = strchr(vars_start, '{');
    if (!p) {
        free(content);
        fprintf(stderr, "Error: Invalid backup format\n");
        return false;
    }
    p++;
    
    int restored = 0;
    
    while (*p && *p != '}' && mgr->count < MAX_VARS) {
        while (*p && (isspace((unsigned char)*p) || *p == ',')) p++;
        if (*p == '}') break;
        
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
            
            while (*p && *p != ':') p++;
            if (*p == ':') p++;
            while (*p && isspace((unsigned char)*p)) p++;
            
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
            
            /* Check if already exists */
            bool exists = false;
            for (int i = 0; i < mgr->count; i++) {
                if (strcmp(mgr->vars[i].key, key) == 0) {
                    strncpy(mgr->vars[i].value, value, MAX_VALUE_LEN - 1);
                    exists = true;
                    break;
                }
            }
            
            if (!exists) {
                strncpy(mgr->vars[mgr->count].key, key, MAX_KEY_LEN - 1);
                strncpy(mgr->vars[mgr->count].value, value, MAX_VALUE_LEN - 1);
                mgr->count++;
            }
            
            restored++;
        } else {
            p++;
        }
    }
    
    free(content);
    
    printf("%s %d variables from backup\n", merge ? "Merged" : "Restored", restored);
    printf("Backup timestamp: %s\n", timestamp);
    
    return evm_save(mgr);
}

/* External compare function for sorting */
int compare_vars(const void *a, const void *b);
