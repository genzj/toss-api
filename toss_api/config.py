# -*- encoding: utf-8 -*-


class DefaultConfig(object):
    ETCD_HOSTNAME = 'localhost'
    ETCD_PORT = 2379
    COIN = 'T' * 4 + 'H' * 6
    ETCD_KEY_PREFIX = 'v1'


class DebugConfig(DefaultConfig):
    pass


class ProductionConfig(DefaultConfig):
    pass
