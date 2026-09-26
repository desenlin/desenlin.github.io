import importlib.util, pathlib, tempfile, unittest, json
SPEC=importlib.util.spec_from_file_location('audit',pathlib.Path(__file__).parents[1]/'analytics_audit.py')
audit=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(audit)
MID='G-MDGMSFPEH2'
GOOD=f'<html><head><script defer src="assets/analytics.js" data-ga-id="{MID}" data-project="example"></script></head></html>'
class CoverageTests(unittest.TestCase):
    def test_missing_wrong_legacy_and_duplicate_tags_fail(self):
        self.assertEqual(audit.issues(GOOD,MID),[])
        for bad in ['<html></html>',GOOD.replace(MID,'G-INCORRECT'),GOOD.replace('</head>','<script src="https://www.google-analytics.com/analytics.js"></script></head>'),GOOD+GOOD]:
            self.assertTrue(audit.issues(bad,MID),bad)
    def test_jekyll_inherited_include_is_understood(self):
        self.assertEqual(audit.issues(GOOD.replace('assets/analytics.js',"{{ '/assets/analytics.js' | relative_url }}"),MID),[])
    def test_inert_tags_and_hydration_payloads(self):
        self.assertTrue(audit.issues('<template>'+GOOD+'</template>',MID))
        bootstrap=f"gtag('js', new Date());\ngtag('config', '{MID}');"
        html=GOOD+f'<script>{bootstrap}</script><script>self.data.push({json.dumps(bootstrap)});</script>'
        self.assertEqual(audit.issues(html,MID),[])
        self.assertTrue(audit.issues(GOOD+f'<script>{bootstrap}\n{bootstrap}</script>',MID))
    def test_new_unlinked_page_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);(root/'index.html').write_text(GOOD)
            (root/'new-activity.html').write_text('<html><head><title>New activity</title></head></html>')
            (root/'tracker.js').write_text("window.top !== window.self activity_start lab_launch event.isTrusted typeof window.gtag !== 'function'")
            cfg={'site_url':'https://desenlin.com/example/','measurement_id':MID,'mode':'html','tracker':'tracker.js','exclude':{}}
            report=audit.source(root,cfg)
            self.assertIn('https://desenlin.com/example/new-activity.html',report['urls'])
            self.assertTrue(any('new-activity.html' in x for x in report['failures']))
    def test_blanket_exclusion_requires_a_reason(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            (root/'.analytics.json').write_text(json.dumps({'site_url':'https://desenlin.com/','measurement_id':MID,'exclude':{'*.html':''}}))
            with self.assertRaises(ValueError):audit.config_at(root)
if __name__=='__main__':unittest.main()
