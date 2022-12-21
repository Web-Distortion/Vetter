import sys

in_file = sys.argv[1]
out_file = sys.argv[2]
body = open(in_file, 'rb').read()
fp = open(out_file, 'wb')

unchunked_body = b''
chunk_size = 0


pos = body.find(b'\r\n')
chunk_size = int(body[:pos], 16)
body = body[pos+2:]
while( chunk_size != 0 ):
    unchunked_body = unchunked_body + body[0:chunk_size]
    body = body[chunk_size:]
    body = body[2:]
    pos = body.find(b'\r\n')
    chunk_size = int(body[:pos], 16)
    body = body[pos+2:]


# body = body[pos+2:]

fp.write(unchunked_body)
