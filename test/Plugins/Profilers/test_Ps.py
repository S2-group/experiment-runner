import os
import time
import unittest
import sys
import psutil

sys.path.append("experiment-runner")
from Plugins.Profilers.Ps import Ps

class TestPs(unittest.TestCase):
    def tearDown(self):
        if self.plugin is None:
            return

        if os.path.exists(self.plugin.logfile):
            os.remove(self.plugin.logfile)

        self.plugin = None

    def test_update(self):
        self.plugin = Ps()
        original_args = self.plugin.args.copy()

        self.plugin.update_parameters(add={"-e": None})
        self.assertIn(("-e", None), self.plugin.args.items())

        self.plugin.update_parameters(remove=["-e"])    
        self.assertDictEqual(original_args, self.plugin.args)

        self.plugin.update_parameters(add={"--cols": 2})
        self.assertIn(("--cols", 2), self.plugin.args.items())

        self.plugin.update_parameters(add={"-p": [1,2,3]})
        self.assertIn(("-p", [1,2,3]), self.plugin.args.items())

    def test_invalid_update(self):
        self.plugin = Ps()
        
        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"--not-a-valid-parameter": None})
        
        original_args = self.plugin.args.copy()

        # This should be a null op
        self.plugin.update_parameters(remove=["--not-a-valid-parameter"])
        self.assertDictEqual(original_args, self.plugin.args)

        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"--cols": "not the correct type"})

        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"-p": ["not", "correct", "type"]})

    
    def test_run(self):
        valid_pid = psutil.pids()[1] # Could possibly fail if the process finishes before we test
        test_outfile = "/tmp/ps_test_out.csv"
        self.plugin = Ps(out_file=test_outfile, target_pid=[valid_pid])

        sleep_len = 2
        headers = self.plugin.args["-o"]

        self.plugin.start()
        time.sleep(sleep_len)
        self.plugin.stop()

        self.assertTrue(os.path.exists(test_outfile))

        # We should see 2 entries in the log
        log = self.plugin.parse_log(test_outfile, headers)
        
        for hdr in headers:
            self.assertEqual(len(log[hdr]), sleep_len)

if __name__ == '__main__':
    unittest.main()
