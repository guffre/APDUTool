# APDU Fuzzer
An APDU tool for smartcard / PCSC fuzzing. It also includes scripting (inspired by gscriptor)
The advantage of using the GUI tool is if you have no idea what you are doing, this breaks
each of the bytes into discrete values. This is the tool I "wish I had" when I was doing an 
ATM hacking challenge by Red Balloon Security. Yes, reading the docs and knowing exactly what
command to send is great, but sometimes brute forcing is great too.

caveat: I wrote this on my flight home from defcon so the code is super-hacky. This push
4? years later is just because I wanted it to run on Python 3.

# apdufuzz.py
Commandline APDU fuzzer. Allows you to bruteforce bytes and calculates Lc value automatically
There's very bare error-checking. It requires two-byte, hex values.

    Example usage:
     
       First reader  Auto-calc Lc            range/comma seperation
                   \             \ 
                    v             v             v     v     v    v
      ./apdufuzz.py 0 00 a4 04 00 xx a0 00 00 00-03 00,10-1a,77 ee-ff 00
