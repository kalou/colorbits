import time
import itertools
import traceback

t = time.time()

def timeit(where):
    global t
    diff = time.time() - t
    if diff > .02:
        print('{}: {}'.format(where, diff))
    t = time.time()

def simplify_pos(pos):
    """
    """
    #print 'simplify %s' % pos
    #traceback.print_stack()

    new = POS()
    removed = []
    for term in pos.terms[:]:
        while len(term) > 1 and UnsetBit() in term:
            term.remove(UnsetBit()) # 0+x = x
        if SetBit() in term or not term: # a+1 = 1
            pos.terms.remove(term)
        for bit in term: # a+a' = 1
            if ~bit in term:
                pos.terms.remove(term)
                break

    # reduce common sets
    for term in pos.terms:
        #print '-> eval %s' % term
        # any set bit in terms: term is removed
        if SetBit() in term:
            #print 'skip 1'
            continue

        # any unset bit is alone and makes the whole POS
        # evaluate to zero
        if UnsetBit() in term:
            return UnsetBit()

        if term in new.terms:
            #print 'skip double term'
            continue

        for other in pos.terms:
            if other == term:
                #print 'skip self comparison'
                continue
            #print 'compare with %s' % other

            # [1]
            if len(other.difference(term)) == 1 and \
               other.difference(term) == ~term.difference(other):
                #print 'diff 1 and not'
                bit = other.difference(term).pop()
                other.remove(bit)
                term.remove(~bit)

            # [2]
            if len(term) == 1 and ~term.copy().pop() in other:
                #print '%s // %s in %s ?' % (term, ~term, other)
                other.remove(~term.copy().pop())

            # if this contains any other smaller term, the other one
            # is sufficient
            if other.issubset(term):
                #print 'subset for %s is %s' % (term, other)
                break
        else:
            #print 'append %s' % term
            new.terms.append(term)

        # [1]
        # (a+b+c..z)(a+b+c+..z') = aa+ab+ac+..az' + ba+bb+..bz' + .. za+zb+zc+..zz' <= 0
        #                        = a(1+b+c+..z') + b(a+1+..z') + z(a+b+c+..+y)
        #                        = a+b+...+y + z(a+b+c+d+e+..+y)
        #                        = a+b+...+y (1+z)
        #                        = a+b+...+y

        # [2]
        # (a'+b'+c'...) & a & b & c ...
        # -> ~(a&b&c) & (a&b&c)

    if len(new.terms) == 1 and len(new.terms[0]) == 1:
        #print 'One left in %s, extracting' % new.terms
        return new.terms[0].pop()
    elif any(len(t) == 0 for t in new.terms):
        #print 'Empty terms'
        return UnsetBit()
    elif len(new.terms) == 0:
        #print 'Full (no terms)'
        return SetBit()

    #print 'simplified to %s' % new
    return new

class SumTerm(set):
    def __invert__(self):
        # Not a real sum inversion as per DeMorgan's
        # TODO gen ProductTerm(nots) ?
        return SumTerm(~x for x in self)

    def union(self, other):
        for bit in other:
            if ~bit in self:
                return SumTerm([SetBit()])
        return super(SumTerm, self).union(other)

class POS:
    def __init__(self, bit=None, terms=None):
        if bit != None:
            self.terms = [SumTerm([bit])]
        elif terms:
            self.terms = [x.copy() for x in terms]
        else:
            self.terms = []

    def __and__(self, other):
        x = POS(terms=self.terms)
        if isinstance(other, Bit):
            other = POS(bit=other)
        x.terms += other.terms
        return simplify_pos(x)

    def __or__(self, other):
        x = POS()
        if isinstance(other, Bit):
            other = POS(bit=other)

        # Distributive (a+b)(c+d) + (e+f)(g+h) =
        #                               A
        #              (A+a+b)(A+c+d)
        #              ((e+f)(g+h)+a+b) ...((e+f)(g+h)+c+d)
        #              ((a+e+f)(a+g+h)+b)(...)
        #              ((a+e+f+b)(a+g+h+b))(..)
        for xs in self.terms:
            for s in other.terms:
                #print '%s - %s' % (xs, s)
                x.terms.append(xs.union(s))
        #print x.terms
        return simplify_pos(x)

    def __xor__(self, other):
        #print '%s ^ %s' % (self, other,)
        return (self | other) & ~(self & other)

    def __invert__(self):
        # Expand to sum of products
        # (a+b+c)(d+e+f)(x+y) =
        # (ad+ae+af+bd+be+bf+cd+ce+cf)(x+y) =
        # xad+xae+xaf+xbd+xbe+xbf+xcd+xce+xcf+..y..
        # Then negate:
        # (~x+~a+~d)(~x+~a+~e)(~x+..
        x = POS(terms=self.terms)
        x.terms = [~SumTerm(p) for p in itertools.product(*self.terms)]

        return simplify_pos(x)

    def __str__(self):
        s = ''
        for x in self.terms:
            if len(x) > 1:
                s += '({})'.format('+'.join([str(b) for b in x]))
            elif len(x) == 1:
                s += str(x.copy().pop())
            else:
                return '0'
        return s

    def __repr__(self):
        return str(self)

class Bit:
    def __hash__(self):
        return hash(str(self._not) + self.v)

    def __ne__(self, other):
        return not self == other

class UnknownBit(Bit):
    def __init__(self, v):
        if not isinstance(v, str):
            raise Exception('unknown bit should be variable name')
        self.v = v
        self._not = False

    def __xor__(self, other):
        if isinstance(other, KnownBit):
            return other ^ self

        if other == self:
            return UnsetBit()
        elif other == ~self:
            return SetBit()

        return (self | other) & ~(self & other)

    def __and__(self, other):
        if isinstance(other, KnownBit):
            return other & self

        if other == self:
            return self
        elif other == ~self:
            return UnsetBit()

        return POS(bit=self) & other

    def __or__(self, other):
        if isinstance(other, KnownBit):
            return other | self

        if other == self:
            return self
        elif other == ~self:
            return SetBit()

        return POS(bit=self) | other

    def __invert__(self):
        x = UnknownBit(self.v)
        x._not = not self._not
        return x

    def __eq__(self, other):
        if isinstance(other, Bit):
            return (self.v == other.v) and \
                   (self._not == other._not)

    def __str__(self):
        ret = self.v
        if self._not:
            ret += "'"
        return ret

    def __repr__(self):
        return str(self)

    def __nonzero__(self):
        return True

class KnownBit(Bit):
    pass

class UnsetBit(KnownBit):
    v = '0'
    _not = False
    def __xor__(self, other):
        return other

    def __and__(self, other):
        return self

    def __or__(self, other):
        return other

    def __invert__(self):
        return SetBit()

    def __nonzero__(self):
        return False

    def __repr__(self):
        return '0'

    def __eq__(self, other):
        return isinstance(other, UnsetBit)

class SetBit(KnownBit):
    v = '1'
    _not = False
    def __xor__(self, other):
        return ~other

    def __and__(self, other):
        return other

    def __or__(self, other):
        return self

    def __invert__(self):
        return UnsetBit()

    def __nonzero__(self):
        return True

    def __repr__(self):
        return '1'

    def __eq__(self, other):
        return isinstance(other, SetBit)

class Number:
    def __init__(self, bits, size=32):
        self.bits = bits
        self.size = size

    @classmethod
    def var(cls, name, size=32):
        n = cls([], size=size)
        for i in range(size-1, -1, -1):
            n.bits.append(UnknownBit('{}.{}'.format(name, i)))
        return n

    @classmethod
    def const(cls, value, size=32):
        n = cls([], size=size)
        for i in range(size-1, -1, -1):
            if value & (1 << i):
                n.bits.append(SetBit())
            else:
                n.bits.append(UnsetBit())
        return n

    def val(self):
        return int(''.join(str(x) for x in self.bits), 2)

    def __str__(self):
        return ' '.join(str(x) for x in self.bits)

    def __repr__(self):
        return str(self)

    def __or__(self, other):
        bits = map(lambda (a,b) : a | b, zip(self.bits, other.bits))
        return Number(bits, self.size)

    def __and__(self, other):
        bits = map(lambda (a,b) : a & b, zip(self.bits, other.bits))
        return Number(bits, self.size)

    def __xor__(self, other):
        bits = map(lambda (a,b) : a ^ b, zip(self.bits, other.bits))
        return Number(bits, self.size)

    def __invert__(self):
        bits = map(lambda x: ~x, self.bits)
        return Number(bits, self.size)

    def __rshift__(self, n):
        bits = [UnsetBit()] * n + self.bits[:self.size-n]
        return Number(bits, self.size)

    def __lshift__(self, n):
        bits = self.bits[n:] + [UnsetBit()] * n
        return Number(bits, self.size)

    def leftrotate(self, n):
        bits = self.bits[n:] + self.bits[:n]
        return Number(bits, self.size)

    def rightrotate(self, n):
        bits = self.bits[self.size-n:] + self.bits[:self.size-n]
        return Number(bits, self.size)

    def __int__(self):
        return sum(2**i for i in range(self.size) if self.bits[self.size-1-i])

    def __cmp__(self, other):
        return int(self).__cmp__(int(other))

    def __nonzero__(self):
        return int(self) != 0

    def __add__(self, other):
        carry = self & other
        result = self ^ other
        ## This is not working
        for i in range(self.size):
            print 'carry %s/%s' % (carry, int(carry))
            shiftedcarry = carry << 1
            carry = result & shiftedcarry
            #print 'shiftedcarry %s' % shiftedcarry
            result ^= shiftedcarry
        #print 'result %s' % result
        return result
