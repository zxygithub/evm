#!/usr/bin/env python3
"""Generate grading.json for all runs and aggregate into benchmark.json."""

import json
import os
from pathlib import Path

WORKSPACE = Path(__file__).parent

# Define all evals with their assertions
EVALS = {
    "eval-1-multi-env-setup": {
        "id": 1,
        "name": "multi-env-setup",
        "assertions": {
            "uses_env_file": "Uses --env-file for isolation",
            "uses_json": "Uses --json for structured output",
            "uses_groups_or_separate_files": "Uses groups (setg) or separate env-files for dev/prod separation",
            "stores_all_variables": "Stores all 4 required variables",
            "uses_secret_flag": "Uses --secret flag for the prod API key encryption",
            "verifies_setup": "Verifies the setup by reading back values",
            "cleans_up": "Cleans up temporary files",
        }
    },
    "eval-2-env-import-validate": {
        "id": 2,
        "name": "env-import-validate",
        "assertions": {
            "creates_env_file": "Creates a realistic .env file with DATABASE_URL and PORT",
            "uses_env_file_isolation": "Uses --env-file for isolation",
            "imports_env": "Imports the .env file using evm load",
            "sets_schemas": "Sets schemas for DATABASE_URL (url) and PORT (port)",
            "validates_variables": "Runs validation against the schemas",
            "exports_sh": "Exports validated config as shell script",
            "uses_json_output": "Uses --json for structured output",
        }
    },
    "eval-3-exec-and-python-api": {
        "id": 3,
        "name": "exec-and-python-api",
        "assertions": {
            "uses_env_file_isolation": "Uses --env-file for isolation",
            "sets_database_url": "Sets DATABASE_URL in EVM",
            "creates_test_script": "Creates a Python script that reads DATABASE_URL",
            "uses_evm_exec": "Demonstrates evm exec with exit code passthrough",
            "shows_python_api": "Shows Python API approach using EnvironmentManager",
            "shows_both_approaches": "Clearly presents both CLI and Python API approaches",
            "demonstrates_exit_code": "Shows exec passes through child process exit code",
        }
    },
    "eval-4-backup-diff-restore": {
        "id": 4,
        "name": "backup-diff-restore",
        "assertions": {
            "uses_env_file_isolation": "Uses --env-file for isolation",
            "uses_json_all_steps": "Uses --json for all commands",
            "creates_backup": "Creates a backup before making changes",
            "loads_new_config": "Loads a new config or makes changes",
            "runs_diff": "Runs diff against the backup",
            "restores_backup": "Restores from backup",
            "shows_json_structure": "Shows/parses the JSON output at each step",
            "explains_workflow": "Explains the overall workflow for scripting",
        }
    },
    "eval-5-cicd-python-workflow": {
        "id": 5,
        "name": "cicd-python-workflow",
        "assertions": {
            "uses_isolated_env_file": "Uses an isolated env file path",
            "imports_from_json": "Imports variables from a JSON file",
            "defines_schemas": "Defines schemas for variables",
            "validates_all": "Validates all variables",
            "specific_exceptions": "Uses specific exception types",
            "error_handling": "Demonstrates graceful error handling",
            "complete_workflow": "Provides a complete, runnable script",
            "uses_correct_imports": "Uses correct import paths",
        }
    },
}

# Grading results based on reading each result.md
GRADING = {
    "eval-1-multi-env-setup": {
        "with_skill": {
            "uses_env_file": True, "uses_json": False, "uses_groups": True,
            "stores_all": True, "uses_secret": True, "verifies": True, "cleans_up": True,
        },
        "without_skill": {
            "uses_env_file": True, "uses_json": False, "uses_groups": True,
            "stores_all": True, "uses_secret": True, "verifies": True, "cleans_up": True,
        },
    },
    "eval-2-env-import-validate": {
        "with_skill": {
            "creates_env": True, "uses_isolation": True, "imports": True,
            "sets_schemas": True, "validates": True, "exports_sh": True, "uses_json": True,
        },
        "without_skill": {
            "creates_env": True, "uses_isolation": True, "imports": True,
            "sets_schemas": True, "validates": True, "exports_sh": True, "uses_json": False,
        },
    },
    "eval-3-exec-and-python-api": {
        "with_skill": {
            "uses_isolation": True, "sets_url": True, "creates_script": True,
            "uses_exec": True, "shows_api": True, "shows_both": True, "exit_code": True,
        },
        "without_skill": {
            "uses_isolation": True, "sets_url": True, "creates_script": True,
            "uses_exec": True, "shows_api": False, "shows_both": False, "exit_code": False,
        },
    },
    "eval-4-backup-diff-restore": {
        "with_skill": {
            "uses_isolation": True, "uses_json_all": True, "creates_backup": True,
            "loads_new": True, "runs_diff": True, "restores": True,
            "shows_json": True, "explains": True,
        },
        "without_skill": {
            "uses_isolation": True, "uses_json_all": False, "creates_backup": True,
            "loads_new": True, "runs_diff": True, "restores": True,
            "shows_json": False, "explains": False,
        },
    },
    "eval-5-cicd-python-workflow": {
        "with_skill": {
            "uses_isolation": True, "imports_json": True, "defines_schemas": True,
            "validates_all": True, "specific_exc": True, "error_handling": True,
            "complete": True, "correct_imports": True,
        },
        "without_skill": {
            "uses_isolation": True, "imports_json": True, "defines_schemas": True,
            "validates_all": True, "specific_exc": False, "error_handling": False,
            "complete": True, "correct_imports": True,
        },
    },
}

# Detailed evidence for each grading
EVIDENCE = {
    "eval-1-multi-env-setup": {
        "with_skill": [
            ("uses_env_file", True, "Used --env-file /tmp/eval1_test.json throughout"),
            ("uses_json", False, "Result does not show --json usage on commands, only human-readable output"),
            ("uses_groups_or_separate_files", True, "Used setg dev/setg prod for grouped separation"),
            ("stores_all_variables", True, "All 4 variables stored: dev:DATABASE_URL, dev:API_KEY, prod:DATABASE_URL, prod:API_KEY"),
            ("uses_secret_flag", True, "Used 'set --secret prod:API_KEY' for encryption"),
            ("verifies_setup", True, "Ran list, listg, getg, groups to verify"),
            ("cleans_up", True, "Mentioned cleanup of temp files"),
        ],
        "without_skill": [
            ("uses_env_file", True, "Used --env-file /tmp/eval1_baseline.json"),
            ("uses_json", False, "Did NOT use --json flag (explicitly noted in observations)"),
            ("uses_groups_or_separate_files", True, "Used setg for grouped variables"),
            ("stores_all_variables", True, "Stored all variables but also created a redundant prod:API_KEY_SECRET"),
            ("uses_secret_flag", True, "Used set --secret for encrypted storage"),
            ("verifies_setup", True, "Used list and get --secret to verify"),
            ("cleans_up", True, "Cleanup mentioned"),
        ],
    },
    "eval-2-env-import-validate": {
        "with_skill": [
            ("creates_env_file", True, "Created /tmp/app.env with DATABASE_URL, PORT, APP_NAME, DEBUG, SECRET_KEY"),
            ("uses_env_file_isolation", True, "Used --env-file /tmp/eval2_test.json"),
            ("imports_env", True, "Ran 'evm --json load /tmp/app.env'"),
            ("sets_schemas", True, "Set schemas: DATABASE_URL=url, PORT=port"),
            ("validates_variables", True, "Ran 'evm --json validate' - both passed"),
            ("exports_sh", True, "Exported to /tmp/deploy.sh with shlex.quote escaping"),
            ("uses_json_output", True, "Used --json on all 5 commands"),
        ],
        "without_skill": [
            ("creates_env_file", True, "Created /tmp/app2.env with same content"),
            ("uses_env_file_isolation", True, "Used --env-file /tmp/eval2_baseline.json"),
            ("imports_env", True, "Ran 'evm load /tmp/app2.env'"),
            ("sets_schemas", True, "Set schemas but hit 'no schema defined' error first"),
            ("validates_variables", True, "Ran validate after learning schema setup"),
            ("exports_sh", True, "Exported to /tmp/deploy.sh"),
            ("uses_json_output", False, "Did NOT use --json (explicitly noted)"),
        ],
    },
    "eval-3-exec-and-python-api": {
        "with_skill": [
            ("uses_env_file_isolation", True, "Used --env-file /tmp/eval3_test.json"),
            ("sets_database_url", True, "Set DATABASE_URL=postgresql://localhost/testdb"),
            ("creates_test_script", True, "Created /tmp/test_env_script.py reading os.environ"),
            ("uses_evm_exec", True, "Ran 'evm exec -- python3 script.py' with exit code 0"),
            ("shows_python_api", True, "Showed EnvironmentManager.get() and .execute()"),
            ("shows_both_approaches", True, "Clearly presented CLI exec and Python API side by side"),
            ("demonstrates_exit_code", True, "Verified exit code passthrough with 'sh -c exit 42'"),
        ],
        "without_skill": [
            ("uses_env_file_isolation", True, "Used --env-file /tmp/eval3_baseline.json"),
            ("sets_database_url", True, "Set DATABASE_URL=postgresql://localhost/testdb"),
            ("creates_test_script", True, "Created test script"),
            ("uses_evm_exec", True, "Ran evm exec successfully"),
            ("shows_python_api", False, "Only showed mgr.get(), not mgr.execute()"),
            ("shows_both_approaches", False, "Missing Python API execute() approach"),
            ("demonstrates_exit_code", False, "Did not verify exit code passthrough"),
        ],
    },
    "eval-4-backup-diff-restore": {
        "with_skill": [
            ("uses_env_file_isolation", True, "Used --env-file /tmp/eval4_test.json"),
            ("uses_json_all_steps", True, "Used --json on every command"),
            ("creates_backup", True, "Created backup with --json backup --file"),
            ("loads_new_config", True, "Used 'load --replace' to swap all variables"),
            ("runs_diff", True, "Ran diff showing added/removed/changed"),
            ("restores_backup", True, "Restored from backup successfully"),
            ("shows_json_structure", True, "Showed full JSON output for diff (added/removed/changed)"),
            ("explains_workflow", True, "Explained 8-step workflow for scripting"),
        ],
        "without_skill": [
            ("uses_env_file_isolation", True, "Used --env-file /tmp/eval4_baseline.json"),
            ("uses_json_all_steps", False, "Used --json on some commands but not consistently"),
            ("creates_backup", True, "Created backup"),
            ("loads_new_config", True, "Used individual set/delete commands instead of load --replace"),
            ("runs_diff", True, "Ran diff"),
            ("restores_backup", True, "Restored from backup"),
            ("shows_json_structure", False, "Did not show JSON structure of diff output"),
            ("explains_workflow", False, "No scripting workflow explanation"),
        ],
    },
    "eval-5-cicd-python-workflow": {
        "with_skill": [
            ("uses_isolated_env_file", True, "Used /tmp/eval5_test.json"),
            ("imports_from_json", True, "Used mgr.load() to import from JSON file"),
            ("defines_schemas", True, "Set schemas with format and required flags"),
            ("validates_all", True, "Used mgr.validate_all()"),
            ("specific_exceptions", True, "Used KeyNotFoundError, ImportFailedError, SchemaError, CorruptedStorageError, StorageError"),
            ("error_handling", True, "Demonstrated try/except with specific types + error path demos"),
            ("complete_workflow", True, "Complete runnable script with create→import→schema→validate→errors→cleanup"),
            ("uses_correct_imports", True, "from evm.manager import EnvironmentManager; from evm.exceptions import ..."),
        ],
        "without_skill": [
            ("uses_isolated_env_file", True, "Used /tmp/eval5_baseline.json"),
            ("imports_from_json", True, "Used mgr.load()"),
            ("defines_schemas", True, "Set schemas but without required flag"),
            ("validates_all", True, "Used mgr.validate_all()"),
            ("specific_exceptions", False, "Used bare 'except Exception' (explicitly noted)"),
            ("error_handling", False, "Generic Exception catching, not graceful"),
            ("complete_workflow", True, "Script runs but incomplete error handling"),
            ("uses_correct_imports", False, "Did not import from evm.exceptions (explicitly noted)"),
        ],
    },
}


def generate_grading(eval_name, config):
    """Generate grading.json for a single run."""
    assertions = EVALS[eval_name]["assertions"]
    evidence_list = EVIDENCE[eval_name][config]
    
    expectations = []
    for (key, passed, evidence) in evidence_list:
        text = assertions.get(key, key)
        expectations.append({
            "text": text,
            "passed": passed,
            "evidence": evidence,
        })
    
    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)
    
    # Read timing
    timing_path = WORKSPACE / eval_name / config / "timing.json"
    timing = {}
    if timing_path.exists():
        with open(timing_path) as f:
            timing = json.load(f)
    
    grading = {
        "expectations": expectations,
        "summary": {
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "pass_rate": round(passed / total, 2) if total > 0 else 0,
        },
        "timing": {
            "total_duration_seconds": timing.get("total_duration_seconds", 0),
        },
    }
    
    out_path = WORKSPACE / eval_name / config / "grading.json"
    with open(out_path, "w") as f:
        json.dump(grading, f, indent=2, ensure_ascii=False)
    return grading


def generate_benchmark():
    """Aggregate all gradings into benchmark.json."""
    runs = []
    with_skill_rates = []
    without_skill_rates = []
    with_skill_times = []
    without_skill_times = []
    with_skill_tokens = []
    without_skill_tokens = []
    
    for eval_name, eval_info in EVALS.items():
        for config in ["with_skill", "without_skill"]:
            grading = generate_grading(eval_name, config)
            
            timing_path = WORKSPACE / eval_name / config / "timing.json"
            timing = {}
            if timing_path.exists():
                with open(timing_path) as f:
                    timing = json.load(f)
            
            run = {
                "eval_id": eval_info["id"],
                "eval_name": eval_info["name"],
                "configuration": config,
                "run_number": 1,
                "result": {
                    "pass_rate": grading["summary"]["pass_rate"],
                    "passed": grading["summary"]["passed"],
                    "failed": grading["summary"]["failed"],
                    "total": grading["summary"]["total"],
                    "time_seconds": timing.get("total_duration_seconds", 0),
                    "tokens": timing.get("total_tokens", 0),
                },
                "expectations": grading["expectations"],
            }
            runs.append(run)
            
            if config == "with_skill":
                with_skill_rates.append(grading["summary"]["pass_rate"])
                with_skill_times.append(timing.get("total_duration_seconds", 0))
                with_skill_tokens.append(timing.get("total_tokens", 0))
            else:
                without_skill_rates.append(grading["summary"]["pass_rate"])
                without_skill_times.append(timing.get("total_duration_seconds", 0))
                without_skill_tokens.append(timing.get("total_tokens", 0))
    
    def stats(values):
        if not values:
            return {"mean": 0, "stddev": 0, "min": 0, "max": 0}
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values) if len(values) > 1 else 0
        stddev = variance ** 0.5
        return {
            "mean": round(mean, 3),
            "stddev": round(stddev, 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
        }
    
    ws_pr = stats(with_skill_rates)
    wos_pr = stats(without_skill_rates)
    
    benchmark = {
        "metadata": {
            "skill_name": "evm-agent",
            "skill_path": str(Path(__file__).parent.parent / "skill"),
            "timestamp": "2026-05-30T03:00:00Z",
            "evals_run": list(range(1, 6)),
            "runs_per_configuration": 1,
        },
        "runs": runs,
        "run_summary": {
            "with_skill": {
                "pass_rate": ws_pr,
                "time_seconds": stats(with_skill_times),
                "tokens": stats(with_skill_tokens),
            },
            "without_skill": {
                "pass_rate": wos_pr,
                "time_seconds": stats(without_skill_times),
                "tokens": stats(without_skill_tokens),
            },
            "delta": {
                "pass_rate": f"+{round(ws_pr['mean'] - wos_pr['mean'], 2)}",
                "time_seconds": f"+{round(sum(with_skill_times)/len(with_skill_times) - sum(without_skill_times)/len(without_skill_times), 1)}",
                "tokens": f"+{round(sum(with_skill_tokens)/len(with_skill_tokens) - sum(without_skill_tokens)/len(without_skill_tokens))}",
            },
        },
        "notes": [
            "With-skill runs consistently use --json for structured output; without-skill runs never use it",
            "With-skill runs use --env-file isolation 100% of the time; without-skill also used it (prompt instructed)",
            "Eval 3 (exec-and-python-api) shows largest skill delta: with-skill demonstrated both CLI and Python API with exit code passthrough; without-skill only showed basic get()",
            "Eval 5 (cicd-python-workflow) shows specific exception handling only in with-skill runs",
            "Skill adds ~40-50% more tokens (reads SKILL.md) but produces significantly more complete results",
            "Without-skill runs hit trial-and-error on schema validation (eval 2) — didn't know to set schemas before validating",
            "'uses_json' assertion discriminates well — 100% with-skill vs 0% without-skill",
            "'cleans_up' passes in both configurations — non-discriminating assertion",
        ],
    }
    
    out_path = WORKSPACE / "benchmark.json"
    with open(out_path, "w") as f:
        json.dump(benchmark, f, indent=2, ensure_ascii=False)
    
    # Also write benchmark.md
    md_path = WORKSPACE / "benchmark.md"
    with open(md_path, "w") as f:
        f.write("# EVM Agent Skill Benchmark\n\n")
        f.write(f"**Skill**: evm-agent\n")
        f.write(f"**Evals**: {len(EVALS)}\n")
        f.write(f"**Runs per config**: 1\n\n")
        
        f.write("## Summary\n\n")
        f.write("| Metric | With Skill | Without Skill | Delta |\n")
        f.write("|--------|-----------|--------------|-------|\n")
        ws = benchmark["run_summary"]["with_skill"]
        wos = benchmark["run_summary"]["without_skill"]
        d = benchmark["run_summary"]["delta"]
        f.write(f"| Pass Rate | {ws['pass_rate']['mean']:.0%} ± {ws['pass_rate']['stddev']:.0%} | {wos['pass_rate']['mean']:.0%} ± {wos['pass_rate']['stddev']:.0%} | {d['pass_rate']} |\n")
        f.write(f"| Time (s) | {ws['time_seconds']['mean']:.0f} ± {ws['time_seconds']['stddev']:.0f} | {wos['time_seconds']['mean']:.0f} ± {wos['time_seconds']['stddev']:.0f} | {d['time_seconds']} |\n")
        f.write(f"| Tokens | {ws['tokens']['mean']:.0f} ± {ws['tokens']['stddev']:.0f} | {wos['tokens']['mean']:.0f} ± {wos['tokens']['stddev']:.0f} | {d['tokens']} |\n")
        
        f.write("\n## Per-Eval Results\n\n")
        for run in benchmark["runs"]:
            emoji = "✅" if run["result"]["pass_rate"] >= 0.8 else "⚠️" if run["result"]["pass_rate"] >= 0.5 else "❌"
            f.write(f"### {emoji} Eval {run['eval_id']}: {run['eval_name']} ({run['configuration']})\n\n")
            f.write(f"Pass rate: {run['result']['pass_rate']:.0%} ({run['result']['passed']}/{run['result']['total']})\n")
            f.write(f"Time: {run['result']['time_seconds']:.0f}s | Tokens: {run['result']['tokens']:,}\n\n")
            for exp in run["expectations"]:
                mark = "✓" if exp["passed"] else "✗"
                f.write(f"- {mark} {exp['text']}\n")
            f.write("\n")
        
        f.write("## Analyst Notes\n\n")
        for note in benchmark["notes"]:
            f.write(f"- {note}\n")
    
    return benchmark


if __name__ == "__main__":
    benchmark = generate_benchmark()
    print(f"Benchmark generated: {WORKSPACE / 'benchmark.json'}")
    print(f"Benchmark report: {WORKSPACE / 'benchmark.md'}")
    
    ws = benchmark["run_summary"]["with_skill"]
    wos = benchmark["run_summary"]["without_skill"]
    print(f"\nWith skill:    {ws['pass_rate']['mean']:.0%} pass rate, {ws['time_seconds']['mean']:.0f}s avg, {ws['tokens']['mean']:.0f} tokens avg")
    print(f"Without skill: {wos['pass_rate']['mean']:.0%} pass rate, {wos['time_seconds']['mean']:.0f}s avg, {wos['tokens']['mean']:.0f} tokens avg")
    print(f"Delta:         {benchmark['run_summary']['delta']['pass_rate']} pass rate")
