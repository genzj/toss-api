# -*- encoding: utf-8 -*-
import os.path

import aio_etcd as etcd
from sanic import Sanic

from toss_api.config import DebugConfig, ProductionConfig
from toss_api.view.api import api_bp


def create_app(debug=False):
    app = Sanic('toss', load_env='TOSS_')

    if debug:
        app.config.from_object(DebugConfig)
    else:
        app.config.from_object(ProductionConfig)

    app.config.DEBUG = debug

    if os.environ.get('TOSS_CONFIGURATION_FILE', None) and os.path.isfile(os.environ['TOSS_CONFIGURATION_FILE']):
        app.config.from_envvar('TOSS_CONFIGURATION_FILE')

    # environment configuration got highest priority for docker deployment convenience
    # so use explicitly loading again
    app.config.load_environment_vars(prefix='TOSS_')

    def create_etcd_client(loop):
        if hasattr(app, 'etcd'):
            return
        app.etcd = etcd.Client(host=app.config.ETCD_HOSTNAME, port=app.config.ETCD_PORT, loop=loop)

    @app.listener('after_server_start')
    def loop_created_cb(app, loop):
        loop.call_soon(create_etcd_client, loop)

    app.blueprint(api_bp)

    return app


if __name__ == "__main__":
    create_app(debug=True).run(host="0.0.0.0", port=8000, debug=True)
