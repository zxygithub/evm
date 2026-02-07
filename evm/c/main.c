/**
 * EVM - Environment Variable Manager
 * Main Entry Point and CLI Implementation
 */

#include "evm.h"
#include <getopt.h>

/* Print usage information */
static void print_usage(const char *program) {
    printf("EVM (Environment Variable Manager) v%s\n", EVM_VERSION);
    printf("A command-line tool for managing environment variables\n\n");
    printf("Usage: %s [OPTIONS] COMMAND [ARGS...]\n\n", program);
    printf("Options:\n");
    printf("  -h, --help          Show this help message\n");
    printf("  -v, --verbose       Show verbose version information\n");
    printf("  --version           Show version\n");
    printf("  --env-file FILE     Use specific env file\n\n");
    printf("Commands:\n");
    printf("  set KEY VALUE              Set an environment variable\n");
    printf("  get KEY                    Get an environment variable\n");
    printf("  delete KEY                 Delete an environment variable\n");
    printf("  list [PATTERN]             List all or filtered variables\n");
    printf("  clear                      Clear all environment variables\n");
    printf("  export --format FMT [-o FILE]   Export to json/env/sh\n");
    printf("  load FILE [--format FMT]   Load from file\n");
    printf("  exec -- COMMAND [ARGS...]  Execute command with env vars\n");
    printf("  rename OLD NEW             Rename a variable\n");
    printf("  copy SRC DST               Copy a variable\n");
    printf("  search PATTERN [--value]   Search variables\n");
    printf("  backup [-f FILE]           Create backup\n");
    printf("  restore FILE [--merge]     Restore from backup\n");
    printf("  setg GROUP KEY VALUE       Set variable in group\n");
    printf("  getg GROUP KEY             Get variable from group\n");
    printf("  deleteg GROUP KEY          Delete variable from group\n");
    printf("  listg GROUP                List variables in group\n");
    printf("  groups                     List all groups\n");
    printf("  delete-group GROUP         Delete entire group\n");
    printf("  move-group KEY GROUP       Move variable to group\n\n");
    printf("Examples:\n");
    printf("  %s set API_KEY abc123\n", program);
    printf("  %s get API_KEY\n", program);
    printf("  %s list\n", program);
    printf("  %s export --format env -o .env\n", program);
}

/* Print verbose version */
static void print_version_verbose(void) {
    printf("EVM (Environment Variable Manager)\n");
    printf("Version: %s\n", EVM_VERSION);
    printf("Author: EVM Tool\n");
    printf("License: MIT\n");
    printf("Storage: ~/.evm/env.json\n");
    printf("\nRepository: https://github.com/zxygithub/evm\n");
    printf("Documentation: https://github.com/zxygithub/evm/blob/main/README.md\n");
}

int main(int argc, char *argv[]) {
    EnvManager mgr;
    char *env_file = NULL;
    
    /* Parse global options */
    int opt;
    int option_index = 0;
    
    static struct option long_options[] = {
        {"help", no_argument, 0, 'h'},
        {"verbose", no_argument, 0, 'v'},
        {"version", no_argument, 0, 'V'},
        {"env-file", required_argument, 0, 'e'},
        {0, 0, 0, 0}
    };
    
    while ((opt = getopt_long(argc, argv, "hve:V", long_options, &option_index)) != -1) {
        switch (opt) {
            case 'h':
                print_usage(argv[0]);
                return 0;
            case 'v':
                print_version_verbose();
                return 0;
            case 'V':
                printf("%s\n", EVM_VERSION);
                return 0;
            case 'e':
                env_file = optarg;
                break;
            default:
                print_usage(argv[0]);
                return 1;
        }
    }
    
    /* Check if command provided */
    if (optind >= argc) {
        print_usage(argv[0]);
        return 1;
    }
    
    /* Initialize manager */
    evm_init(&mgr, env_file);
    
    char *command = argv[optind];
    
    /* Handle commands */
    if (strcmp(command, "set") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Error: set requires KEY and VALUE\n");
            return 1;
        }
        return evm_set(&mgr, argv[optind + 1], argv[optind + 2]) ? 0 : 1;
    }
    
    else if (strcmp(command, "get") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: get requires KEY\n");
            return 1;
        }
        return evm_get(&mgr, argv[optind + 1], NULL) ? 0 : 1;
    }
    
    else if (strcmp(command, "delete") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: delete requires KEY\n");
            return 1;
        }
        return evm_delete(&mgr, argv[optind + 1]) ? 0 : 1;
    }
    
    else if (strcmp(command, "list") == 0) {
        const char *pattern = (optind + 1 < argc) ? argv[optind + 1] : NULL;
        
        /* Check for --show-groups option */
        bool show_groups = false;
        for (int i = optind + 1; i < argc; i++) {
            if (strcmp(argv[i], "--show-groups") == 0) {
                show_groups = true;
                break;
            }
        }
        
        evm_list(&mgr, pattern, show_groups);
        return 0;
    }
    
    else if (strcmp(command, "clear") == 0) {
        evm_clear(&mgr);
        return 0;
    }
    
    else if (strcmp(command, "export") == 0) {
        const char *format = "json";
        const char *output = NULL;
        const char *group = NULL;
        
        for (int i = optind + 1; i < argc; i++) {
            if (strcmp(argv[i], "--format") == 0 || strcmp(argv[i], "-f") == 0) {
                if (i + 1 < argc) format = argv[++i];
            } else if (strcmp(argv[i], "--output") == 0 || strcmp(argv[i], "-o") == 0) {
                if (i + 1 < argc) output = argv[++i];
            } else if (strcmp(argv[i], "--group") == 0 || strcmp(argv[i], "-g") == 0) {
                if (i + 1 < argc) group = argv[++i];
            }
        }
        
        if (!output) {
            output = (strcmp(format, "json") == 0) ? "env.json" :
                     (strcmp(format, "env") == 0) ? ".env" : "export.sh";
        }
        
        if (strcmp(format, "json") == 0) {
            return evm_export_json(&mgr, output) ? 0 : 1;
        } else if (strcmp(format, "env") == 0) {
            return evm_export_env(&mgr, output) ? 0 : 1;
        } else if (strcmp(format, "sh") == 0) {
            return evm_export_sh(&mgr, output) ? 0 : 1;
        } else {
            fprintf(stderr, "Error: Unknown format '%s'\n", format);
            return 1;
        }
    }
    
    else if (strcmp(command, "load") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: load requires FILE\n");
            return 1;
        }
        
        const char *filename = argv[optind + 1];
        const char *format = NULL;
        bool replace = false;
        const char *group = NULL;
        
        for (int i = optind + 1; i < argc; i++) {
            if (strcmp(argv[i], "--format") == 0 || strcmp(argv[i], "-f") == 0) {
                if (i + 1 < argc) format = argv[++i];
            } else if (strcmp(argv[i], "--replace") == 0 || strcmp(argv[i], "-r") == 0) {
                replace = true;
            } else if (strcmp(argv[i], "--group") == 0 || strcmp(argv[i], "-g") == 0) {
                if (i + 1 < argc) group = argv[++i];
            }
        }
        
        /* Detect format from extension */
        if (!format) {
            size_t len = strlen(filename);
            if (len > 5 && strcmp(filename + len - 5, ".json") == 0) {
                format = "json";
            } else if (len > 4 && strcmp(filename + len - 4, ".env") == 0) {
                format = "env";
            } else {
                format = "json";
            }
        }
        
        if (strcmp(format, "json") == 0) {
            return evm_load_json(&mgr, filename, replace, group) ? 0 : 1;
        } else if (strcmp(format, "env") == 0) {
            return evm_load_env(&mgr, filename, replace, group) ? 0 : 1;
        } else {
            fprintf(stderr, "Error: Unknown format '%s'\n", format);
            return 1;
        }
    }
    
    else if (strcmp(command, "exec") == 0) {
        if (optind + 2 >= argc || strcmp(argv[optind + 1], "--") != 0) {
            fprintf(stderr, "Error: exec requires -- followed by command\n");
            return 1;
        }
        return evm_execute(&mgr, &argv[optind + 2], argc - optind - 2) ? 0 : 1;
    }
    
    else if (strcmp(command, "rename") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Error: rename requires OLD_KEY and NEW_KEY\n");
            return 1;
        }
        return evm_rename(&mgr, argv[optind + 1], argv[optind + 2]) ? 0 : 1;
    }
    
    else if (strcmp(command, "copy") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Error: copy requires SRC_KEY and DST_KEY\n");
            return 1;
        }
        return evm_copy(&mgr, argv[optind + 1], argv[optind + 2]) ? 0 : 1;
    }
    
    else if (strcmp(command, "search") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: search requires PATTERN\n");
            return 1;
        }
        
        bool search_value = false;
        for (int i = optind + 1; i < argc; i++) {
            if (strcmp(argv[i], "--value") == 0 || strcmp(argv[i], "-v") == 0) {
                search_value = true;
                break;
            }
        }
        
        evm_search(&mgr, argv[optind + 1], search_value);
        return 0;
    }
    
    else if (strcmp(command, "backup") == 0) {
        const char *file = NULL;
        for (int i = optind + 1; i < argc; i++) {
            if (strcmp(argv[i], "--file") == 0 || strcmp(argv[i], "-f") == 0) {
                if (i + 1 < argc) file = argv[++i];
            }
        }
        
        if (!file) {
            /* Generate timestamped filename */
            time_t now = time(NULL);
            struct tm *tm_info = localtime(&now);
            static char filename[256];
            strftime(filename, sizeof(filename), 
                     "~/.evm/backup_%Y%m%d_%H%M%S.json", tm_info);
            file = filename;
        }
        
        char expanded[1024];
        expand_path(file, expanded);
        return evm_backup(&mgr, expanded) ? 0 : 1;
    }
    
    else if (strcmp(command, "restore") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: restore requires FILE\n");
            return 1;
        }
        
        bool merge = false;
        for (int i = optind + 1; i < argc; i++) {
            if (strcmp(argv[i], "--merge") == 0 || strcmp(argv[i], "-m") == 0) {
                merge = true;
                break;
            }
        }
        
        return evm_restore(&mgr, argv[optind + 1], merge) ? 0 : 1;
    }
    
    else if (strcmp(command, "setg") == 0) {
        if (optind + 3 >= argc) {
            fprintf(stderr, "Error: setg requires GROUP, KEY, and VALUE\n");
            return 1;
        }
        return evm_set_grouped(&mgr, argv[optind + 1], argv[optind + 2], argv[optind + 3]) ? 0 : 1;
    }
    
    else if (strcmp(command, "getg") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Error: getg requires GROUP and KEY\n");
            return 1;
        }
        return evm_get_grouped(&mgr, argv[optind + 1], argv[optind + 2], NULL) ? 0 : 1;
    }
    
    else if (strcmp(command, "deleteg") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Error: deleteg requires GROUP and KEY\n");
            return 1;
        }
        return evm_delete_grouped(&mgr, argv[optind + 1], argv[optind + 2]) ? 0 : 1;
    }
    
    else if (strcmp(command, "listg") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: listg requires GROUP\n");
            return 1;
        }
        evm_list_group(&mgr, argv[optind + 1], false);
        return 0;
    }
    
    else if (strcmp(command, "groups") == 0) {
        evm_list_groups(&mgr);
        return 0;
    }
    
    else if (strcmp(command, "delete-group") == 0) {
        if (optind + 1 >= argc) {
            fprintf(stderr, "Error: delete-group requires GROUP\n");
            return 1;
        }
        return evm_delete_group(&mgr, argv[optind + 1]) ? 0 : 1;
    }
    
    else if (strcmp(command, "move-group") == 0) {
        if (optind + 2 >= argc) {
            fprintf(stderr, "Error: move-group requires KEY and GROUP\n");
            return 1;
        }
        return evm_move_to_group(&mgr, argv[optind + 1], argv[optind + 2]) ? 0 : 1;
    }
    
    else {
        fprintf(stderr, "Error: Unknown command '%s'\n", command);
        print_usage(argv[0]);
        return 1;
    }
    
    return 0;
}
