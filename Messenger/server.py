"""Программа-сервер"""
import socket
import sys
import json
import logging
import Messenger.log.server_log_config
from Messenger.decorators import Log
from Messenger.errors import ReqFieldMissingError, IncorrectDataRecivedError
from common.variables import ACTION, ACCOUNT_NAME, RESPONSE, MAX_CONNECTIONS, \
    PRESENCE, TIME, USER, ERROR, DEFAULT_PORT, RESPONDEFAULT_IP_ADDRESSSE
from common.utils import get_message, send_message


class Server:
    def __init__(self, params=[]):
        self.SERVER_LOGGER = logging.getLogger('server')
        self.init_params(params)

    @Log()
    def init_params(self, params):
        try:
            if '-p' in params:
                self.listen_port = int(params[params.index('-p') + 1])
            else:
                self.listen_port = DEFAULT_PORT
            if self.listen_port < 1024 or self.listen_port > 65535:
                self.SERVER_LOGGER.critical(f'Попытка запуска сервера с указанием недопустимого порта'
                                            f'{self.listen_port} Допустимы адреса с 1024 до 65535. Сервер завершает работу.')
                sys.exit(1)
        except IndexError:
            self.SERVER_LOGGER.critical(
                f'После параметра -\'p\' необходимо указать номер порта.Сервер завершает работу.')
            sys.exit(1)

        try:
            if '-a' in params:
                self.listen_address = params[params.index('-a') + 1]
            else:
                self.listen_address = ''
        except IndexError:
            self.SERVER_LOGGER.critical(
                f'После параметра -\'a\' необходимо указать номер порта.Сервер завершает работу.')
            sys.exit(1)

    @Log()
    def init_sock(self):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.bind((self.listen_address, self.listen_port))

    @Log()
    def server_running(self):
        self.init_sock()
        self.transport.listen(MAX_CONNECTIONS)
        self.SERVER_LOGGER.info(f'Запущен сервер, порт для подключений: {self.listen_port}, '
                                f'адрес с которого принимаются подключения: {self.listen_address}. '
                                f'Если адрес не указан, принимаются соединения с любых адресов.')
        while True:
            client, client_address = self.transport.accept()
            self.SERVER_LOGGER.info(f'Установлено соедение с {client_address}')
            try:
                message_from_client = get_message(client)
                self.SERVER_LOGGER.debug(f'Получено сообщение {message_from_client}')
                response = self.process_client_message(message_from_client)
                self.SERVER_LOGGER.info(f'Сформирован ответ клиенту {response}')
                send_message(client, response)
                self.SERVER_LOGGER.debug(f'Соединение с клиентом {client_address} закрывается.')
                client.close()
            except json.JSONDecodeError:
                self.SERVER_LOGGER.error(f'Не удалось декодировать Json строку, полученную от '
                                         f'клиента {client_address}. Соединение закрывается.')
                client.close()
            except IncorrectDataRecivedError:
                self.SERVER_LOGGER.error(f'От клиента {client_address} приняты некорректные данные. '
                                         f'Соединение закрывается.')
                client.close()

    @Log()
    def process_client_message(self, message):
        '''
        Обработчик сообщений от клиентов, принимает словарь -
        сообщение от клинта, проверяет корректность,
        возвращает словарь-ответ для клиента

        :param message:
        :return:
        '''
        self.SERVER_LOGGER.debug(f'Разбор сообщения от клиента : {message}')
        if ACTION in message and message[ACTION] == PRESENCE and TIME in message \
                and USER in message and message[USER][ACCOUNT_NAME] == 'Guest':
            return {RESPONSE: 200}
        return {
            RESPONDEFAULT_IP_ADDRESSSE: 400,
            ERROR: 'Bad Request'
        }


if __name__ == '__main__':
    server = Server(sys.argv)
    server.server_running()
