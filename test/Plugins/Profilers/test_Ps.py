import os
import time
import unittest
import sys
import psutil

sys.path.append("experiment-runner")
from Plugins.Profilers.Ps import Ps

class TestPs(unittest.TestCase):
    def test_update(self):
        ps = Ps()
        original_args = ps.args.copy()

        ps.update_parameters(add={"-e": None})
        self.assertIn(("-e", None), ps.args.items())

        ps.update_parameters(remove=["-e"])    
        self.assertDictEqual(original_args, ps.args)

        ps.update_parameters(add={"--cols": 2})
        self.assertIn(("--cols", 2), ps.args.items())

        ps.update_parameters(add={"-p": [1,2,3]})
        self.assertIn(("-p", [1,2,3]), ps.args.items())

    def test_invalid_update(self):
        ps = Ps()
        
        with self.assertRaises(RuntimeError):
            ps.update_parameters(add={"--not-a-valid-parameter": None})
        
        original_args = ps.args.copy()

        # This should be a null op
        ps.update_parameters(remove=["--not-a-valid-parameter"])
        self.assertDictEqual(original_args, ps.args)

        with self.assertRaises(RuntimeError):
            ps.update_parameters(add={"--cols": "not the correct type"})

        with self.assertRaises(RuntimeError):
            ps.update_parameters(add={"-p": ["not", "correct", "type"]})

    
    def test_run(self):
        valid_pid = psutil.pids()[1] # Could possibly fail if the process finishes before we test
        test_outfile = "/tmp/ps_test_out.csv"
        ps = Ps(out_file=test_outfile, target_pid=[valid_pid])

        sleep_len = 2
        headers = ps.args["-o"]

        ps.start()
        time.sleep(sleep_len)
        ps.stop()

        # We should see 5 entries in the log
        log = ps.parse_log(test_outfile, headers)
        
        for hdr in headers:
            self.assertEqual(len(log[hdr]), sleep_len)

        os.remove(test_outfile)

if __name__ == '__main__':
    unittest.main()
