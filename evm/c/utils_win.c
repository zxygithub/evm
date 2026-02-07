/**
 * EVM - Environment Variable Manager
 * Windows Compatible Utility Functions
 */

#include "evm_win.h"

/* Platform-specific path expansion */
void expand_path_platform(const char *path, char *expanded) {
#ifdef _WIN32
    if (path[0] == '~') {
        const char *home = getenv("USERPROFILE");
        if (!home) home = getenv("HOME");
        if (home) {
            /* Replace ~ with home and convert slashes */
            snprintf(expanded, 1024, "%s%s", home, path + 1);
            /* Convert forward slashes to backslashes */
            for (int i = 0; expanded[i]; i++) {
                if (expanded[i] == '/') expanded[i] = '\\';
            }
            return;
        }
    }
    strncpy(expanded, path, 1024);
    /* Convert forward slashes to backslashes */
    for (int i = 0; expanded[i]; i++) {
        if (expanded[i] == '/') expanded[i] = '\\';
    }
#else
    if (path[0] == '~') {
        const char *home = getenv("HOME");
        if (home) {
            snprintf(expanded, 1024, "%s%s", home, path + 1);
            return;
        }
    }
    strncpy(expanded, path, 1024);
#endif
}

/* Wrapper for expand_path */
void expand_path(const char *path, char *expanded) {
    expand_path_platform(path, expanded);
}

/* Platform-specific directory creation */
bool ensure_dir_platform(const char *path) {
    char tmp[1024];
    strncpy(tmp, path, sizeof(tmp) - 1);
    tmp[sizeof(tmp) - 1] = '\0';
    
    /* Find last path separator */
    char *p = NULL;
#ifdef _WIN32
    p = strrchr(tmp, '\\');
    if (!p) p = strrchr(tmp, '/');
#else
    p = strrchr(tmp, '/');
#endif
    
    if (p) {
        *p = '\0';
        
        struct stat st = {0};
        if (stat(tmp, &st) == -1) {
            /* Create directory recursively */
            char *sep = tmp;
            while ((sep = strchr(sep, PATH_SEP)) != NULL) {
                *sep = '\0';
                if (strlen(tmp) > 0) {
#ifdef _WIN32
                    _mkdir(tmp);
#else
                    mkdir(tmp, 0755);
#endif
                }
                *sep = PATH_SEP;
                sep++;
            }
#ifdef _WIN32
            _mkdir(tmp);
#else
            mkdir(tmp, 0755);
#endif
        }
    }
    return true;
}

/* Wrapper for ensure_dir */
bool ensure_dir(const char *path) {
    return ensure_dir_platform(path);
}

/* Trim whitespace from string */
char *trim(char *str) {
    if (!str) return NULL;
    
    while (isspace((unsigned char)*str)) str++;
    
    if (*str == 0) return str;
    
    char *end = str + strlen(str) - 1;
    while (end > str && isspace((unsigned char)*end)) end--;
    
    end[1] = '\0';
    return str;
}

/* Check if key has group prefix */
bool has_group_prefix(const char *key, const char *group) {
    if (!group || !group[0]) return false;
    
    char prefix[MAX_KEY_LEN];
    snprintf(prefix, sizeof(prefix), "%s:", group);
    return strncmp(key, prefix, strlen(prefix)) == 0;
}

/* Extract group and name from key */
void extract_group(const char *key, char *group, char *name) {
    char *colon = strchr(key, ':');
    if (colon) {
        size_t group_len = colon - key;
        if (group_len >= MAX_KEY_LEN) group_len = MAX_KEY_LEN - 1;
        strncpy(group, key, group_len);
        group[group_len] = '\0';
        strncpy(name, colon + 1, MAX_KEY_LEN - 1);
        name[MAX_KEY_LEN - 1] = '\0';
    } else {
        strcpy(group, "default");
        strncpy(name, key, MAX_KEY_LEN - 1);
        name[MAX_KEY_LEN - 1] = '\0';
    }
}

/* JSON escape string */
char *json_escape(const char *str, char *output, size_t outlen) {
    size_t j = 0;
    for (size_t i = 0; str[i] && j < outlen - 1; i++) {
        switch (str[i]) {
            case '"': if (j < outlen - 2) { output[j++] = '\\'; output[j++] = '"'; } break;
            case '\\': if (j < outlen - 2) { output[j++] = '\\'; output[j++] = '\\'; } break;
            case '\n': if (j < outlen - 2) { output[j++] = '\\'; output[j++] = 'n'; } break;
            case '\r': if (j < outlen - 2) { output[j++] = '\\'; output[j++] = 'r'; } break;
            case '\t': if (j < outlen - 2) { output[j++] = '\\'; output[j++] = 't'; } break;
            default: output[j++] = str[i]; break;
        }
    }
    output[j] = '\0';
    return output;
}

/* JSON unescape string */
char *json_unescape(const char *str, char *output, size_t outlen) {
    size_t j = 0;
    for (size_t i = 0; str[i] && j < outlen - 1; i++) {
        if (str[i] == '\\' && str[i + 1]) {
            i++;
            switch (str[i]) {
                case '"': output[j++] = '"'; break;
                case '\\': output[j++] = '\\'; break;
                case 'n': output[j++] = '\n'; break;
                case 'r': output[j++] = '\r'; break;
                case 't': output[j++] = '\t'; break;
                default: output[j++] = str[i]; break;
            }
        } else {
            output[j++] = str[i];
        }
    }
    output[j] = '\0';
    return output;
}

/* Case-insensitive strstr */
char *strcasestr(const char *haystack, const char *needle) {
    if (!needle[0]) return (char *)haystack;
    
    char *h = (char *)haystack;
    size_t needle_len = strlen(needle);
    
    while (*h) {
        if (tolower((unsigned char)*h) == tolower((unsigned char)*needle)) {
            if (strncasecmp(h, needle, needle_len) == 0) {
                return h;
            }
        }
        h++;
    }
    return NULL;
}
