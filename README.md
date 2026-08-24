# Desen Lin academic website

This is the maintainable Quarto source for the academic website. GitHub Actions
renders and publishes it to GitHub Pages after each change to the `main` branch.

## Add a paper

1. Copy `papers/paper-template.yml`.
2. Rename the copy using `YEAR-short-title.yml`.
3. Fill in the fields and remove `draft: true` when ready.
4. Commit the file. The research page is regenerated automatically.

Only `title`, `year`, `category`, and `citation` are required. Abstract, links,
coauthors, honors, presentations, and media are optional and appear only when
provided.

Use a complete APA reference in `citation`. Each coauthor can include an
`affiliation` and profile `url`; each honor, presentation, or media item can
include a `label` and `url`. Include the city, state/country, and year in every
presentation label.

## Update the CV

Place the new PDF at `files/desen-lin-cv.pdf`, retaining that exact filename.
After the one-time launch migration, replacing the PDF is the only required step.

## Local preview

Install Quarto and PyYAML, then run:

```bash
python -m pip install pyyaml
quarto preview
```

## Domain cutover

Do not add the custom-domain `CNAME` file until the GitHub Pages site has been
fully reviewed and the Wix DNS cutover is scheduled.
