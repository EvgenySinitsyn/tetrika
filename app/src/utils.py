import functools
from base import objects, User, Post
from peewee import DoesNotExist
from aiohttp.web import HTTPFound
from datetime import datetime
import asyncio
import aiohttp

SEMAPHORE = asyncio.Semaphore(7)
URL = 'https://jsonplaceholder.typicode.com/posts'


async def send_post(user_id, title, body, post):
    await SEMAPHORE.acquire()
    start = datetime.now().timestamp()
    async with aiohttp.ClientSession() as session:
        data = {
            'title': title,
            'body': body,
            'userId': user_id,
        }
        response = await session.post(URL, data=data)
    time_of_work = datetime.now().timestamp() - start
    await asyncio.sleep(1 - time_of_work)
    SEMAPHORE.release()
    post.response_text = await response.text()
    post.response_status = response.status
    await objects.update(post)


async def set_post_error(error, post, file):
    post.error = error
    await objects.update(post)
    file.errors_quantity += 1
    await objects.update(file)


async def process_string(string, file):
    post = await Post.add(file, string)
    try:
        user_id, title, body = string.split(',')
    except Exception as ex:
        await set_post_error('Некорректные данные', post, file)
        return
    if not user_id.isdigit():
        await set_post_error('Неверный тип данных', post, file)
        return
    asyncio.create_task(send_post(user_id, title, body, post))


def check_session():
    def wrapper(func):
        @functools.wraps(func)
        async def wrapped(instance):
            try:
                await objects.get(User, sessions=instance.request.cookies.get('session_id'))
            except DoesNotExist as ex:
                return HTTPFound('/login')
            return await func(instance)
        return wrapped
    return wrapper
