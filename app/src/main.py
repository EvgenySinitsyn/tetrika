import aiohttp_jinja2
import jinja2
from aiohttp.web import Application, run_app
from routes import routes

app = Application()
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

if __name__ == '__main__':
    app.add_routes(routes)
    run_app(app, port=5000)
