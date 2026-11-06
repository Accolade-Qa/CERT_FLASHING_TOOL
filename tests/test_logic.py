import unittest

from service_tool_app.logic import calculate_crc16, is_default_uin


class LogicTests(unittest.TestCase):
    def test_crc16_xmodem_check_value(self):
        self.assertEqual(calculate_crc16(0, b'123456789'), 0x31C3)

    def test_crc16_supports_incremental_updates(self):
        first = calculate_crc16(0, b'1234')
        self.assertEqual(calculate_crc16(first, b'56789'), 0x31C3)

    def test_default_uin_check_is_case_insensitive(self):
        self.assertTrue(is_default_uin('acon4naxxx'))
        self.assertFalse(is_default_uin('ACON4NA'))
        self.assertFalse(is_default_uin('some-other-uin'))


if __name__ == '__main__':
    unittest.main()
