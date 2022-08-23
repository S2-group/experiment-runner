import os
import unittest
import shutil
import tempfile

from Plugins.Profilers.WattsUpPro import WattsUpPro


class TestWattsUpPro(unittest.TestCase):
    def test_all(self):
        # ', 1.0, 5, str(context.run_dir.resolve() / 'sample.log'
        tmpdir = tempfile.mkdtemp()
        port = '/dev/ttyUSB0'
        try:
            meter = WattsUpPro(port, 1.0)
            meter.log(5, tmpdir + '/sample.log')
        except RuntimeError as ex:
            if os.path.exists(port):
                raise
            print(f"[WARNING] {self.__class__.__name__}.{self.test_all.__name__} skipped! Reason: {ex}")

        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    unittest.main()
