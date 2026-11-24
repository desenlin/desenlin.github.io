# Public-repository workflow reliability

Audit date: November 24, 2026. Scope: all six public repositories currently owned by `desenlin`, verified against the public owner-repository API with no next page. Repositories owned by other accounts and private repositories are outside this audit.

The inventory covered 15 committed workflow YAML files and 19 GitHub workflow entries including managed Pages workflows. All 19 entries were active when checked. The latest analytics runs in all six repositories passed. An earlier failure at academic-site commit `d0e6f15` was a single HTTP 503 response from the published Sandbox page, followed by a successful retry; the subsequent `main` source and post-deployment audits also passed. That failure was separate from GitHub's inactivity notices.

## Analytics coverage after consolidation

| Repository | Weekly source and live checks | Local checks retained |
| --- | --- | --- |
| `desenlin.github.io` | Central Monday workflow, 17:29 UTC | Push, pull request, deployment, manual |
| `FIN351` | Central workflow, dedicated job and report | Push, pull request, page build, deployment, manual |
| `FIN355` | Central workflow, dedicated job and report | Push, pull request, page build, deployment, manual |
| `site-feasibility-sandbox` | Central workflow, dedicated job and report | Push, pull request, deployment, manual |
| `ame-quarter` | Central workflow, dedicated job and report | Push, pull request, page build, deployment, manual |
| `housing-market-lab` | Central workflow, dedicated job and report | Push, pull request, manual; deployment workflow also calls the live audit |

The shared auditor retries temporary serving/network errors with a bounded three-attempt policy. Persistent errors and tracking-validation failures still fail. Engine changes in academic-site PRs are tested using that PR revision; callers from other repositories use the published engine on `main`.

## Remaining schedules and recurrence risk

After consolidation there are five committed workflows with a native schedule: the central analytics workflow and the following four Housing Market Lab workflows.

| Housing Market Lab workflow | Schedule (UTC) | Purpose |
| --- | --- | --- |
| Validate data and deploy Pages | 13:23 on the 12th, 18th, 24th, and 28th of each month | Refresh providers, validate, publish |
| Dependency security audit | Monday, 16:47 | Check the dependency lockfile |
| Check annual ACS release | 14:41 on the 15th of December, January, February | Detect annual releases and corrections |
| Check annual HCD housing delivery | 14:47 on the 15th of July and October | Detect annual housing-delivery updates |

These data/security jobs need their own repository context, data files, and, in the ACS case, the configured Census credential. Their schedules remain in place. The market-brief workflow is triggered by completed data workflows rather than its own cron; it can therefore be affected if upstream scheduled refreshes stop.

Every remaining public-repository schedule is subject to the same inactivity policy. Consolidation removes five separate analytics timers but cannot exempt the academic site or Housing Market Lab from GitHub's rule. Frequent successful audits do not ensure a repository remains active, as the original warnings demonstrated. Recent pipeline commits reduce practical exposure in Housing Market Lab but are not a reason to omit this failure mode from maintenance.

## What inactivity means

GitHub's documentation says scheduled workflows in public repositories are disabled after 60 days without repository activity. It does not enumerate every event that resets the internal counter. Do not treat account-wide activity, website visits, an open PR, comments, or successful workflow runs as a guaranteed reset. A pushed change or a merged PR that creates a commit in the affected repository is the concrete maintenance action to rely on. If a workflow has already been disabled, use **Enable workflow**; GitHub also explicitly documents that a writer's commit changing the cron schedule reactivates a deactivated schedule.

The policy is per repository. Updating `FIN351` does not keep `desenlin.github.io` active. No documented repository setting exempts a public native schedule from this rule. Scheduled execution can also be delayed or dropped during GitHub Actions load, independently of inactivity.

## Option for sites that remain unchanged for months

A small private coordinator can run the existing public reusable audit against an explicit matrix of the six public repositories. The 60-day rule documented for public schedules would no longer determine whether weekly analytics checks run. The coordinator only needs read access to public source; no cross-repository write token is needed for analytics. Each public repository can retain its event-triggered checks.

Private-runner compute and artifact storage count against the account's included allowance, whereas standard public runners remain free. Use short report retention and review the allowance before moving the schedule. This is an architectural option, not an already-created repository or scheduled service.

Moving the four Housing Market Lab data/security workflows to an outside scheduler would be a separate change: it must preserve their schedules, inputs, Census credential use, concurrency, validation, and deployment behavior. Running a private analytics coordinator alone would not maintain those data jobs. An external dispatcher would need deliberately scoped Actions access; a read-only analytics coordinator does not.

Sources:

- [GitHub: disable and enable workflows](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows)
- [GitHub: schedule events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [GitHub: Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)
