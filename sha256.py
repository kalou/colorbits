#!/usr/bin/python
import math
import struct

from bits import Number, UnknownBit

def padStr(string):
    s = string
    l = len(string)
    s += '\x80'
    if len(s) % 56:
        s += '\x00' * (56 - len(s) % 64)
    s += struct.pack('!Q', l*8)
    return s

def makeMsg(string):
    s = padStr(string)
    l = len(s) / 4
    return [Number.const(v) for (n, v)
            in enumerate(struct.unpack('!%dL' % l, s))]

def padMsg(arr):
    """Pad a hash for further hashing"""
    l = 32*len(arr)
    arr.append(Number.const(0x80000000))
    arr += [Number.const(0)] * 6
    arr.append(Number.const(l))
    print len(arr)
    return arr

def binary(arr):
    return struct.pack('!8L', *arr)

def makeHash(arr):
    return binary(arr).encode('hex')

class SHA256:
    RC = [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2]

    k = map(Number.const, RC)

    def hash(self, msg):
        """Use makeMsg to have an array of numbers ready here"""
        h0 = Number.const(0x6a09e667)
        h1 = Number.const(0xbb67ae85)
        h2 = Number.const(0x3c6ef372)
        h3 = Number.const(0xa54ff53a)
        h4 = Number.const(0x510e527f)
        h5 = Number.const(0x9b05688c)
        h6 = Number.const(0x1f83d9ab)
        h7 = Number.const(0x5be0cd19)

        for t in range(0, len(msg), 16):
            print 'Round {}'.format(t)
            w = msg[t:t+16] + [Number.const(0)] * 48
            for i in range(16, 64):
                print 'Initround {}'.format(i)
                s0 = w[i-15].rightrotate(7) ^ w[i-15].rightrotate(18) ^ (w[i-15] >> 3)
                s1 = w[i-2].rightrotate(17) ^ w[i-2].rightrotate(19) ^ (w[i-2] >> 10)
                w[i] = w[i-16] + s0 + w[i-7] + s1

            a = h0
            b = h1
            c = h2
            d = h3
            e = h4
            f = h5
            g = h6
            h = h7

            for i in range(64):
                print 'Subround {}'.format(i)
                S1 = e.rightrotate(6) ^ e.rightrotate(11) ^ e.rightrotate(25)
                ch = (e & f) ^ ((~e) & g)
                temp1 = h + S1 + ch + self.k[i] + w[i]
                S0 = a.rightrotate(2) ^ a.rightrotate(13) ^ a.rightrotate(22)
                maj = (a & b) ^ (a & c) ^ (b & c)
                temp2 = S0 + maj

                h = g
                g = f
                f = e
                e = d + temp1
                d = c
                c = b
                b = a
                a = temp1 + temp2

            h0 = h0 + a
            h1 = h1 + b
            h2 = h2 + c
            h3 = h3 + d
            h4 = h4 + e
            h5 = h5 + f
            h6 = h6 + g
            h7 = h7 + h
        return [h0, h1, h2, h3, h4, h5, h6, h7]

if __name__ == '__main__':
    header_hex = ("01000000" +
     "81cd02ab7e569e8bcd9317e2fe99f2de44d49ab2b8851ba4a308000000000000" +
     "e320b6c2fffc8d750423db8b1eb942ae710e951ed797f7affc8892b0f1fc122b" +
     "c7f5d74d" +
     "f2b9441a" +
     "42a14695") # // <_ ZOB _>

    header_bin = header_hex.decode('hex')
    print len(header_bin)

    msg = makeMsg(header_bin)

    # CNT = msg[19]
    msg[19].bits[0] = UnknownBit('a')
    #msg[19].bits[1] = UnknownBit('b')
    #msg[19].bits[2] = UnknownBit('c')
    #msg[19].bits[3] = UnknownBit('d')
    #msg[19].bits[4] = UnknownBit('e')
    #msg[19].bits[5] = UnknownBit('f')
    #msg[19].bits[6] = UnknownBit('g')
    #msg[19].bits[7] = UnknownBit('h')

    sha = SHA256()
    h = sha.hash(msg)
    print makeHash(h)
    # assert(makeHash(h) == 'b9d751533593ac10cdfb7b8e03cad8babc67d8eaeac0a3699b82857dacac9390')

    msg2 = padMsg(h)
    print msg2
    h = sha.hash(msg2)
    print makeHash(h)

    print h
