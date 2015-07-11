from bottle import route, run, request
from urllib.request import urlopen
from hashlib import sha1
import pickle
import redis


URL = 'http://api.openweathermap.org/data/2.5/weather'
TIME_TO_EXPIRE = 15

cache = redis.StrictRedis()


def get_qs():
    return '&'.join('='.join((key, val)) for key, val in request.query.items())


def caching_middleware(app):
    def get_key():
        if 'reload' in request.query:
            del request.query['reload']
        qs = get_qs()
        name = app.__name__
        key = str((name, qs)).encode()
        return sha1(key).hexdigest()

    def wrapped_app(*args, **kwargs):
        reload = 'reload' in request.query
        key = get_key()

        if key not in cache or reload:
            print('add into cache')
            resp = app(*args, **kwargs)
            cache.set(key, pickle.dumps(resp))
            cache.expire(key, TIME_TO_EXPIRE)

        return pickle.loads(cache.get(key))

    return wrapped_app


@route('/weather')
@caching_middleware
def weather():
    qs = get_qs()
    resp = urlopen('{url}?{qs}'.format(url=URL, qs=qs)).read()
    return resp


if __name__ == '__main__':
    print('Examples:')
    print('http://127.0.0.1:8080/weather?q=Kiev')
    print('http://127.0.0.1:8080/weather?q=Kiev&units=metric')
    print('http://127.0.0.1:8080/weather?q=London')
    run()