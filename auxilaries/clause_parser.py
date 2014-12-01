import re
import os
import sys

#clause='copyout(a,b) copyin(b) independent sync'
clause='present_or_copyin(a,b) present_or_copyout(c) create(seq)'

regex = re.compile(r'([A-Za-z0-9_]+)([\ ]*)(\((.+?)\))*')
for i in regex.findall(clause):
    print '%'.join(i)
