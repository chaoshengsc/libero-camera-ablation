"""运行 LeRobot 的 migrate_policy_normalization,但先把"声明为 tuple、JSON 里是 list"的配置字段转成 tuple。
不改 LeRobot 源码;效果等同于 draccus 正常解码配置。"""
import dataclasses
import sys
import typing

import lerobot.processor.migrate_policy_normalization as mig

_orig = mig.make_policy_config

def _tuple_fixed(policy_type, **kw):
    cfg = _orig(policy_type, **kw)
    hints = typing.get_type_hints(type(cfg))
    for f in dataclasses.fields(cfg):
        v = getattr(cfg, f.name)
        if isinstance(v, list) and "tuple" in str(hints.get(f.name, "")):
            setattr(cfg, f.name, tuple(v)); print(f"[tuplefix] {f.name}: list -> tuple {tuple(v)}")
    return cfg

# 入口保护:多进程以 spawn 方式启动时子进程会重新导入本文件,没有保护会重复执行主流程
if __name__ == "__main__":
    mig.make_policy_config = _tuple_fixed
    sys.exit(mig.main())
