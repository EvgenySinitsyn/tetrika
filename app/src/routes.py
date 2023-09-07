from aiohttp.web import RouteTableDef, HTTPFound, View
import aiohttp_jinja2
from utils import check_session, process_string
from base import User, FILE_STATUS, objects, File
import uuid
import aiohttp
from peewee import DoesNotExist
import asyncio


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
        while True:
            string = await field.readline()
            if not string:
                break
            string = string.decode().strip()
            if start:
                if not string == 'userId,title,body':
                    file.status = FILE_STATUS['incorrect_data']
                    await objects.update(file)
                    break
                start = False
                continue
            asyncio.create_task(process_string(string, file))
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
