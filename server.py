from aiohttp import web
import os

async def handle(request):
    return web.Response(text="🤖 Crypto Bot is running!")

app = web.Application()
app.router.add_get('/', handle)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, port=port)