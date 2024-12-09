import os
import unittest
import time
import sys
from pprint import pprint

sys.path.append("experiment-runner")
from Plugins.Profilers.PowerMetrics import PowerMetrics
from Plugins.Profilers.PowerMetrics import PMSampleTypes

class TestPowerMetrics(unittest.TestCase):
    # def tearDown(self):
    #     if self.plugin is None:
    #         return

    #     if os.path.exists(self.plugin.logfile):
    #         os.remove(self.plugin.logfile)

    #     self.plugin = None

    def test_update(self):
        self.plugin = PowerMetrics()
        original_args = self.plugin.args.copy()

        self.plugin.update_parameters(add={"--show-process-qos": None})
        self.assertIn(("--show-process-qos", None), self.plugin.args.items())

        self.plugin.update_parameters(remove=["--show-process-qos"])    
        self.assertDictEqual(original_args, self.plugin.args)

        self.plugin.update_parameters(add={"--unhide-info": 
                                           [PMSampleTypes.PM_SAMPLE_TASKS, PMSampleTypes.PM_SAMPLE_SFI]})
        self.assertIn(("--unhide-info", 
                       [PMSampleTypes.PM_SAMPLE_TASKS, PMSampleTypes.PM_SAMPLE_SFI]), self.plugin.args.items())

    def test_invalid_update(self):
        self.plugin = PowerMetrics()
        
        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"--not-a-valid-parameter": None})
        
        original_args = self.plugin.args.copy()

        # This should be a null op
        self.plugin.update_parameters(remove=["--not-a-valid-parameter"])
        self.assertDictEqual(original_args, self.plugin.args)

        with self.assertRaises(RuntimeError):
            self.plugin.update_parameters(add={"--unhide-info": ["not", "correct", "type"]})
    
    def test_run(self):
        test_outfile = "/tmp/pm_test_out.csv"
        self.plugin = PowerMetrics(out_file=test_outfile, sample_frequency=1000)

        sleep_len = 2

        self.plugin.start()
        time.sleep(sleep_len)
        self.plugin.stop()

        self.assertTrue(os.path.exists(test_outfile))

        log = self.plugin.parse_log(test_outfile)
        power_data = self.plugin.parse_plist_power(log)
        
        # powermetrics returns a seperate plist for each measurement
        self.assertEqual(len(log), (sleep_len/(self.plugin.args["--sample-rate"]/1000)) - 1)

        # Make sure we have results from each sampler
        for sampler in map(lambda x: x.value, self.plugin.args["--samplers"]):
            # TODO: This doesnt properly check all results, only for the parameters used in this test
            # As names of samplers can differ from names of the data headers, we approximate this a bit.
            for l in log:
                if "cpu_power" in sampler:
                    self.assertIn("package_joules", l["processor"].keys())
                    self.assertIn("package_watts", l["processor"].keys())
                else:
                    self.assertTrue(len(list(filter(lambda x: sampler.lower() in x.lower() or x.lower() in sampler.lower(), l.keys()))) > 0)
        
        # Check that our power data filter is also working
        for l in power_data:
            self.assertIn("GPU", l.keys())
            self.assertIn("agpm_stats", l.keys())
            self.assertIn("processor", l.keys())
            self.assertIn("timestamp", l.keys())


if __name__ == '__main__':
    unittest.main()
