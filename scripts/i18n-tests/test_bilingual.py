import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from build_bilingual import protect, units, translated_soup, rewrite_url
from translate_new_text import validate


class BilingualTests(unittest.TestCase):
    def test_research_exceptions_never_enter_translation(self):
        soup = BeautifulSoup('''<html><body><div class="paper-card"><h3>Original Paper Title</h3>
        <p class="paper-authors">Author Name</p><p class="paper-venue-line">Journal Name</p>
        <div class="paper-meta-label">Honors</div><div class="paper-meta-items">Award 2026</div>
        <div class="paper-meta-items">Conference in Boston</div><div class="paper-meta-items">Media headline</div>
        <dialog class="citation-dialog"><p>Formal citation</p></dialog>
        <details class="abstract-disclosure"><summary>Abstract</summary><p>Housing research.</p></details>
        </div></body></html>''', 'html.parser')
        protect(soup)
        extracted = {text for _, _, text in units(soup)}
        self.assertEqual(extracted, {'Honors', 'Abstract', 'Housing research.'})
        zh = translated_soup(soup, {'Honors': '荣誉', 'Abstract': '摘要', 'Housing research.': '住房研究。'})
        self.assertEqual(zh.h3.text, 'Original Paper Title')
        self.assertEqual([n.text for n in zh.select('.paper-meta-items')], ['Award 2026', 'Conference in Boston', 'Media headline'])

    def test_changed_prose_requires_a_new_translation(self):
        old = {'Research in 2025.': '2025年的研究。'}
        soup = BeautifulSoup('<html><body><p>Research in 2026.</p></body></html>', 'html.parser')
        with self.assertRaises(KeyError):
            translated_soup(soup, old)

    def test_internal_links_switch_but_assets_and_labs_do_not(self):
        available = {'research.html', 'index.html'}
        self.assertEqual(rewrite_url('../research.html#papers', 'research-summaries/a.html', available, True, True), '/zh/research.html#papers')
        self.assertEqual(rewrite_url('../images/chart.png', 'research-summaries/a.html', available, True), '/images/chart.png')
        self.assertEqual(rewrite_url('/housing-market-lab/', 'index.html', available, True, True), '/housing-market-lab/')
        self.assertEqual(rewrite_url('https://example.com/a', 'index.html', available, True, True), 'https://example.com/a')

    def test_machine_translation_cannot_silently_change_numbers(self):
        validate('Price rose by 4.3% in 2026.', '2026年价格上涨4.3%。')
        with self.assertRaises(ValueError):
            validate('Price rose by 4.3%.', '价格上涨43%。')

    def test_hidden_scripts_and_comments_are_untouched(self):
        soup = BeautifulSoup('<!DOCTYPE html><html><body><!-- Hidden source link --><p>Visible text</p><script>track("English event");</script></body></html>', 'html.parser')
        self.assertEqual([text for _, _, text in units(soup)], ['Visible text'])


if __name__ == '__main__':
    unittest.main()
