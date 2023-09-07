import peewee
import peewee_async
from config import CONFIG
from datetime import datetime
from hashlib import sha256
import uuid


database = peewee_async.MySQLDatabase(CONFIG['mysql_base'], user=CONFIG['mysql_user'],
                                      host=CONFIG['mysql_name_host'], password=CONFIG['mysql_password'],
                                      charset=CONFIG['mysql_charset'], port=CONFIG['mysql_port'])
objects = peewee_async.Manager(database)

FILE_STATUS = {
    'in_queue': 0,
    'in_processing': 1,
    'done': 2,
    'done_with_errors': 3,
    'incorrect_data': 4,
}


class User(peewee.Model):
    id = peewee.PrimaryKeyField()
    create_tm = peewee.DateTimeField()
    login = peewee.CharField(unique=True)
    password = peewee.CharField()
    sessions = peewee.TextField()

    class Meta:
        database = database

    @classmethod
    async def add(cls, login, password1, password2, session=None):
        user = None
        result = 'Введены разные пароли'
        if password1 != password2:
            return user, result
        password = sha256(password1.encode()).hexdigest()
        try:
            user = await objects.create(cls, create_tm=datetime.now(),
                                        login=login,
                                        password=password,
                                        sessions=session if session else '')
            result = True
        except peewee.OperationalError as ex:
            result = 'Не удалось'
        except peewee.IntegrityError as ex:
            result = 'Пользователь с такоим логином уже есть'
        return user, result

    @classmethod
    async def check_user_credentials(cls, login, password):
        try:
            user = await objects.get(cls, login=login)
        except peewee.DoesNotExist:
            return
        password = sha256(password.encode()).hexdigest()
        if user.password != password:
            return
        user.sessions = uuid.uuid4()
        await objects.update(user)
        return user.sessions


class File(peewee.Model):
    id = peewee.PrimaryKeyField()
    create_tm = peewee.DateTimeField()
    name = peewee.CharField()
    user = peewee.ForeignKeyField(User)
    status = peewee.IntegerField()
    errors_quantity = peewee.IntegerField(default=0)

    class Meta:
        database = database

    @classmethod
    async def add(cls, user, file_name):
        file = await objects.create(File,
                                    create_tm=datetime.now(),
                                    name=file_name,
                                    user=user,
                                    status=FILE_STATUS['in_queue'])
        return file


class Post(peewee.Model):
    id = peewee.PrimaryKeyField()
    create_tm = peewee.DateTimeField()
    file = peewee.ForeignKeyField(File)
    csv_string = peewee.TextField()
    response_text = peewee.TextField(null=True)
    response_status = peewee.IntegerField(null=True)
    error = peewee.CharField(null=True)

    class Meta:
        database = database

    @classmethod
    async def add(cls, file, csv_string, response_text=None, response_status=None, error=None):
        post = await objects.create(
            cls,
            create_tm=datetime.now(),
            file=file,
            csv_string=csv_string,
            response_text=response_text,
            response_status=response_status,
            error=error
        )
        return post


User.create_table(True)
File.create_table(True)
Post.create_table(True)

objects.database.allow_sync = False
