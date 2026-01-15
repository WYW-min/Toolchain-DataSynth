from dataclasses import dataclass as origin_dataclass, fields, FrozenInstanceError


def ddataclass(cls=None, **kwargs):
    def wrap(cls):
        cls = origin_dataclass(cls, **kwargs)

        # 1. 取值 obj[key]
        def __getitem__(self, key):
            if not hasattr(self, key):
                raise KeyError(f"'{self.__class__.__name__}' has no key '{key}'")
            return getattr(self, key)

        # 2. 赋值 obj[key] = val
        def __setitem__(self, key, value):
            if not hasattr(self, key):
                raise KeyError(f"'{self.__class__.__name__}' has no key '{key}'")
            if kwargs.get("frozen", False):
                raise FrozenInstanceError(f"cannot assign to field '{key}'")
            setattr(self, key, value)

        # 3. 删除 del obj[key]
        def __delitem__(self, key):
            if not hasattr(self, key):
                raise KeyError(f"'{self.__class__.__name__}' has no key '{key}'")
            if kwargs.get("frozen", False):
                raise FrozenInstanceError(f"cannot delete field '{key}'")
            delattr(self, key)

        # 4. 支持 in 判断: "key" in obj
        def __contains__(self, key):
            return hasattr(self, key)

        # 5. 获取所有字段名: obj.keys()
        def keys(self):
            return tuple(f.name for f in fields(self))

        # 6. 获取所有字段值: obj.values()
        def values(self):
            return tuple(getattr(self, f.name) for f in fields(self))

        # 7. 获取键值对: obj.items() 支持遍历
        def items(self):
            return tuple((f.name, getattr(self, f.name)) for f in fields(self))

        # 8. 快速转为纯字典: obj.to_dict()
        def to_dict(self):
            return {f.name: getattr(self, f.name) for f in fields(self)}

        # 绑定所有增强方法
        cls.__getitem__ = __getitem__
        cls.__setitem__ = __setitem__
        cls.__delitem__ = __delitem__
        cls.__contains__ = __contains__
        cls.keys = keys
        cls.values = values
        cls.items = items
        cls.to_dict = to_dict
        return cls

    if cls is None:
        return wrap
    return wrap(cls)
