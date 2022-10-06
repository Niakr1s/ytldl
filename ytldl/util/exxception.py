def try_or(func, default=None):
    try:
        return func()
    except:
        return default
