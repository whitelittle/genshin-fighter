import tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import monitor

class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old=monitor.STATE
        monitor.STATE=Path(self.tmp.name)/'state.json'
    def tearDown(self):
        monitor.STATE=self.old
        self.tmp.cleanup()
    def test_identity_removed_and_html_kept_as_inert_text(self):
        value=monitor.anonymize('回复 @测试昵称 : UID:123456 手机13812345678 邮件a@test.cn C:\\Users\\Personal\\x <script>bad</script>')
        for secret in ('测试昵称','123456','13812345678','a@test.cn','Personal'):
            self.assertNotIn(secret,value)
        self.assertIn('<script>',value) # UI uses textContent, never innerHTML.
    def test_repeat_and_cross_source_dedup_preserves_sources(self):
        self.assertEqual(monitor.ingest('bilibili',[{'text':'有点卡'}],'partial'),1)
        self.assertEqual(monitor.ingest('bilibili',[{'text':'有点卡'}],'partial'),0)
        monitor.ingest('miyoushe',[{'text':'有点卡'}],'main')
        groups=[g for g in monitor.dashboard()['groups'] if g['text']=='有点卡']
        self.assertEqual(len(groups),1)
        self.assertEqual(len([e for e in groups[0]['entries'] if not e['summary']]),2)
    def test_empty_or_failure_preserves_success_and_comments(self):
        monitor.ingest('bilibili',[{'text':'出招不明显'}],'partial')
        before=monitor.read_state()
        with self.assertRaises(ValueError): monitor.ingest('bilibili',[{'text':''}],'empty')
        monitor.mark_error('bilibili','站点限制')
        after=monitor.read_state()
        self.assertEqual(before['comments'],after['comments'])
        self.assertEqual(before['sources']['bilibili']['last_success'],after['sources']['bilibili']['last_success'])
        self.assertEqual(after['sources']['bilibili']['status'],'error')
    def test_empty_public_api_does_not_close_existing_comments(self):
        with patch.object(monitor,'request_json',return_value={'page':{'count':0},'replies':[]}):
            with self.assertRaises(ValueError): monitor.collect_bilibili()

if __name__=='__main__': unittest.main()
