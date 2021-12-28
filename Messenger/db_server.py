from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import mapper, sessionmaker
import datetime
from Messenger.common.variables import SERVER_DATABASE


# Класс - серверная база данных:
class ServerStorage:
    Base = declarative_base()

    # Таблица всех пользователей
    class AllUsers(Base):
        __tablename__ = 'Users'
        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True)
        last_login = Column(DateTime)

        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

        def __repr__(self):
            return f'<User({self.id}, {self.name}, {self.last_login})>'

    # Активные пользователи:
    class ActiveUsers(Base):
        __tablename__ = 'Active_users'
        id = Column(Integer, primary_key=True)
        user = Column(ForeignKey('Users.id'), unique=True)
        ip_address = Column(String)
        port = Column(Integer)
        login_time = Column(DateTime)

        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

        def __repr__(self):
            return f'<User({self.user}, {self.ip_address}, {self.port}, {self.login_time})>'

    # История входов
    class LoginHistory(Base):
        __tablename__ = 'Login_history'
        id = Column(Integer, primary_key=True)
        name = Column(ForeignKey('Users.id'))
        date_time = Column(DateTime)
        ip = Column(String)
        port = Column(Integer)

        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

        def __repr__(self):
            return f'<User({self.name}, {self.ip}, {self.port}, {self.date_time})>'

    # Создаём движок базы данных
    # SERVER_DATABASE - sqlite:///server_base.db3
    # echo=False - отключает вывод на экран sql-запросов)
    # pool_recycle - по умолчанию соединение с БД через 8 часов простоя обрывается
    # Чтобы этого не случилось необходимо добавить pool_recycle=7200 (переустановка
    # соединения через каждые 2 часа)

    database_engine = create_engine(SERVER_DATABASE, echo=False, pool_recycle=7200)
    Base.metadata.create_all(database_engine)

    def __init__(self):
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()
        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        # Когда устанавливаем соединение, очищаем таблицу активных пользователей
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    # Функция выполняющаяся при входе пользователя. Если пользователь не зарегистрирован,
    # то он добавляется в таблицу Users.
    # Пользователь добавляется в таблицу Active_users и сохраняется история входов в таблице Login_history
    def user_login(self, username, ip_address, port):
        result = self.session.query(self.AllUsers).filter_by(name=username)

        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if result.count():
            user = result.first()
            user.last_login = datetime.datetime.now()
        # Если нет, то создаём нового пользователя
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        self.session.commit()

    # Функция, выполняющаяся при отключении пользователя. Пользователь удаляется из таблицы Active_users
    def user_logout(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    # Функция, возвращающая список всех пользователей со временем последнего входа.
    def users_list(self):
        query = self.session.query(self.AllUsers.name, self.AllUsers.last_login)
        return query.all()

    # Функция, возвращающая список активных пользователей
    def active_users_list(self):
        query = self.session.query(
            self.AllUsers.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.AllUsers)
        return query.all()

    # Функция, возвращающая историю входов по конкретному пользователю, если пользователь не задан, то по всем
    def login_history(self, username=None):
        query = self.session.query(self.AllUsers.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.AllUsers)
        if username:
            query = query.filter(self.AllUsers.name == username)
        return query.all()


# Отладка
if __name__ == '__main__':
    test_db = ServerStorage()
    # Выполняем "подключение" пользователя
    test_db.user_login('client_1', '192.168.1.4', 8080)
    test_db.user_login('client_2', '192.168.1.5', 7777)

    # Выводим список кортежей - активных пользователей
    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_users_list())

    # Выполняем "отключение" пользователя
    test_db.user_logout('client_1')
    # И выводим список активных пользователей
    print(' ---- test_db.active_users_list() after logout client_1 ----')
    print(test_db.active_users_list())

    # Запрашиваем историю входов по пользователю
    print(' ---- test_db.login_history(client_1) ----')
    print(test_db.login_history('client_1'))

    # и выводим список известных пользователей
    print(' ---- test_db.users_list() ----')
    print(test_db.users_list())
