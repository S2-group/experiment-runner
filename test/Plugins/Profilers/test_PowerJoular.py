import os
import unittest
import time
import psutil
import sys

sys.path.append("experiment-runner")
from Plugins.Profilers.PowerJoular import PowerJoular

class TestPowerJoular(unittest.TestCase):
    def tearDown(self):
        if self.plugin is None:
            return

        if  self.plugin.target_logfile                  \
            and os.path.exists(self.plugin.target_logfile):

            os.remove(self.plugin.target_logfile)

        if os.path.exists(self.plugin.logfile):
            os.remove(self.plugin.logfile)

        self.plugin = None

    def test_update(self):
        self.plugin = PowerJoular()
        original_args = self.plugin.args.copy()

        self.plugin.update_parameters(add={"-t": None})
        self.assertIn(("-t", None), self.plugin.args.items())

        self.plugin.update_parameters(remove=["-t"])    
        self.assertDictEqual(original_args, self.plugin.args)

        self.plugin.update_parameters(add={"-a": "program"})
        self.assertIn(("-a", "program"), self.plugin.args.items())

    def test_invalid_update(self):
        self.plugin = PowerJoular()
        
        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"--not-a-valid-parameter": None})
        
        original_args = self.plugin.args.copy()

        # This should be a null op
        self.plugin.update_parameters(remove=["--not-a-valid-parameter"])
        self.assertDictEqual(original_args, self.plugin.args)

        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"-p": "not the correct type"})

    def test_run(self):
        valid_pid = psutil.pids()[0] # Could possibly fail if the process finishes before we test
        test_outfile = "/tmp/pj_test_out.csv"
        self.plugin = PowerJoular(out_file=test_outfile, target_pid=valid_pid)

        sleep_len = 2

        self.plugin.start()
        time.sleep(sleep_len)
        self.plugin.stop()

        self.assertTrue(os.path.exists(test_outfile))
        self.assertTrue(os.path.exists(self.plugin.target_logfile))

        # We should see sleep_len - 1 entries in the log
        log = self.plugin.parse_log(test_outfile)
        target_log = self.plugin.parse_log(self.plugin.target_logfile)
        
        for k, v in log.items():
            self.assertEqual(len(v), sleep_len - 1)

        for k, v in target_log.items():
            self.assertEqual(len(v), sleep_len - 1)

if __name__ == '__main__':
    unittest.main()
