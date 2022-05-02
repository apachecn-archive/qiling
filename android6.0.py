#!/usr/bin/env python3

from qiling import *
from qiling.os.mapper import QlFsMappedObject
from collections import defaultdict

class Fake_maps(QlFsMappedObject):
    def __init__(self, ql):
        self.ql = ql
    def read(self, size):
        stack = next(filter(lambda x : x[3]=='[stack]', self.ql.mem.map_info))
        return ('%x-%x %s\n' % (stack[0], stack[1], stack[3])).encode()
    def fstat(self):
        return defaultdict(int)
    def close(self):
        return 0

if __name__ == "__main__":
    rootfs = "android6.0"
    test_binary = "android6.0/bin/arm64_android_jniart"
    env = {"ANDROID_DATA":"/data", "ANDROID_ROOT":"/system"}
    ql = Qiling([test_binary], rootfs, env, multithread = True)
    ql.add_fs_mapper("/proc/self/task/2000/maps", Fake_maps(ql))
    ql.run()
