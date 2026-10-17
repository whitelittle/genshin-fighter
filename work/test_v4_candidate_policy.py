import unittest
from v4_candidate_policy import offline_export_eligible
class CandidatePolicyTests(unittest.TestCase):
    def test_fitted_candidate_allowed_for_offline_only(self):
        self.assertTrue(offline_export_eligible({'offline_fit_passed':True,'status':'candidate_requires_review'}))
    def test_unfitted_blocked(self):
        self.assertFalse(offline_export_eligible({'offline_fit_passed':False,'status':'candidate_requires_review'}))
    def test_pending_and_historical_blocked(self):
        for status in ['needs_grip','requires_pose_overlap_fix','historical_layout','deferred_contact']:
            with self.subTest(status=status):
                self.assertFalse(offline_export_eligible({'offline_fit_passed':True,'status':status}))
    def test_missing_fields_fail_closed(self):
        for value in [{},{'offline_fit_passed':True},{'status':'candidate_requires_review'}]:
            self.assertFalse(offline_export_eligible(value))
    def test_non_boolean_fit_not_accepted(self):
        for fit in ['true',1,None]:
            self.assertFalse(offline_export_eligible({'offline_fit_passed':fit,'status':'candidate_requires_review'}))
    def test_invalid_status_fail_closed(self):
        for status in ['',None,True,{}]:
            self.assertFalse(offline_export_eligible({'offline_fit_passed':True,'status':status}))
if __name__=='__main__':unittest.main()
