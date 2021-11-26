"""Программа-клиент"""

import sys
import json
import socket
import time
from common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT
from common.utils import get_message, send_message


class Client:
    def __init__(self, params=[]):
        self.init_params(params)

    def init_params(self, params):
        try:
            self.server_address = params[1]
            self.server_port = int(params[2])
            if self.server_port < 1024 or self.server_port > 65535:
                raise ValueError
        except IndexError:
            self.server_address = DEFAULT_IP_ADDRESS
            self.server_port = DEFAULT_PORT
        except ValueError:
            print('В качестве порта может быть указано только число в диапазоне от 1024 до 65535.')
            sys.exit(1)

    def init_sock(self):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.connect((self.server_address, self.server_port))

    def client_running(self):
        self.init_sock()
        message_to_server = self.create_presence()
        send_message(self.transport, message_to_server)
        try:
            answer = self.process_ans(get_message(self.transport))
            print(answer)
        except (ValueError, json.JSONDecodeError):
            print('Не удалось декодировать сообщение сервера.')

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
        return out

    def process_ans(self, message):
        '''
        Функция разбирает ответ сервера
        :param message:
        :return:
        '''
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        raise ValueError


if __name__ == '__main__':
    client = Client()
    client.client_running()
