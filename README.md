# APDUTool
An APDU tool for smartcard / PCSC fuzzing. Also does scripting. Inspired by gscriptor

# apdufuzz.py
Command-line APDU fuzzer. Allows you to bruteforce bytes and calculates Lc value automatically
There's very bare error-checking. It requires two-byte, hex values and will not work with "0" or "103", for example.

    Example usage:
     
       First reader  Auto-calc Lc            range/comma seperation
                   \             \ 
                    v             v             v     v     v    v
      ./apdufuzz.py 0 00 a4 04 00 xx a0 00 00 00-03 00,10-1a,77 ee-ff 00
