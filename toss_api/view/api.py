# -*- encoding: utf-8 -*-
import asyncio
from asyncio import InvalidStateError, CancelledError
from json import dumps

from sanic.response import json
from sanic.log import logger

from toss_api.db.model import read_results, watch_toss, toss1, toss2
from toss_api.view import api_bp

L = logger.getChild(__name__)


@api_bp.route('/toss/1')
async def bp_root(request):
    app = request.app
    result = await toss1(app)
    return json({'result': result, 'total': await read_results(app)})


@api_bp.route('/toss/2')
async def bp_root(request):
    app = request.app
    result = await toss2(app)
    return json({
        'result': result,
        'total': await read_results(app)
    })


@api_bp.websocket('/toss/ws')
async def ws(request, ws):
    app = request.app
    updates = [
        asyncio.ensure_future(watch_toss(app, key=key, index=None)) for key in ('H', 'T', 'HT', 'TH')
    ]
    recv = asyncio.ensure_future(ws.recv())

    while True:
        try:
            await asyncio.wait(
                updates + [recv, ],
                return_when=asyncio.FIRST_COMPLETED
            )
        except CancelledError:
            recv.cancel()
            for update in updates:
                update.cancel()
            break

        if recv.done():
            message = recv.result().strip()
            if message == 'toss1':
                result = await toss1(app)
            elif message == 'toss2':
                result = await toss2(app)
            elif message == 'refresh':
                result = 'ok'
            else:
                result = 'unknown action'
            await ws.send(dumps({
                'action': message,
                'result': result,
                # 'total': await read_results(app)
            }))
            recv = asyncio.ensure_future(ws.recv())

        for idx, update in enumerate(updates):
            if update.done():
                change = update.result()
                key = change.key.rsplit('/', 1)[-1]
                await ws.send(dumps({
                    'updated': {
                        'key': key,
                        'value': change.value,
                        'index': change.modifiedIndex,
                    },
                    'total': await read_results(app)
                }))
                updates[idx] = asyncio.ensure_future(watch_toss(app, key=key, index=change.modifiedIndex + 1))
