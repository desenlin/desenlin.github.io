# Desen Lin academic website

Source for [desenlin.com](https://desenlin.com), the academic website of
[Desen Lin](https://desenlin.com), Associate Professor of Finance at California
State University, Fullerton. The site presents research, teaching materials,
and a curriculum vitae.

The website is built with [Quarto](https://quarto.org/) and published to GitHub
Pages by GitHub Actions after changes are merged into `main`.

## Repository structure

- `index.qmd`, `research.qmd`, `teaching.qmd`, and `cv.qmd`: principal pages
- `papers/`: structured research records used to generate the research page
- `research-summaries/`: accessible summaries of selected research
- `scripts/`: Python build utilities
- `styles/`: site-specific CSS
- `.github/workflows/publish.yml`: automated build and deployment

## Add or update a paper

1. Copy `papers/paper-template.yml`.
2. Rename the copy using `YEAR-short-title.yml`.
3. Fill in the fields and remove `draft: true` when ready.
4. Commit the file. The research page is regenerated automatically.

Only `title`, `year`, `category`, and `citation` are required. Abstract, links,
coauthors, honors, presentations, and media are optional and appear only when
provided. Supported categories are `publication`, `working-paper`,
`work-in-progress`, `dissertation`, `policy-report`, `unpublished-manuscript`,
and `pre-doctoral`. Dissertation, policy-report, unpublished-manuscript, and
pre-doctoral records appear under Other Research. Use the optional `sort_order`
field to control position within a section; lower numbers appear first.

Use a complete APA reference in `citation`. Each coauthor can include an
`affiliation` and profile `url`; each honor, presentation, or media item can
include a `label` and `url`. Include the city, state/country, and year in every
presentation label.

## Update the CV

Replace `files/desen-lin-cv.pdf`, retaining that exact filename. The website
links to that stable path.

## Local preview

Install Quarto and PyYAML, then run:

```bash
python -m pip install pyyaml
quarto preview
```

## Contributing and editorial control

Corrections and accessibility improvements are welcome through GitHub Issues or
pull requests; see [CONTRIBUTING.md](CONTRIBUTING.md). A public repository lets
others propose changes, but only the repository owner or an authorized
collaborator can merge or publish them.

## Citation

If you reuse substantial original content or the site's source code in academic
or instructional work, please use the repository's **Cite this repository**
link. Citation metadata are maintained in [CITATION.cff](CITATION.cff).

Suggested reference:

> Lin, D. (2026). *Desen Lin academic website* [Computer software].
> https://desenlin.com

## License and attribution

The software and original website content use different licenses. Code is
available under the MIT License; original prose and original visualizations are
available under CC BY 4.0. Personal, scholarly, institutional, and third-party
assets are excluded unless expressly identified otherwise. See
[LICENSE.md](LICENSE.md) for the precise scope and attribution requirements.

The views expressed on this personal academic website are those of the author
and do not necessarily represent California State University, Fullerton or the
California State University system.

## Domain cutover note

Do not add the custom-domain `CNAME` file until the GitHub Pages site has been
fully reviewed and the Wix DNS cutover is scheduled.
