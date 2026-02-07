/**
 * EVM - Environment Variable Manager
 * List and Search Functions Implementation
 */

#include "evm.h"
#include <ctype.h>

/* Compare function for sorting */
int compare_vars(const void *a, const void *b) {
    const EnvVar *va = (const EnvVar *)a;
    const EnvVar *vb = (const EnvVar *)b;
    return strcmp(va->key, vb->key);
}

/* List all environment variables */
void evm_list(EnvManager *mgr, const char *pattern, bool show_groups) {
    if (mgr->count == 0) {
        printf("No environment variables set\n");
        return;
    }
    
    /* Sort variables */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
    if (show_groups) {
        /* Group by namespace */
        printf("\nEnvironment Variables (by group):\n");
        printf("======================================================================\n");
        
        char current_group[MAX_KEY_LEN] = "";
        bool first_group = true;
        
        for (int i = 0; i < mgr->count; i++) {
            char group[MAX_KEY_LEN], name[MAX_KEY_LEN];
            extract_group(mgr->vars[i].key, group, name);
            
            if (strcmp(group, current_group) != 0) {
                if (!first_group) {
                    printf("\n");
                }
                printf("\n[%s]\n", group);
                printf("----------------------------------------------------------------------\n");
                strcpy(current_group, group);
                first_group = false;
            }
            
            printf("%s = %s\n", name, mgr->vars[i].value);
        }
        
        printf("\n======================================================================\n");
        printf("Total: %d variables\n", mgr->count);
    } else {
        /* Simple list */
        printf("\nEnvironment Variables:\n");
        
        /* Calculate max key length */
        size_t max_len = 0;
        for (int i = 0; i < mgr->count; i++) {
            size_t len = strlen(mgr->vars[i].key);
            if (len > max_len) max_len = len;
        }
        
        /* Print separator */
        for (size_t i = 0; i < max_len + 50; i++) printf("-");
        printf("\n");
        
        /* Print variables */
        for (int i = 0; i < mgr->count; i++) {
            if (pattern && pattern[0]) {
                if (strstr(mgr->vars[i].key, pattern) == NULL) {
                    continue;
                }
            }
            printf("%-*s = %s\n", (int)max_len, mgr->vars[i].key, mgr->vars[i].value);
        }
        
        /* Print separator */
        for (size_t i = 0; i < max_len + 50; i++) printf("-");
        printf("\n");
        printf("Total: %d variables\n", mgr->count);
    }
}

/* List variables in specific group */
void evm_list_group(EnvManager *mgr, const char *group, bool no_prefix) {
    if (!group || !group[0]) {
        evm_list(mgr, NULL, false);
        return;
    }
    
    char prefix[MAX_KEY_LEN];
    snprintf(prefix, sizeof(prefix), "%s:", group);
    size_t prefix_len = strlen(prefix);
    
    /* Count matching variables */
    int count = 0;
    size_t max_len = 0;
    for (int i = 0; i < mgr->count; i++) {
        if (strncmp(mgr->vars[i].key, prefix, prefix_len) == 0) {
            count++;
            size_t name_len = strlen(mgr->vars[i].key) - prefix_len;
            if (name_len > max_len) max_len = name_len;
        }
    }
    
    if (count == 0) {
        printf("No environment variables in group '%s'\n", group);
        return;
    }
    
    printf("\nEnvironment Variables in group '%s':\n", group);
    for (size_t i = 0; i < max_len + 50; i++) printf("-");
    printf("\n");
    
    /* Print sorted */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
    for (int i = 0; i < mgr->count; i++) {
        if (strncmp(mgr->vars[i].key, prefix, prefix_len) == 0) {
            const char *display_key = no_prefix ? mgr->vars[i].key + prefix_len : mgr->vars[i].key;
            printf("%-*s = %s\n", (int)(no_prefix ? max_len : max_len + prefix_len), 
                   display_key, mgr->vars[i].value);
        }
    }
    
    for (size_t i = 0; i < max_len + 50; i++) printf("-");
    printf("\n");
    printf("Total: %d variables\n", count);
}

/* List all groups */
void evm_list_groups(EnvManager *mgr) {
    char groups[MAX_VARS][MAX_KEY_LEN];
    int group_count = 0;
    int group_vars[MAX_VARS] = {0};
    
    /* Collect groups */
    for (int i = 0; i < mgr->count; i++) {
        char group[MAX_KEY_LEN], name[MAX_KEY_LEN];
        extract_group(mgr->vars[i].key, group, name);
        
        /* Check if group already exists */
        int found = -1;
        for (int j = 0; j < group_count; j++) {
            if (strcmp(groups[j], group) == 0) {
                found = j;
                break;
            }
        }
        
        if (found >= 0) {
            group_vars[found]++;
        } else if (group_count < MAX_VARS) {
            strcpy(groups[group_count], group);
            group_vars[group_count] = 1;
            group_count++;
        }
    }
    
    if (group_count == 0) {
        printf("No groups found. All variables are in the default namespace.\n");
        return;
    }
    
    printf("\nAvailable Groups:\n");
    printf("--------------------------------------------------\n");
    
    for (int i = 0; i < group_count; i++) {
        printf("%-30s (%d variables)\n", groups[i], group_vars[i]);
    }
    
    printf("--------------------------------------------------\n");
    printf("Total: %d groups\n", group_count);
}

/* Search environment variables */
void evm_search(EnvManager *mgr, const char *pattern, bool search_value) {
    if (!pattern || !pattern[0]) {
        printf("No search pattern specified\n");
        return;
    }
    
    /* Sort first */
    qsort(mgr->vars, mgr->count, sizeof(EnvVar), compare_vars);
    
    /* Collect results */
    EnvVar results[MAX_VARS];
    int result_count = 0;
    size_t max_len = 0;
    
    for (int i = 0; i < mgr->count; i++) {
        bool match = false;
        
        /* Check key */
        if (strcasestr(mgr->vars[i].key, pattern)) {
            match = true;
        }
        /* Check value if requested */
        else if (search_value && strcasestr(mgr->vars[i].value, pattern)) {
            match = true;
        }
        
        if (match) {
            results[result_count] = mgr->vars[i];
            size_t len = strlen(mgr->vars[i].key);
            if (len > max_len) max_len = len;
            result_count++;
        }
    }
    
    if (result_count == 0) {
        printf("No environment variables match '%s' in %s\n", 
               pattern, search_value ? "key and value" : "key");
        return;
    }
    
    printf("\nSearch results for '%s':\n", pattern);
    for (size_t i = 0; i < max_len + 50; i++) printf("-");
    printf("\n");
    
    for (int i = 0; i < result_count; i++) {
        printf("%-*s = %s\n", (int)max_len, results[i].key, results[i].value);
    }
    
    for (size_t i = 0; i < max_len + 50; i++) printf("-");
    printf("\n");
    printf("Total: %d matches\n", result_count);
}

/* Case-insensitive strstr (GNU extension) */
char *strcasestr(const char *haystack, const char *needle) {
    if (!needle[0]) return (char *)haystack;
    
    char *h = (char *)haystack;
    while (*h) {
        if (tolower((unsigned char)*h) == tolower((unsigned char)*needle)) {
            char *h2 = h + 1;
            char *n2 = (char *)needle + 1;
            while (*n2 && tolower((unsigned char)*h2) == tolower((unsigned char)*n2)) {
                h2++;
                n2++;
            }
            if (!*n2) return h;
        }
        h++;
    }
    return NULL;
}
