import unittest
from ii_researcher.utils.text_tools import remove_all_line_breaks, choose_k


class TestTextTools(unittest.TestCase):
    def test_remove_all_line_breaks(self):
        # Test basic line break removal
        input_text = "Hello\nWorld"
        self.assertEqual(remove_all_line_breaks(input_text), "Hello World")

        # Test multiple types of line breaks
        input_text = "Hello\r\nWorld\rTest\nCase"
        self.assertEqual(remove_all_line_breaks(input_text), "Hello World Test Case")

        # Test empty string
        self.assertEqual(remove_all_line_breaks(""), "")

        # Test string with no line breaks
        input_text = "Hello World"
        self.assertEqual(remove_all_line_breaks(input_text), "Hello World")

        # Test multiple consecutive line breaks
        input_text = "Hello\n\n\nWorld"
        self.assertEqual(remove_all_line_breaks(input_text), "Hello   World")

    def test_choose_k(self):
        # Test basic selection
        items = [1, 2, 3, 4, 5]
        result = choose_k(items, 3)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(item in items for item in result))
        self.assertEqual(len(set(result)), 3)  # Check for no duplicates

        # Test when k equals list length
        result = choose_k(items, 5)
        self.assertEqual(len(result), 5)
        self.assertEqual(sorted(result), sorted(items))

        # Test when k is larger than list length
        result = choose_k(items, 10)
        self.assertEqual(len(result), 5)
        self.assertEqual(sorted(result), sorted(items))

        # Test with empty list
        self.assertEqual(choose_k([], 3), [])

        # Test with k=0
        self.assertEqual(len(choose_k(items, 0)), 0)

        # Test with different types
        strings = ["a", "b", "c", "d"]
        result = choose_k(strings, 2)
        self.assertEqual(len(result), 2)
        self.assertTrue(all(s in strings for s in result))

    def test_choose_k_preserves_original(self):
        # Test that original list is not modified
        original = [1, 2, 3, 4, 5]
        original_copy = original.copy()
        _ = choose_k(original, 3)
        self.assertEqual(original, original_copy)
