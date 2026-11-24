import importlib.util, pathlib, tempfile, unittest, json
from unittest import mock
from urllib.error import HTTPError, URLError
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

class LiveFetchTests(unittest.TestCase):
    URL='https://desenlin.com/site-feasibility-sandbox/index.html'

    def response(self,html=GOOD):
        response=mock.MagicMock()
        response.__enter__.return_value=response
        response.url=self.URL
        response.headers={'Content-Type':'text/html; charset=utf-8'}
        response.read.return_value=html.encode('utf-8')
        return response

    def test_temporary_http_and_network_failures_recover(self):
        for failure in [HTTPError(self.URL,503,'Service Unavailable',{},None),URLError('temporary connection failure')]:
            with self.subTest(failure=type(failure).__name__), mock.patch.object(audit,'urlopen',side_effect=[failure,self.response()]) as fetch, mock.patch.object(audit.time,'sleep') as sleep:
                self.assertEqual(audit.get_html(self.URL),(GOOD,self.URL))
                self.assertEqual(fetch.call_count,2)
                sleep.assert_called_once_with(2)

    def test_persistent_server_error_still_fails_after_three_attempts(self):
        failures=[HTTPError(self.URL,503,'Service Unavailable',{},None) for _ in range(3)]
        with mock.patch.object(audit,'urlopen',side_effect=failures) as fetch, mock.patch.object(audit.time,'sleep') as sleep:
            with self.assertRaises(HTTPError) as raised:audit.get_html(self.URL)
            self.assertIs(raised.exception,failures[-1])
            self.assertEqual(fetch.call_count,3)
            self.assertEqual(sleep.call_args_list,[mock.call(2),mock.call(4)])

    def test_missing_page_is_not_retried(self):
        with mock.patch.object(audit,'urlopen',side_effect=HTTPError(self.URL,404,'Not Found',{},None)) as fetch, mock.patch.object(audit.time,'sleep') as sleep:
            with self.assertRaises(HTTPError):audit.get_html(self.URL)
            fetch.assert_called_once()
            sleep.assert_not_called()

    def test_missing_tracking_remains_a_validation_failure(self):
        with mock.patch.object(audit,'urlopen',return_value=self.response('<html></html>')) as fetch, mock.patch.object(audit.time,'sleep') as sleep:
            report=audit.live({'site_url':self.URL.rsplit('/',1)[0]+'/','measurement_id':MID},{'urls':[self.URL]})
            self.assertTrue(any('Expected one shared analytics script' in error for error in report['failures']))
            fetch.assert_called_once()
            sleep.assert_not_called()

    def test_unapproved_redirect_is_not_retried(self):
        response=self.response()
        response.url='https://example.com/'
        with mock.patch.object(audit,'urlopen',return_value=response) as fetch, mock.patch.object(audit.time,'sleep') as sleep:
            with self.assertRaisesRegex(ValueError,'Unexpected redirect destination'):audit.get_html(self.URL)
            fetch.assert_called_once()
            sleep.assert_not_called()
if __name__=='__main__':unittest.main()
