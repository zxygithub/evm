/**
 * EVM - Environment Variable Manager
 * Group Management Functions Implementation
 */

#ifdef _WIN32
#include "evm_win.h"
#else
#include "evm.h"
#endif

/* Set variable in specific group */
bool evm_set_grouped(EnvManager *mgr, const char *group, const char *key, const char *value) {
    if (!group || !group[0]) {
        return evm_set(mgr, key, value);
    }
    
    char full_key[MAX_KEY_LEN];
    snprintf(full_key, sizeof(full_key), "%s:%s", group, key);
    
    return evm_set(mgr, full_key, value);
}

/* Get variable from specific group */
bool evm_get_grouped(EnvManager *mgr, const char *group, const char *key, char *output) {
    if (!group || !group[0]) {
        return evm_get(mgr, key, output);
    }
    
    char full_key[MAX_KEY_LEN];
    snprintf(full_key, sizeof(full_key), "%s:%s", group, key);
    
    /* Try with group prefix first */
    if (evm_get(mgr, full_key, output)) {
        return true;
    }
    
    /* Fall back to key without prefix */
    return evm_get(mgr, key, output);
}

/* Delete variable from specific group */
bool evm_delete_grouped(EnvManager *mgr, const char *group, const char *key) {
    if (!group || !group[0]) {
        return evm_delete(mgr, key);
    }
    
    char full_key[MAX_KEY_LEN];
    snprintf(full_key, sizeof(full_key), "%s:%s", group, key);
    
    return evm_delete(mgr, full_key);
}

/* Delete entire group */
bool evm_delete_group(EnvManager *mgr, const char *group) {
    if (!group || !group[0]) {
        fprintf(stderr, "Error: Group name cannot be empty\n");
        return false;
    }
    
    if (strcmp(group, "default") == 0) {
        fprintf(stderr, "Error: Cannot delete default namespace. Use 'clear' to remove all variables.\n");
        return false;
    }
    
    char prefix[MAX_KEY_LEN];
    snprintf(prefix, sizeof(prefix), "%s:", group);
    size_t prefix_len = strlen(prefix);
    
    /* Count variables to delete */
    int to_delete = 0;
    for (int i = 0; i < mgr->count; i++) {
        if (strncmp(mgr->vars[i].key, prefix, prefix_len) == 0) {
            to_delete++;
        }
    }
    
    if (to_delete == 0) {
        fprintf(stderr, "Error: Group '%s' not found or has no variables\n", group);
        return false;
    }
    
    /* Remove variables */
    int new_count = 0;
    for (int i = 0; i < mgr->count; i++) {
        if (strncmp(mgr->vars[i].key, prefix, prefix_len) != 0) {
            mgr->vars[new_count] = mgr->vars[i];
            new_count++;
        }
    }
    
    mgr->count = new_count;
    printf("Deleted group '%s' and all its variables (%d total)\n", group, to_delete);
    
    return evm_save(mgr);
}

/* Move variable to different group */
bool evm_move_to_group(EnvManager *mgr, const char *key, const char *group) {
    if (!key || !key[0]) {
        fprintf(stderr, "Error: Key cannot be empty\n");
        return false;
    }
    
    /* Find the variable */
    int idx = -1;
    for (int i = 0; i < mgr->count; i++) {
        if (strcmp(mgr->vars[i].key, key) == 0) {
            idx = i;
            break;
        }
    }
    
    if (idx < 0) {
        fprintf(stderr, "Error: Environment variable '%s' not found\n", key);
        return false;
    }
    
    /* Extract current name without group */
    char current_group[MAX_KEY_LEN], name[MAX_KEY_LEN];
    extract_group(key, current_group, name);
    
    /* Create new key */
    char new_key[MAX_KEY_LEN];
    if (group && group[0]) {
        snprintf(new_key, sizeof(new_key), "%s:%s", group, name);
    } else {
        strcpy(new_key, name);
    }
    
    /* Check if new key already exists */
    if (strcmp(key, new_key) != 0 && evm_exists(mgr, new_key)) {
        fprintf(stderr, "Error: Environment variable '%s' already exists\n", new_key);
        return false;
    }
    
    /* Rename */
    strncpy(mgr->vars[idx].key, new_key, MAX_KEY_LEN - 1);
    printf("Moved: %s -> %s\n", key, new_key);
    
    return evm_save(mgr);
}
