"""Программа-клиент"""

import sys
import json
import socket
import time
import logging
import Messenger.log .client_log_config
from Messenger.errors import ReqFieldMissingError
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.utils import get_message, send_message


class Client:
    def __init__(self, params=[]):
        self.init_params(params)
        self.CLIENT_LOGGER = logging.getLogger('client')

    def init_params(self, params):
        try:
            self.server_address = params[1]
            self.server_port = int(params[2])
            if self.server_port < 1024 or self.server_port > 65535:
                self.CLIENT_LOGGER.critical(
                    f'Попытка запуска клиента с недопустимым номером порта: {self.server_port}.'
                    f' Допустимы адреса с 1024 до 65535. Клиент завершает работу.')
                sys.exit(1)
        except IndexError:
            self.server_address = DEFAULT_IP_ADDRESS
            self.server_port = DEFAULT_PORT

    def init_sock(self):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.connect((self.server_address, self.server_port))

    def client_running(self):
        try:
            self.init_sock()
            message_to_server = self.create_presence()
            send_message(self.transport, message_to_server)
            answer = self.process_ans(get_message(self.transport))
            self.CLIENT_LOGGER.info(f'Принят ответ от сервера {answer}')
        except json.JSONDecodeError:
            self.CLIENT_LOGGER.error('Не удалось декодировать полученную Json строку.')
        except ConnectionRefusedError:
            self.CLIENT_LOGGER.critical(f'Не удалось подключиться к серверу {self.server_address}:{self.server_port}, '
                                   f'конечный компьютер отверг запрос на подключение.')
        except ReqFieldMissingError as missing_error:
            self.CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле '
                                f'{missing_error.missing_field}')

    def create_presence(self, account_name='Guest'):
        '''
        Функция генерирует запрос о присутствии клиента
        :param account_name:
        :return:
        '''
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        self.CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
        return out

    def process_ans(self, message):
        '''
        Функция разбирает ответ сервера
        :param message:
        :return:
        '''
        self.CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        self.CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле {RESPONSE}')
        raise ReqFieldMissingError(RESPONSE)


if __name__ == '__main__':
    client = Client()
    client.client_running()
