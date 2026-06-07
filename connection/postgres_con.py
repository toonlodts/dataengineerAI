import psycopg2

class PostgresConnection:
    def __init__(self, host="localhost", database="postgres", user="postgres", password="postgres", port=5432):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None
    
    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host = self.host,
                database = self.database,
                user = self.user,
                password = self.password,
                port = self.port,
            )
            self.connection.autocommit = True
            print("Connected to Postgres!")
        except Exception as e:
            print("Failed to connect: ", e)

    def get_connection(self):
        return self.connection
    
    def close(self):
        if self.connection:
            self.connection.close()
            print("Postgres connection closed!")