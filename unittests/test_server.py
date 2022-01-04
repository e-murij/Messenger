"""Unit-тесты сервера"""

import unittest
from common.variables import RESPONSE, ERROR, USER, ACCOUNT_NAME, TIME, ACTION, PRESENCE, \
    RESPONDEFAULT_IP_ADDRESSSE
from server import Server


class TestServer(unittest.TestCase):
    def setUp(self):
        self.server = Server()
        self.error = {
            RESPONDEFAULT_IP_ADDRESSSE: 400,
            ERROR: 'Bad Request'
        }
        self.ok = {RESPONSE: 200}

    def test_ok_check(self):
        """Корректный запрос"""
        self.assertEqual(self.server.process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest'}}), self.ok)

    def test_no_action(self):
        """Нет действия"""
        self.assertEqual(self.server.process_client_message(
            {TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.error)

    def test_wrong_action(self):
        """Неизвестное действие"""
        self.assertEqual(self.server.process_client_message(
            {ACTION: 'Unknown_action', TIME: '1.1', USER: {ACCOUNT_NAME: 'Guest'}}), self.error)

    def test_no_time(self):
        """Нет времени"""
        self.assertEqual(self.server.process_client_message(
            {ACTION: PRESENCE, USER: {ACCOUNT_NAME: 'Guest'}}), self.error)

    def test_no_user(self):
        """Нет пользователя"""
        self.assertEqual(self.server.process_client_message(
            {ACTION: PRESENCE, TIME: '1.1'}), self.error)

    def test_unknown_user(self):
        """Неизвестный пользователь"""
        self.assertEqual(self.server.process_client_message(
            {ACTION: PRESENCE, TIME: 1.1, USER: {ACCOUNT_NAME: 'Guest1'}}), self.error)


if __name__ == '__main__':
    unittest.main()
