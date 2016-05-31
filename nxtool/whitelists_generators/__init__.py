def modify_search(func):
    def wrapper(provider, wl):
        search = provider.search
        ret = func(provider, wl)
        provider.search = search
        return ret
    return wrapper
