import hashlib
import json
import yaml


def get_md5(text: str) -> str:
    # 1. 创建 MD5 对象
    md5_obj = hashlib.md5()
    # 2. 传入字节数据（必须 encode）
    md5_obj.update(text.encode("utf-8"))
    # 3. 获取 16 进制字符串格式的摘要
    return md5_obj.hexdigest()


def format_dict(d: dict, mode="json"):
    if mode not in ["json", "yaml"]:
        raise ValueError("mode must be 'json' or 'yaml'")
    if mode == "json":
        return json.dumps(d, indent=4, ensure_ascii=False)
    else:
        return yaml.dump(d, allow_unicode=True, sort_keys=False)
