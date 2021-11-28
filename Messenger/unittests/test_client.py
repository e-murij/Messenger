"""Unit-тесты клиента"""

import unittest
from Messenger.common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE
from Messenger.client import Client


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = Client()

    def test_def_presence_correct(self):
        """Тест корректного запроса"""
        test = self.client.create_presence()
        test[TIME] = 1.1
        self.assertEqual(test, {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_def_presence_incorrect(self):
        """Тест некорректного запроса"""
        test = self.client.create_presence()
        test[TIME] = 1.1
        self.assertNotEqual(test, {ACTION: 'wrong', TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}})

    def test_200_ans_correct(self):
        """Тест корректтного разбора ответа 200"""
        self.assertEqual(self.client.process_ans({RESPONSE: 200}), '200 : OK')

    def test_200_ans_incorrect(self):
        """Тест некорректтного разбора ответа 200"""
        self.assertNotEqual(self.client.process_ans({RESPONSE: 200}), '400 : Bad Request')

    def test_400_ans_correct(self):
        """Тест корректного разбора 400"""
        self.assertEqual(self.client.process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '400 : Bad Request')

    def test_400_ans_incorrect(self):
        """Тест некорректного разбора 400"""
        self.assertNotEqual(self.client.process_ans({RESPONSE: 400, ERROR: 'Bad Request'}), '200 : OK')

    def test_no_response(self):
        """Тест исключения без поля RESPONSE"""
        self.assertRaises(ValueError, self.client.process_ans, {ERROR: 'Bad Request'})


if __name__ == '__main__':
    unittest.main()
