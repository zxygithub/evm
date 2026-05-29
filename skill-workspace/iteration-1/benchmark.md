# Benchmark: evm-agent skill

**With-skill pass rate: 100%** | Without-skill: 56% | **Delta: +44%**

## Per-eval breakdown

| Eval | With Skill | Without Skill | Delta |
|------|-----------|--------------|-------|
| Multi-Environment Setup | 100% (5/5) | 60% (3/5) | +40% |
| Import/Validate/Export | 100% (5/5) | 60% (3/5) | +40% |
| Exec + Python API | 100% (5/5) | 40% (2/5) | +60% |
| Backup/Diff/Restore | 100% (5/5) | 100% (5/5) | +0% |
| CI/CD Python Workflow | 100% (5/5) | 20% (1/5) | +80% |

## Key findings

- **--json usage** is the single biggest differentiator — with-skill runs use it consistently, without-skill runs rarely discover it
- **Python API guidance** in the skill dramatically improves code quality (Eval 5: 100% vs 20%)
- **--dry-run** and **exit code verification** are skill-specific patterns never discovered without guidance
- **Eval 4** passes equally in both configs because the prompt explicitly requests JSON output
- Without the skill, agents use bare `except Exception` instead of specific types, miss `mgr.execute()`, and don't verify exit codes