import sqlite3


def get_all_object_fields(tb_name):
    field_names = [
        attr
        for attr in dir(tb_name)
        if not callable(getattr(tb_name, attr))
        and not attr.startswith("__")
        and attr != "key"
    ]

    field_attrs = {attr: getattr(tb_name, attr) for attr in field_names}
    return field_attrs


class Field:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is not None and self.value is not None:
            query = (
                f"SELECT {self.name} FROM {obj.__class__.__name__} WHERE pk={obj.pk}"
            )
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            row = cursor.execute(query).fetchone()[0]
            conn.close()
            return row

        else:
            return self.value

    def __set__(self, obj, value):
        tb_name = obj.__class__.__name__
        tb = eval(tb_name)
        field_attrs = get_all_object_fields(tb)
        field_attrs[self.name] = value

        query_val = f"'{value}'" if isinstance(value, str) else value

        query = f"UPDATE {tb_name} SET {self.name}={query_val} WHERE pk={obj.pk}"
        print(query)

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()


class CharField(Field):
    def __init__(self):
        self.value = ""

    def __set__(self, obj, value):
        if not isinstance(value, str):
            raise TypeError("CharField only takes str value")
        super().__set__(obj, value)


class IntegerField(Field):
    def __init__(self):
        self.value = 0

    def __set__(self, obj, value):
        if not isinstance(value, int):
            raise TypeError("IntegerField only takes integer value")
        super().__set__(obj, value)


class BaseModel:
    key = []

    def __init__(self, pk):
        if not isinstance(pk, int):
            raise TypeError("pk must be integer")

        if pk in self.__class__.key:
            raise ValueError("pk is already taken.")

        self.pk = pk
        self.__class__.key.append(pk)

        tb_name = self.__class__.__name__
        tb = eval(tb_name)

        field_attrs = get_all_object_fields(tb)

        conn = sqlite3.connect("database.db", isolation_level=None)
        cursor = conn.cursor()

        field_querys = []
        for k, value in field_attrs.items():
            query = ""
            if k == "key":
                query = "pk INTEGER PRIMARY KEY"
            else:
                if isinstance(value, str):
                    query = f"{k} text"
                elif isinstance(value, int):
                    query = f"{k} INTEGER"

            field_querys.append(query)

        tb_query = f"CREATE TABLE IF NOT EXISTS {tb_name}("
        for idx, q in enumerate(field_querys, 1):
            if idx == len(field_querys):
                tb_query += q + ")"
            else:
                tb_query += q + ","
        cursor.execute(tb_query)

        set_pk_query = f"INSERT INTO {tb_name}(pk) VALUES({self.pk})"
        try:
            cursor.execute(set_pk_query)
        except:
            pass
        finally:
            conn.commit()
            conn.close()

