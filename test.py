#!/usr/bin/python

from bits import Number

if __name__ == '__main__':
    #x = Number.var('x', 64)
    #res = ((~x | Number.const(0x7AFAFA697AFAFA69, 64)) & Number.const(0xA061440A061440, 64)) \
    #   + ((x & Number.const(0x10b1050504, 64)) | Number.const(0x1010104, 64))
    #print res

    x = Number.var('x', 4)
    y = Number.var('y', 4)
    print x+y
