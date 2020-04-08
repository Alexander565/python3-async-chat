#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
from time import sleep


class ServerProtocol(asyncio.Protocol):
    login: str = None
    logins: list = []
    history_messages: list = []
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
            self.update_history(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "")
                if self.login_valid(self.login):
                    self.logins.append(self.login)
                    self.transport.write(f"Привет, {self.login}!\n".encode())
                    self.send_history()
                else:
                    self.transport.write(f"Логин {self.login} занят, попробуйте другой\n".encode())
                    sleep(1.5)
                    self.login = None
                    self.transport.close()
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        self.transport.write("Введите ваш логин в формате <login: ваш логин>:\t".encode())
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        for login in self.logins:
            if login == self.login:
                self.logins.remove(login)
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"

        for user in self.server.clients:
            user.transport.write(message.encode())

    def login_valid(self, login: str):
        for client_login in self.logins:
            if login == client_login:
                return False
        return True

    def update_history(self, message: str):
        self.history_messages.append(f"{self.login}: {message}\n")
        if len(self.history_messages) > 10:
            del self.history_messages[0]

    def send_history(self):
        for message in self.history_messages:
            self.transport.write(message.encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
