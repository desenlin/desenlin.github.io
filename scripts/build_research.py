"""Build the research-page include from one YAML file per paper."""

from __future__ import annotations

import html
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "papers"
OUTPUT = ROOT / "_generated" / "research-list.qmd"

SECTIONS = [
    ("publication", "Publications", ("publication",)),
    ("working-paper", "Working Papers", ("working-paper",)),
    ("work-in-progress", "Work in Progress", ("work-in-progress",)),
    (
        "policy-reports-and-others",
        "Policy Reports and Others",
        ("policy-report", "pre-doctoral"),
    ),
]


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_papers() -> list[dict]:
    papers: list[dict] = []
    for path in sorted(PAPER_DIR.glob("*.yml")):
        if path.name == "paper-template.yml":
            continue
        record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if record.get("draft"):
            continue
        for required in ("title", "year", "category", "citation"):
            if not record.get(required):
                raise ValueError(f"{path.name}: missing required field '{required}'")
        record["_source"] = path.name
        papers.append(record)
    return sorted(papers, key=lambda item: (-int(item["year"]), item["title"]))


def render_link(value: dict | str, css_class: str | None = None) -> str:
    if isinstance(value, str):
        return esc(value)
    label = esc(value.get("label") or value.get("name") or "")
    url = value.get("url") or value.get("href")
    class_markup = f' class="{css_class}"' if css_class else ""
    if url:
        return (
            f'<a{class_markup} href="{esc(url)}" target="_blank" '
            f'rel="noreferrer">{label}</a>'
        )
    return f'<span{class_markup}>{label}</span>' if css_class else label


def render_authors(authors: list[dict | str]) -> str:
    rendered: list[str] = []
    for author in authors:
        if isinstance(author, str):
            rendered.append(esc(author))
            continue
        name = render_link(author)
        affiliation = author.get("affiliation")
        if affiliation:
            name += f' <span class="paper-affiliation">({esc(affiliation)})</span>'
        rendered.append(name)
    if len(rendered) < 2:
        return "".join(rendered)
    if len(rendered) == 2:
        return " and ".join(rendered)
    return ", ".join(rendered[:-1]) + ", and " + rendered[-1]


def render_list(label: str, values: list[dict | str] | None) -> list[str]:
    if not values:
        return []
    return [
        '<div class="paper-meta">',
        f'<div class="paper-meta-label">{esc(label)}</div>',
        f'<div class="paper-meta-items">{" · ".join(render_link(value) for value in values)}</div>',
        "</div>",
    ]


def render_paper(paper: dict, citation_id: str) -> list[str]:
    lines = ['::: {.paper-card}']
    status = paper.get("status")
    if status:
        lines.append(
            f'<div class="paper-topline"><span class="paper-status">{esc(status)}</span></div>'
        )
    lines.extend(["", f'### {paper["title"]}', ""])
    authors = paper.get("authors") or []
    venue = paper.get("venue")
    venue_name = venue.get("name") if isinstance(venue, dict) else venue
    if (
        paper.get("category") == "working-paper"
        and str(venue_name or "").strip().casefold() == "ssrn electronic journal"
    ):
        venue = None
    if authors:
        lines.extend(
            [f'<p class="paper-authors">with {render_authors(authors)}</p>', ""]
        )
    venue_line = render_link(venue) + ", " if venue else ""
    venue_line += esc(paper["year"])
    lines.extend([f'<p class="paper-venue-line">{venue_line}</p>', ""])

    links = paper.get("links") or []
    link_items = [
        f'<a href="{esc(link["url"])}" target="_blank" rel="noreferrer">{esc(link["label"])}</a>'
        for link in links
    ]
    show_citation = paper.get(
        "show_citation", paper.get("category") != "work-in-progress"
    )
    if show_citation:
        link_items.append(
            f'<button type="button" class="citation-link" aria-haspopup="dialog" '
            f'onclick="document.getElementById(\'{citation_id}\').showModal()">'
            "APA citation</button>"
        )
    if link_items:
        lines.extend(
            [f'<div class="paper-links">{" ".join(link_items)}</div>', ""]
        )

    if show_citation:
        lines.extend(
            [
                f'<dialog class="citation-dialog" id="{citation_id}" onclick="if (event.target === this) this.close()">',
                '<div class="citation-dialog-content">',
                '<div class="citation-dialog-heading">',
                "<h4>APA citation</h4>",
                '<form method="dialog"><button class="citation-close" aria-label="Close APA citation">×</button></form>',
                "</div>",
                f'<p>{esc(paper["citation"])}</p>',
                "</div>",
                "</dialog>",
                "",
            ]
        )

    abstract = paper.get("abstract")
    if abstract:
        lines.extend(
            [
                '<details class="abstract-disclosure">',
                "<summary>Abstract</summary>",
                f"<p>{esc(abstract.strip())}</p>",
                "</details>",
                "",
            ]
        )

    lines.extend(render_list("Honors", paper.get("honors")))
    lines.extend(render_list("Presentations", paper.get("presentations")))
    lines.extend(render_list("Media", paper.get("media")))
    lines.extend([":::", ""])
    return lines


def main() -> None:
    papers = load_papers()
    lines = [
        '<nav class="research-jump" aria-label="Research sections">',
        *[
            f'<a href="#{section_id}">{esc(title)}</a>'
            for section_id, title, _ in SECTIONS
        ],
        "</nav>",
        "",
    ]
    citation_number = 0
    for section_id, title, categories in SECTIONS:
        matching = [paper for paper in papers if paper["category"] in categories]
        lines.extend(
            [
                f'## {title} {{#{section_id}}}',
                "",
            ]
        )
        for paper in matching:
            citation_number += 1
            lines.extend(render_paper(paper, f"citation-{citation_number}"))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
