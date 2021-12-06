"""Программа-клиент"""
import argparse
import sys
import json
import socket
import time
import logging
import Messenger.log.client_log_config
from Messenger.decorators import Log
from Messenger.errors import ReqFieldMissingError, ServerError
from Messenger.common.variables import ACTION, PRESENCE, TIME, USER, ACCOUNT_NAME, \
    RESPONSE, ERROR, DEFAULT_IP_ADDRESS, DEFAULT_PORT, MESSAGE, MESSAGE_TEXT, SENDER
from common.utils import get_message, send_message


class Client:
    def __init__(self):
        self.CLIENT_LOGGER = logging.getLogger('client')
        self.server_address, self.server_port, self.client_mode = self.arg_parser()
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @Log()
    def arg_parser(self):
        """Создаём парсер аргументов коммандной строки
        и читаем параметры, возвращаем 3 параметра
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('addr', default=DEFAULT_IP_ADDRESS, nargs='?')
        parser.add_argument('port', default=DEFAULT_PORT, type=int, nargs='?')
        parser.add_argument('-m', '--mode', default='listen', nargs='?')
        namespace = parser.parse_args(sys.argv[1:])
        server_address = namespace.addr
        server_port = namespace.port
        client_mode = namespace.mode

        # проверим подходящий номер порта
        if not 1023 < server_port < 65536:
            self.CLIENT_LOGGER.critical(
                f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
                f'Допустимы адреса с 1024 до 65535. Клиент завершается.')
            sys.exit(1)

        # Проверим допустим ли выбранный режим работы клиента
        if client_mode not in ('listen', 'send'):
            self.CLIENT_LOGGER.critical(f'Указан недопустимый режим работы {client_mode}, '
                                        f'допустимые режимы: listen , send')
            sys.exit(1)

        return server_address, server_port, client_mode

    @Log()
    def client_running(self):
        self.CLIENT_LOGGER.info(
            f'Запущен клиент с парамертами: адрес сервера: {self.server_address}, '
            f'порт: {self.server_port}, режим работы: {self.client_mode}')
        try:
            self.transport.connect((self.server_address, self.server_port))
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
        except ServerError as error:
            self.CLIENT_LOGGER.error(f'При установке соединения сервер вернул ошибку: {error.text}')
            sys.exit(1)
        else:
            # Если соединение с сервером установлено корректно,
            # начинаем обмен с ним, согласно требуемому режиму.
            if self.client_mode == 'send':
                print('Режим работы - отправка сообщений.')
            else:
                print('Режим работы - приём сообщений.')
            while True:
                if self.client_mode == 'send':
                    try:
                        send_message(self.transport, self.create_message(self.transport))
                    except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                        self.CLIENT_LOGGER.error(f'Соединение с сервером {self.server_address} было потеряно.')
                        sys.exit(1)
                if self.client_mode == 'listen':
                    try:
                        self.message_from_server(get_message(self.transport))
                    except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                        self.CLIENT_LOGGER.error(f'Соединение с сервером {self.server_address} было потеряно.')
                        sys.exit(1)

    @Log()
    def create_presence(self, account_name='Guest'):
        """
        Функция генерирует запрос о присутствии клиента
        :param account_name:
        :return:
        """
        out = {
            ACTION: PRESENCE,
            TIME: time.time(),
            USER: {
                ACCOUNT_NAME: account_name
            }
        }
        self.CLIENT_LOGGER.debug(f'Сформировано {PRESENCE} сообщение для пользователя {account_name}')
        return out

    @Log()
    def process_ans(self, message):
        """
        Функция разбирает ответ сервера
        :param message:
        :return:
        """
        self.CLIENT_LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        if RESPONSE in message:
            if message[RESPONSE] == 200:
                return '200 : OK'
            return f'400 : {message[ERROR]}'
        self.CLIENT_LOGGER.error(f'В ответе сервера отсутствует необходимое поле {RESPONSE}')
        raise ReqFieldMissingError(RESPONSE)

    @Log()
    def create_message(self, sock, account_name='Guest'):
        """
        Функция запрашивает текст сообщения и возвращает его.
        Так же завершает работу при вводе подобной комманды
        """
        message = input('Введите сообщение для отправки или \'!!!\' для завершения работы: ')
        if message == '!!!':
            sock.close()
            self.CLIENT_LOGGER.info('Завершение работы по команде пользователя.')
            print('Спасибо за использование нашего сервиса!')
            sys.exit(0)
        message_dict = {
            ACTION: MESSAGE,
            TIME: time.time(),
            ACCOUNT_NAME: account_name,
            MESSAGE_TEXT: message
        }
        self.CLIENT_LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')
        return message_dict

    @Log()
    def message_from_server(self, message):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        if ACTION in message and message[ACTION] == MESSAGE and \
                SENDER in message and MESSAGE_TEXT in message:
            print(f'Получено сообщение от пользователя '
                  f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
            self.CLIENT_LOGGER.info(f'Получено сообщение от пользователя '
                                    f'{message[SENDER]}:\n{message[MESSAGE_TEXT]}')
        else:
            self.CLIENT_LOGGER.error(f'Получено некорректное сообщение с сервера: {message}')


if __name__ == '__main__':
    client = Client()
    client.client_running()
