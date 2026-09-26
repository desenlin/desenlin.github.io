# Analytics coverage and maintenance

The academic site and real estate tools use GA4 measurement ID `G-MDGMSFPEH2`. Linguistics Teaching Labs retains `G-BQB575CQX3`. Different measurement IDs identify different data streams; this audit does not assume they belong to separate GA properties.

## Recorded activity

| Event | Meaning |
| --- | --- |
| `page_view` | A page was opened. Existing Google tags are reused, never configured twice. |
| `lab_launch` | A link opens a lab, activity, or course tool collection. |
| `activity_start` | First qualifying interaction with an activity's controls during that page load. |
| `view_change`, `section_view` | A viewer switches a CRE studio view or section. |
| `premise_select`, `premise_visit` | A premise is selected or its visit control is used. |
| `scene_open_tab`, `graphics_change` | The standalone scene is opened or graphics quality changes. |
| `rent_roll_download` | The rent-roll download control is used. |
| `assumption_change`, `assumptions_reset` | Assumptions are edited or reset; entered numbers are not transmitted. Each annotated input reports at most once per page load. |
| `case_load`, `case_reset`, `building_draw`, `site_draw`, `geometry_edit`, `geometry_move`, `geometry_rotate`, `geometry_delete`, `editing_finish` | A feasibility-sandbox control is used. These measure control use, not a successfully completed drawing or student assignment. |

The shared script also preserves the existing `housing_market_lab_click`, `linguistics_teaching_labs_click`, and `labs_portal_click` events where their attributes already exist. They describe the same action as `lab_launch`; do not sum them as separate launches.

Custom event parameters contain page paths, project IDs, destination paths, and fixed control labels. They do not include entered numbers, student names, free text, drawn geometry, or answers. `activity_start` does not mean an assignment was completed. The embedded Ame Quarter scene suppresses its own analytics; its parent page records the visit and annotated controls. Opening the scene as a top-level page records its own page view. Portable/offline copies do not initialize the shared tracker.

For grouped reports, a GA administrator can register `project_id`, `activity_id`, `lab_id`, `action_value`, and `link_location` as event-scoped custom dimensions. Event names can be checked without creating these dimensions. No GA account settings or custom dimensions are changed by GitHub Actions.

## Automated checks

The six academic-site and real-estate repositories have `.analytics.json` and an **Analytics tracking audit** workflow. The three Linguistics repositories retain their independent **Analytics coverage** workflows and Wednesday schedules, documented in their own `docs/analytics.md`. Their checks validate page-view tags and prepare reviewable missing-tag repair patches; this update preserves that configuration.

The shared real-estate audit runs:

- Every push and pull request: validate source pages and shared layouts, reject missing/wrong/legacy/duplicate tags, and run regression tests of the tracker and auditor.
- After a successful Pages deployment: inspect the published HTML and run Chromium checks of page-view generation and configured activity events.
- Every Monday between 17:17 and 17:41 UTC: repeat the live audit, staggered across repositories.
- **Run workflow** in GitHub Actions: optionally rerun the full live audit at any time.

The central reusable workflow and audit scripts live in this repository. Other repositories reference its `main` branch so improvements to the checker take effect without copying its implementation. Each site owns its small tracker asset and its configuration. Workflows have read-only repository permissions and no Google credentials.

The source check discovers HTML files recursively, including pages with no navigation link. Jekyll, Quarto, and React inheritance are checked explicitly. The live check follows same-site HTML links; the academic-site audit also follows new tools linked under `desenlin.com`. The discovery limit is 200 pages and fails visibly if exceeded. A completely separate new repository must install the workflow/configuration; linking it from Labs also makes it discoverable by the weekly website audit.

Browser checks intercept Google collection requests and return an empty response locally. Test page views and clicks are **not sent to Google Analytics**. Checks verify that events are generated for the correct destination, including exactly one initial page view. They cannot verify private GA report receipt, data filters, retention, consent settings, or historical visitor counts. Check Realtime or DebugView in GA when validating account-side changes.

Failures appear in the repository's Actions tab with failing URLs/reasons, a job summary, and downloadable JSON reports retained for 14 days. GitHub email notifications depend on the account's notification settings. These checks are not automatically made required branch-protection checks. Public-repository scheduled workflows may be disabled by GitHub after prolonged repository inactivity; pushes/PR checks still provide coverage, and maintainers should re-enable any disabled schedule.

## Adding a page or activity

Use the existing shared layout. For standalone HTML, include exactly one deferred local script with the correct relative path and IDs:

```html
<script defer src="assets/analytics.js"
  data-ga-id="G-MDGMSFPEH2" data-project="project-slug"></script>
```

Nested pages need a correspondingly relative script path. Keep any existing working Google tag; the shared script reuses it. Do not add a second `gtag('config', ...)` call. Use `data-analytics-action="event_name"` and an optional fixed `data-analytics-value="label"` for meaningful controls. Select values are included only with an explicit `data-analytics-allowed="value1,value2"` allowlist. Never set analytics labels from student input.

Update `.analytics.json` only when project structure changes. Exclusions must document a reason, and should identify templates or partials rather than hide missing tags on public pages. Add an interaction to `smoke` when introducing an important control. Run the audit before merging; inspect the first post-deployment result.

Sources: [Google tag setup](https://developers.google.com/tag-platform/gtagjs), [GA setup verification](https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot), [GitHub scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [Playwright request interception](https://playwright.dev/docs/network).
