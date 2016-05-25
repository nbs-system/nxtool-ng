def modify_search(func):
    def wrapper(provider):
        search = provider.search
        ret = func(provider)
        provider.search = search
        return ret
    return wrapper
