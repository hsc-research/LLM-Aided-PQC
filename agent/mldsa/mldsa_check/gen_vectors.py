#!/usr/bin/env python3
import random, sys
Q = 8380417
GAMMA2 = {2:(Q-1)//88, 3:(Q-1)//32, 5:(Q-1)//32}
def decompose(r, sec_lvl):
    g2 = GAMMA2[sec_lvl]; t = 2*g2
    r %= Q; a0 = r % t
    if a0 > g2: a0 -= t
    if r - a0 == Q-1: a1 = 0; a0 -= 1
    else: a1 = (r - a0)//t
    return a1, a0 % Q
def main():
    n = int(sys.argv[1]) if len(sys.argv)>1 else 200
    sec = int(sys.argv[2]) if len(sys.argv)>2 else 3
    random.seed(1234)
    vals = [0,1,Q-1,(Q-1)//2,261889,785665,523776,190464]
    vals += [random.randint(0,Q-1) for _ in range(n-len(vals))]
    fdi=open("di.hex","w"); fa1=open("a1.hex","w"); fa0=open("a0.hex","w"); fn=open("nvec.txt","w")
    for di in vals:
        a1,a0 = decompose(di,sec)
        fdi.write(f"{di:06x}\n"); fa1.write(f"{a1:06x}\n"); fa0.write(f"{a0:06x}\n")
    fdi.close(); fa1.close(); fa0.close()
    fn.write(str(len(vals))); fn.close()
    print(f"wrote {len(vals)} vectors (sec={sec}) to di.hex/a1.hex/a0.hex")
if __name__=="__main__": main()
