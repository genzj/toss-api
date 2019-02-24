# -*- encoding: utf-8 -*-
from random import choice, choices

from etcd import EtcdKeyNotFound, EtcdCompareFailed
from sanic import Sanic

TOSS_ANSWER_KEY = '/toss/result/'


def generate_key(app: Sanic, result: str):
    return app.config.ETCD_KEY_PREFIX + TOSS_ANSWER_KEY + result


async def read_toss(app, result, key=None):
    key = key or generate_key(app, result)
    try:
        v = int((await app.etcd.read(key)).value)
    except EtcdKeyNotFound:
        await app.etcd.write(key, 0, prevExist=False)
        v = 0
    return v


async def read_results(app):
    candidates = ['T', 'H', 'TH', 'HT']
    return {
        r: await read_toss(app, r) for r in candidates
    }


async def save_toss(app, result, key=None):
    key = generate_key(app, result)

    while True:
        try:
            v = await read_toss(app, result, key=key)
            await app.etcd.write(key, v + 1, prevValue=v)
        except EtcdCompareFailed:
            pass
        else:
            break


async def watch_toss(app, key, index):
    answer = await app.etcd.watch(generate_key(app, key), index=index)
    return answer


async def toss1(app):
    result = choice(app.config.COIN)
    await save_toss(app, result)
    return result


async def toss2(app):
    while True:
        result = ''.join(choices(app.config.COIN, k=2))
        for r in result:
            await save_toss(app, r)
        if result[0] != result[1]:
            break
    await save_toss(app, result)
    return result
