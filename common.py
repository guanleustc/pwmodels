#!/usr/bin/python

from __future__ import print_function
import sys, os
import bz2, re
import json, string
#from Crypto.Random import random
import random, re, itertools
import operator
import struct
from functools import reduce


BASE_DIR = os.getcwd()
sys.path.append(BASE_DIR)
MAX_INT = 2**64-1
DEBUG = True

import os

from os.path import (expanduser)
from math import sqrt
# opens file checking whether it is bz2 compressed or not.
import tarfile

home = expanduser("~")
pwd = os.path.dirname(os.path.abspath(__file__))
ROCKYOU_TOTAL_CNT = 32603388.0
pw_characters = string.ascii_letters + string.digits+string.punctuation + ' '

class random:
    @staticmethod
    def randints(s, e, n=1):
        """
        returns n uniform random numbers from [s, e]
        """
        assert e>=s, "Wrong range: [{}, {})".format(s, e)
        n = max(1, n)
        arr = [s + a%(e-s) for a in struct.unpack('<%dL'%n, os.urandom(4*n))]
        return arr

    @staticmethod
    def randint(s,e):
        """
        returns one random integer between s and e. Try using @randints in case you need
        multiple random integer. @randints is more efficient
        """
        return random.randints(s,e,1)[0]
    
    @staticmethod
    def choice(arr):
        i = random.randint(0, len(arr))
        return arr[i]
    
    @staticmethod
    def sample(arr, n, unique=False):
        if unique:
            arr = set(arr)
            assert len(arr)>n, "Cannot sample uniquely from a small array."
            if len(arr) == n:
                return arr;
            if n>len(arr)/2:
                res = list(arr)
                while len(res)>n:
                    del res[random.randint(0,len(res))]
            else:
                res = []
                arr = list(arr)
                while len(res)<n:
                    i = random.randint(0,len(arr))
                    res.append(arr[i])
                    del arr[i]
        else:
            return [arr[i] for i in random.randints(0, len(arr), n)]


def gen_n_random_num(n, MAX_NUM=MAX_INT, unique=True):
    """
    Returns @n @unique random unsigned integers (4 bytes) \
    between 0 and @MAX_NUM.
    """
    fmt = "<%dI" % n
    t =  struct.calcsize(fmt)
    D = [d%MAX_NUM for d in struct.unpack(fmt, os.urandom(t))]
    if unique:
        D = set(D)
        assert MAX_NUM>n, "Cannot have {0} unique integers less than {1}".format(n, MAX_NUM)
        while len(D)<n:
            print ("Number of collision: {}. Regenerating!".format(n-len(D)))
            fmt = "<%dI" % (n-len(D))
            t =  struct.calcsize(fmt)
            extra = struct.unpack(fmt, os.urandom(t))
            D |= set(d%MAX_NUM for d in extra)
        D = list(D)        
    return D


def sample_following_dist(handle_iter, n, totalf):
    """Samples n passwords following the distribution from the handle
    @handle_iter is an iterator that gives (pw,f) @n is the total
    number of samle asked for @totalf is the total number of users,
    which is euqal to sum(f for pw,f in handle_iter)
    As, handle_iterator is an iterator and can only traverse once, @totalf
    needs to be supplied to the funciton.
    
    Returns, an array of @n tuples (id, pw) sampled from @handle_iter.
    """
    multiplier = 1.0
    if totalf == 1.0:
        multiplier = 1e8
        # print "WARNING!! I don't except probabilities"

    totalf = totalf * multiplier
    print("# Population Size", totalf)
    A = gen_n_random_num(n, totalf, unique=False)
    A.sort(reverse=True)
    # Uniqueness check, non necessarily required, but not very
    # computationally intensive
    assert len(A) == n, "Not enough randomnumbers generated"\
        "Requried {}, generated only {}".format(n, len(A))
    # if not all(A[i] != A[i-1] for i in range(1,n,1)):
    #     for i in range(1,n,1):
    #         if A[i] == A[i-1]:
    #             print i, A[i], A[i-1]
    j = 0
    sampled = 0
    val = A.pop()
    # print handle_iter
    for w,f in handle_iter:
        j += f*multiplier
        if not A: break
        while val<j:
            sampled += 1
            if sampled %5000 == 0:
                print ("Sampled:",sampled)
            yield (val, w)
            if A:
                val = A.pop()
            else:
                break

    print ("# Stopped at:", w, f, j, '\n')
    while A and val<j:
        yield (val, w)
        if A:
            i, val = A.pop()
        else:
            break


def MILLION(n):
    return n*10e6

def sort_dict(D):
    # sort the dictionary by keys and returns a tuple list
    return sorted(D.items(), key=operator.itemgetter(1))

# returns the type of file.
def file_type(filename):
    magic_dict = {
        "\x1f\x8b\x08": "gz",
        "\x42\x5a\x68": "bz2",
        "\x50\x4b\x03\x04": "zip"
    }
    max_len = max(len(x) for x in magic_dict)
    with open(filename) as f:
        file_start = f.read(max_len)
    for magic, filetype in magic_dict.items():
        if file_start.startswith(magic):
            return filetype
    return "no match"


def open_(filename, mode='r'):
    if mode == 'w':
        type_ = filename.split('.')[-1]
    else:
        type_ = file_type(filename)
    if type_ == "bz2":
        f = bz2.BZ2File(filename, mode)
    elif type_ == "gz":
        f = tarfile.open(filename, mode)
    else:
        f = open(filename, mode);
    return f;

def getallgroups(arr, k=-1):
    """
    returns all the subset of @arr of size less than equalto @k
    the return array will be of size \sum_{i=1}^k nCi, n = len(arr)
    """
    if k<0:
        k = len(arr)
    return itertools.chain.from_iterable(itertools.combinations(set(arr), j)
                                    for j in range(1,k+1))
    

def is_asciistring(s):
    try:
        s.decode('ascii')
        return True
    except (UnicodeDecodeError, UnicodeEncodeError) as e:
        # warning("UnicodeError:", s, str(e))
        return False

def get_line(file_object, limit=-1, pw_filter=lambda x: True):
    regex = re.compile(r'\s*([0-9]+) (.*)$')
    i = 0
    for l in file_object:
        if limit>0 and limit<=i:
            break
        m = regex.match(l)
        if not m:
            warning ("REGEX FAIL: ", l)
        c, w = m.groups()
        c = int(c)
        w = w.replace('\x00', '\\x00')
        try:
            w = w.decode('utf-8', errors='replace')
        except UnicodeDecodeError:
            #try with latin1
            warning("Error in decoding: ({} {}). Line: {}. Ignoring!"\
                    .format(w, c, l))
            continue
        if w and pw_filter(w) and c>0:
            i += 1
            yield w,c
        else:
            pass
            #warning ("Filter Failed or malformed string: ", w, c)


def open_get_line(filename, limit=-1, **kwargs):
    with open_(filename) as f:
        for w,c in get_line(f, limit, **kwargs):
            yield w, c

# TODO - Optimize the tokenization process
regex = r'([A-Za-z_]+)|([0-9]+)|(\W+)'
def print_err( *args ):
    if DEBUG:
        sys.stderr.write(' '.join([str(a) for a in args])+'\n')

def tokens(w):
    T = []
    while w:
        m = re.match(regex, w)
        T.append(m.group(0))
        w = w[len(T[-1]):]
    return T


def whatchar(c):
    if c.isalpha(): return 'L';
    if c.isdigit():
        return 'D';
    else:
        return 'Y'

def mean_sd(arr):
    s = sum(arr)
    s2 = sum([x * x for x in arr])
    n = len(arr)
    m = s / float(n)
    sd = sqrt(float(s2) / n - m * m)
    return m, sd

def prod(arr):
    return reduce(operator.mul, arr, 1)

def convert2group(t, totalC):
    return t + random.randint(0, (MAX_INT-t)/totalC) * totalC
    
def warning(*objs):
    if DEBUG:
        print("WARNING: ", *objs, file=sys.stderr)

# assumes last element in the array(A) is the sum of all elements
def getIndex(p, A):
    p %= A[-1]
    i = 0;
    for i, v in enumerate(A):
        p -= v;
        if p < 0: break
    return i


if __name__ == "__main__":    
    print(list(getallgroups([1,2,3,4,5,6,7,8,9], 5)))
    
    # unittest.main()

