import unittest
from tools.task0028_timeline_gate import parse_time,provider_time,price_vector,valid_vector
class TimelineGateTests(unittest.TestCase):
 def test_provider_time(self):
  self.assertEqual(provider_time({"updateDate":"2026-10-17","updateTime":"20:30:00"}).utcoffset().total_seconds(),28800)
 def test_bad_timestamp(self):
  self.assertIsNone(provider_time({}))
 def test_excludes_transport_metadata(self):
  a={"h":"2.30","d":"3.00","a":"3.10","updateDate":"2026-10-17","updateTime":"12:00:00","hf":"1"}
  b={**a,"updateTime":"13:00:00","hf":"0"}
  self.assertEqual(price_vector(a),price_vector(b))
 def test_valid_required(self):
  self.assertTrue(valid_vector({"h":"2.1","d":"3.3","a":"3.7"},"had"))
  self.assertFalse(valid_vector({"h":"2.1","d":"3.3"},"had"))
  self.assertFalse(valid_vector({"h":"1.0","d":"3.3","a":"2.2"},"had"))
if __name__=="__main__":unittest.main()
