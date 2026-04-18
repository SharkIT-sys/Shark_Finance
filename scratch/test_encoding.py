
s = "SincronizaciÃƒÆ’Ã‚Â³n"
try:
    # Try multiple rounds of decoding if needed
    print(f"Original: {s}")
    b1 = s.encode('latin-1')
    print(f"Bytes 1: {b1}")
    s1 = b1.decode('utf-8')
    print(f"Decoded 1: {s1}")
    b2 = s1.encode('latin-1')
    print(f"Bytes 2: {b2}")
    s2 = b2.decode('utf-8')
    print(f"Decoded 2: {s2}")
except Exception as e:
    print(f"Error: {e}")
