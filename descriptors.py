import logging
logger = logging.getLogger('server')


class Port:
    def __set__(self, instance, value):
        if not 1023 < value < 65536:
            logger.critical(
                f'Попытка запуска сервера/клиента с указанием неподходящего порта {value}.'
                f'Допустимы адреса с 1024 до 65535. Сервер/клиент завершает работу')
            exit(1)
        instance.__dict__[self.attr_name] = value

    def __set_name__(self, owner, attr_name):
        self.attr_name = attr_name
