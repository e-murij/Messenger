"""Программа-сервер"""

import socket
import sys
import json
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message


class Server:
    def __init__(self, params=[]):
        self.init_params(params)
        self.init_sock()
        self.server_running()

    def init_params(self, params):
        try:
            if '-p' in params:
                self.listen_port = int(params[params.index('-p') + 1])
            else:
                self.listen_port = DEFAULT_PORT
            if self.listen_port < 1024 or self.listen_port > 65535:
                raise ValueError
        except IndexError:
            print('После параметра -\'p\' необходимо указать номер порта.')
            sys.exit(1)
        except ValueError:
            print(
                'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
            sys.exit(1)

        try:
            if '-a' in params:
                self.listen_address = params[params.index('-a') + 1]
            else:
                self.listen_address = ''

        except IndexError:
            print(
                'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
            sys.exit(1)
        print(self.listen_port)

    def init_sock(self):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind((self.listen_address, self.listen_port))

    def server_running(self):
        self.transport.listen(MAX_CONNECTIONS)

        while True:
            client, client_address = self.transport.accept()
            try:
                message_from_client = get_message(client)
                print(message_from_client)
                response = self.process_client_message(message_from_client)
                send_message(client, response)
                client.close()
            except (ValueError, json.JSONDecodeError):
                print('Принято некорретное сообщение от клиента.')
                client.close()

    def process_client_message(self, message):
        '''
        Обработчик сообщений от клиентов, принимает словарь -
        сообщение от клинта, проверяет корректность,
        возвращает словарь-ответ для клиента

        :param message:
        :return:
        '''
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
            return {RESPONSE: 200}
        return {
            RESPONDEFAULT_IP_ADDRESSSE: 400,
            ERROR: 'Bad Request'
        }


if __name__ == '__main__':
    server = Server(sys.argv)
