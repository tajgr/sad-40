import unittest
from unittest.mock import MagicMock

from measure_node import MeasureNode
import os

class MeasureNodeTest(unittest.TestCase):
    def test_make_dir(self):
        c = MeasureNode(config={"storage_path": "."}, bus=MagicMock() )
        c.wdn1 = "tmp_test"
        wd = c.make_dir("test_label")
        print(wd)
        os.path.isdir(wd)
        self.assertTrue(os.path.isdir(wd))
        os.rmdir(wd)
        os.rmdir(os.path.join(c.storage_path, c.wdn1))


if __name__ == '__main__':
    unittest.main()
