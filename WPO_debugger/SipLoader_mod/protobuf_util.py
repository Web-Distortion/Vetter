import http_record_pb2
import chardet

def get_meta(filename):
    response = http_record_pb2.RequestResponse()
    meta = {'scheme': '', 'first_line': '', 'Host': '','Content-Type': '', 'Content-Encoding': '', 'Transfer-Encoding': ''}
    with open(filename, 'rb') as f:
        response.ParseFromString(f.read())
        # print(response)
        if response.HasField('scheme'):
            meta['scheme'] = 'HTTP' if response.scheme == 1 else 'HTTPS'
        if response.HasField('request'):
            if response.request.HasField('first_line'):
                code = chardet.detect(response.request.first_line)
                meta['first_line'] = str(response.request.first_line, code['encoding'])
            for header in response.request.header:
                if header.HasField('key') and header.HasField('value'):
                    # print(header.key)
                    # print(header.value)
                    if header.key == b'Host':
                        code = chardet.detect(header.value)
                        meta['Host'] = str(header.value, code['encoding'])
        if response.HasField('response'):
            for header in response.response.header:
                if header.HasField('key') and header.HasField('value'):
                    # print(header.key)
                    # print(header.value)
                    code = chardet.detect(header.value)
                    if header.key == b'Content-Type':
                        meta['Content-Type'] = str(header.value, code['encoding'])
                    elif header.key == b'Content-Encoding':
                        meta['Content-Encoding'] = str(header.value, code['encoding'])
                    elif header.key == b'Transfer-Encoding':
                        meta['Transfer-Encoding'] = str(header.value, code['encoding'])

    return meta

def remove_header(filename, rm_header):
    response = http_record_pb2.RequestResponse()
    with open(filename, 'rb') as f:
        response.ParseFromString(f.read())
        # print(response)
        if response.HasField('response'):
            index = None
            i = 0
            for header in response.response.header:
                if header.HasField('key') and header.HasField('value'):
                    # print(header.key)
                    # print(header.value)
                    code = chardet.detect(header.key)
                    # print(header.key)
                    # print(code)
                    # print(header.key.decode(code['encoding'], 'ignore'))
                    if header.key.decode(code['encoding'], 'ignore') == rm_header:
                        index = i
                        # print(index)
                        break
                i += 1
            if index is not None:
                # print(index)
                del response.response.header[index]
    with open(filename, 'wb') as f:
        # print(response)
        f.write(response.SerializeToString())

def replace_body(filename, body_filename):
    response = http_record_pb2.RequestResponse()
    with open(filename, 'rb') as f:
        response.ParseFromString(f.read())
        # print(response)
        if response.HasField('response') and response.response.HasField('body'):
            with open(body_filename,  'rb') as fb:
                body = fb.read()
                response.response.body = body
    with open(filename, 'wb') as f:
        # print(response)
        f.write(response.SerializeToString())

def update_header(filename, key, value):
    response = http_record_pb2.RequestResponse()
    with open(filename, 'rb') as f:
        response.ParseFromString(f.read())
        # print(response.response.header)
        has_header = False
        if response.HasField('response'):
            for header in response.response.header:
                if header.HasField('key') and header.HasField('value'):
                    # print(header.key)
                    # print(header.value)
                    # print(header.key.decode(code['encoding'], 'ignore'))
                    if header.key == key:
                        header.value = value
                        has_header = True
                        break
            if not has_header:
                header = http_record_pb2.HTTPHeader()
                header.key = key
                header.value = value
                response.response.header.extend([header])
    with open(filename, 'wb') as f:
        # print(response.response.header)
        f.write(response.SerializeToString())

def get_response_body(filename):
    ret = None
    response = http_record_pb2.RequestResponse()
    with open(filename, 'rb') as f:
        response.ParseFromString(f.read())
        if response.HasField('response') and response.response.HasField('body'):
            ret = response.response.body
    
    return ret
