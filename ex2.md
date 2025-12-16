unsigned f(unsigned n)
{
  return (n==0) ? 1 : 2*f(n-1);
}

int main()
{
  unsigned x;
  x = f(3);
  return 0;
}

  nop // to get the CMD mode of logisim to work
  jmpi main 

f:
  // stack: [retAddr] n ...
  retAddr: 0
  n: 1
  ldi  a,n   // a == 1
  add  a,d   // a == 1+SP == &n
  ld   a,(a) // a == *a == *(&n) == n
  and  a,a   // a = (a & a), Z flag is affected
             // Z==1 iff a==0
  jzi  f_then // n == 0
  // n != 0, n > 0
  // else expr
  // f(n-1)
  // push n-1
  // regA already has n
  dec a // a == n-1
  dec d
  st  (d),a // push n-1
  // push ret addr
  dec d
  ldi a,. 5 +
  st  (d),a // push ret addr
  // jmpi f
  jmpi f
  // clean up the arg
  inc  d
  // make use of ret val
  add  a,a // a == 2*f(n-1)
  jmpi f_ret
f_then:
  ldi  a,1 // ret val of 1
  
f_ret:
  ld   b,(d) // b == retAddr
  inc  d
  jmp  b

main:
  // [x]
  x: 0
  dec  d
  // we are done allocating for the local var
  ldi  a,3
  dec  d
  st   (d),a
  dec  d
  ldi  a,. 5 +
  st   (d),a
  jmpi f
  inc  d
  ldi  b,x  // b == 0
  add  b,d  // b == &x
  st   (b),a  // x = f(3)
  inc  d    // dealloc x
  halt