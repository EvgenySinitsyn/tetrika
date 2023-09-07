from aiohttp.web import RouteTableDef, HTTPFound, View
import aiohttp_jinja2
from utils import check_session, process_string
from base import User, objects, File, Post
import uuid
import aiohttp
from peewee import DoesNotExist
import asyncio
import json


routes = RouteTableDef()


@routes.view('/')
class IndexView(View):
    @check_session()
    async def get(self):
        return HTTPFound(self.request.app.router['file'].url_for())


@routes.view('/register', name='register')
class RegisterView(View):

    @aiohttp_jinja2.template('register.html')
    async def get(self):
        return {}

    @aiohttp_jinja2.template('register.html')
    async def post(self):
        body = await self.request.post()
        session = uuid.uuid4()
        user, result = await User.add(body.get('login'), body.get('password1'), body.get('password2'), session)
        if not user:
            return {'error': result}
        response = HTTPFound(self.request.app.router['login'].url_for())
        response.set_cookie('session_id', user.sessions)
        return response


@routes.view('/file', name='file')
class FileView(View):
    @aiohttp_jinja2.template('upload_file.html')
    @check_session()
    async def get(self):
        return {}

    @aiohttp_jinja2.template('upload_file.html')
    @check_session()
    async def post(self):
        reader = await self.request.multipart()
        field = await reader.next()
        filename = field.filename
        if field.headers[aiohttp.hdrs.CONTENT_TYPE] != 'text/csv':
            return {'error': 'Поддерживаются только text/csv файлы'}
        user = await objects.get(User, sessions=self.request.cookies.get('session_id'))
        file = await File.add(user, filename)
        start = True
        strings_quantity = 0
        while True:
            string = await field.readline()
            if not string:
                break

            string = string.decode().strip()
            if start:
                if not string == 'userId,title,body':
                    file.status = 'incorrect_data'
                    await objects.update(file)
                    break
                start = False
                continue
            strings_quantity += 1
            asyncio.create_task(process_string(string, file))
        file.strings_quantity = strings_quantity
        await objects.update(file)
        return {}


@routes.view('/logout', name='logout')
class LogoutView(View):
    async def post(self):
        try:
            user = await objects.get(User, sessions=self.request.cookies.get('session_id'))
            user.sessions = ''
            await objects.update(user)
        except DoesNotExist as ex:
            pass
        return HTTPFound(self.request.app.router['login'].url_for())


@routes.view('/login', name='login')
class LoginView(View):

    @aiohttp_jinja2.template('login.html')
    async def get(self):
        return {}

    @aiohttp_jinja2.template('login.html')
    async def post(self):
        body = await self.request.post()
        session = await User.check_user_credentials(body.get('login'), body.get('password'))
        if not session:
            return {'error': 'Неверные логин или пароль.'}
        response = HTTPFound(self.request.app.router['file'].url_for())
        response.set_cookie('session_id', session)
        return response


@routes.view('/files', name='files_status')
class FilesStatusView(View):
    @aiohttp_jinja2.template('files_status.html')
    @check_session()
    async def get(self):
        user = await objects.get(User, sessions=self.request.cookies.get('session_id'))
        files = await objects.execute(File.select().where(File.user == user))
        return {'files': files}


@routes.view('/strings', name='strings')
class FileStringsStatusView(View):
    @aiohttp_jinja2.template('strings.html')
    @check_session()
    async def get(self):
        user = await objects.get(User, sessions=self.request.cookies.get('session_id'))
        file_id = self.request.query.get('file')
        strings = await objects.execute(Post.select().join(File).join(User).where(
            Post.file == file_id, User.id == user).order_by(Post.id))
        response_strings = []
        for string in strings:
            string_response_body = json.loads(string.response_text) if string.response_text else None
            response_string = {'string': string.csv_string,
                               'message': string.error}
            if string_response_body and string.response_status == 201:
                response_string['message'] = {
                    'result': f'Статус: {string.response_status}, ответ: {string.response_text}',
                    'userId': int(string_response_body['userId']),
                    'postId': string_response_body['id']
                }
            response_strings.append(response_string)
        return {'strings': response_strings}
