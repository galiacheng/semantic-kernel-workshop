import unittest

class TestSample(unittest.TestCase):
    def test_sample(self):
        """Test basic functionality"""
        self.assertEqual(1 + 1, 2)
        self.assertEqual("fastapi".upper(), "FASTAPI")
    
    def test_sample1(self):
        """Test basic functionality"""
        self.assertEqual(1 + 1, 2)
        self.assertEqual("fastapi".upper(), "FASTAPI")
    
    def test_sample2(self):
        """Test basic functionality"""
        self.assertEqual(1 + 1, 2)
        self.assertEqual("fastapi".upper(), "FASTAPI")
    
    def test_sample3(self):
        """Test basic functionality"""
        self.assertEqual(1 + 1, 2)
        self.assertEqual("fastapi".upper(), "FASTAPI")

if __name__ == '__main__':
    unittest.main()