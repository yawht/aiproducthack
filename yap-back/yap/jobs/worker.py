import sys
from .app import celery_app

def _main():
    celery_app.start(argv=sys.argv[1:])


if __name__ == '__main__':
    _main()
