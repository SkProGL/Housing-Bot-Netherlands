import sqlite3


class DatabaseControl:
    accommodation_default_table = {
        'website_name': 'TEXT PRIMARY KEY ',
        'price': 'INT',
        'price_1': 'INT',
        'price_2': 'INT',
        'url': 'TEXT',
        'url_1': 'TEXT',
        'url_2': 'TEXT'
    }
    user_default_table = {
        'chat_id': 'TEXT PRIMARY KEY',
        'first_name': 'TEXT',
        'last_name': 'TEXT',
        'register_date': 'DATETIME',
        'status': 'TEXT',
        'filter_id': 'INT2',
        'notifications': 'INT2'
    }

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_table(self, table_name, columns):
        columns_parsed = ', '.join([f'{col} {data_type}' for col, data_type in columns.items()])
        query = f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_parsed})'
        self.cursor.execute(query)
        self.conn.commit()

    def copy_table(self, from_table, table_name):
        self.delete(table_name, '1=1')
        query = f'INSERT OR REPLACE INTO {table_name} SELECT * FROM {from_table}'
        self.cursor.execute(query)
        self.conn.commit()

    def insert(self, table_name, data_columns):
        columns = ', '.join(data_columns.keys())
        placeholders = ', '.join(['?'] * len(data_columns))
        # use OR REPLACE to prevent primary key being duplicated
        query = f'INSERT OR REPLACE INTO {table_name} ({columns}) VALUES ({placeholders})'
        values = tuple(data_columns.values())
        self.cursor.execute(query, values)
        self.conn.commit()

    def select(self, table_name, condition=None, field='*'):
        query = f'SELECT {field} FROM {table_name}'
        if condition:
            query += f' WHERE {condition}'
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def select_column(self, column_name, table_name, condition=None):
        query = f'SELECT {column_name} FROM {table_name}'
        if condition:
            query += f' WHERE {condition}'

        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def select_columns(self, column_name, table_name, condition=None):
        query = f'SELECT {column_name} FROM {table_name}'
        if condition:
            query += f' WHERE {condition}'

        self.cursor.execute(query)
        return self.cursor.fetchall()

    def update(self, table_name, data: dict, condition):
        new_data = ', '.join([f'{col} = ?' for col in data.keys()])
        query = f'UPDATE {table_name} SET {new_data} WHERE {condition}'
        values = tuple(data.values())
        self.cursor.execute(query, values)
        self.conn.commit()

    def delete(self, table_name, condition):
        query = f'DELETE FROM {table_name} WHERE {condition}'
        self.cursor.execute(query)
        self.conn.commit()

    def exists(self, table_name, condition):
        query = f'SELECT * FROM {table_name} WHERE {condition}'
        self.cursor.execute(query)
        return self.cursor.fetchone() is not None

    def count_rows(self, table_name, column_name):
        query = f'SELECT COUNT({column_name}) FROM {table_name}'
        self.cursor.execute(query)
        count = self.cursor.fetchone()
        return count[0] if count is not None else 0

    def table_exists(self, table_name):
        query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        self.cursor.execute(query)
        return self.cursor.fetchone() is not None

    def delete_table(self, table_name):
        query = f"DROP TABLE {table_name}"
        self.cursor.execute(query)
        self.conn.commit()

    def close(self):
        self.conn.close()
