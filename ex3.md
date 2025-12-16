unsigned strlen(const char *str)
{
  return (*str) ? 1+strlen(str+1) : 0;
}

int main()
{
  unsigned x;
  x = strlen("Tak");
  return 0;
}

nop
ldi  d,0
jmpi main

strlen:
  // [retAddr] str
  retAddr: 0
  str: 1
  ldi  c,str
  add  c,d
  ld   c,(c)  // c == str
  ld   b,(c)  // b == *(c) == *(str)
  and  b,b
  ldi  a,0    // let's assume it is an empty str
  jzi  strlen_isNull
  // is not null
  inc  c // a == str+1
  dec  d
  st   (d),c // push str+1
  dec  d
  ldi  a,. 5 +
  st   (d),a // push ret addr
  jmpi strlen
  inc  d
  // a == strlen(str+1)
  inc  a
strlen_isNull:
  ld   b,(d)
  inc  d
  jmp  b

__lit_str1:
  byte 84
  byte 97
  byte 107
  byte 0
main:
  // [x]
  dec  d
  x: 0
  dec  d
  ldi  a,__lit_str1
  st   (d),a // push "Tak"
  dec  d
  ldi  a,. 5 +
  st   (d),a  // push ret addr
  jmpi strlen
  inc  d
  ldi  b,x
  add  b,d
  st   (b),a  // x = strlen("Tak")
  inc  d
  halt