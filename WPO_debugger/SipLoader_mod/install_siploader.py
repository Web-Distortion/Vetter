import os
import protobuf_util
import json

original_page_folder = '..'
scheduled_page_folder = '..'

sites = [{'domain': 'amazon.com', 'url': 'https://www.amazon.com/'}]

for site in sites:
    domain = site['domain']
    url = site['url']

    record_dir = '%s/%s' % (original_page_folder, domain)
    out_dir = '%s/%s_reordered'  % (scheduled_page_folder, domain)

    if os.path.exists(out_dir):
        print('%s already exists.' % (out_dir))
        continue

    recorded_folder = record_dir
    rewritten_folder = out_dir

    try:
        url_res_ids = json.load(open('./url_ids/%s_res_id.json' % (domain), 'rb'))
        # print(url_res_ids)

        url_tag_ids = json.load(open('./url_ids/%s_tag_id.json' % (domain), 'rb'))
        # print(url_tag_ids)

        inline_js = json.load(open('./inline_js/%s.json' % (domain), 'rb'))
        # print(inline_js)

    except Exception as e:
        print(e)
        graph = {}
        url_tag_ids = {}
        inline_js = {}
        continue    

    chunked_htmls = json.load(open('./chunked_html/%s.json' % (domain), 'rb'))
    # print(chunked_htmls)    

    # temp folder to store rewritten protobufs
    os.system("rm -rf rewritten")
    os.system( "cp -r " + recorded_folder + " rewritten" )

    files = os.listdir("rewritten")

    for filename in files:
        print(domain, filename)
    
        scheduler_init = "<script>\n"

        meta = protobuf_util.get_meta('./rewritten/%s' % filename)
        # print(meta)
        url = 'http' if meta['scheme'] == 'HTTP' else 'https'
        url += ('://' + meta['Host'] + meta['first_line'].split(' ')[1])
        object_url = url
        # print(url)
        response_body = protobuf_util.get_response_body('./rewritten/%s' % filename)
        # print(response_body)

        with open('./rewritten/response', 'wb') as f:
            f.write(response_body)

        if ( ("html" in meta['Content-Type']) or ("javascript" in meta['Content-Type']) or ("css" in meta['Content-Type'])):
            if 'chunked' in meta['Transfer-Encoding']:
                os.system( "python unchunk.py rewritten/response rewritten/response1" )
                os.system( "mv rewritten/response1 rewritten/response" )
                # remove transfer-encoding chunked header from original file since we are unchunking
                # os.system( "../bin/removeheader rewritten/" + filename + " Transfer-Encoding" )
                # print(meta)
                protobuf_util.remove_header('./rewritten/%s' % filename, 'Transfer-Encoding')
            if 'gzip' in meta['Content-Encoding']:
                os.system('gzip -d -c rewritten/response > rewritten/response1')
                os.system('mv rewritten/response1 rewritten/response')
            elif 'br' in meta['Content-Encoding']:
                os.system('mv rewritten/response rewritten/response.br')
                os.system('brotli -d rewritten/response.br -o rewritten/response')
                os.system('rm rewritten/response.br')
            if 'html' in meta['Content-Type']:
                if object_url in url_tag_ids and object_url in chunked_htmls and object_url in inline_js:
                    scheduler_init = scheduler_init + "window.siploaderTagId = " + json.dumps(url_tag_ids[object_url]) +";\n"
                    scheduler_init = scheduler_init + "window.siploaderResId = " + json.dumps(url_res_ids[object_url]) +";\n"
                    scheduler_init = scheduler_init + "window.siploaderChunkedHTML = " + json.dumps(chunked_htmls[object_url]) + ";\n"
                    scheduler_init = scheduler_init + "window.siploaderInlineJS= " + json.dumps(inline_js[object_url]) + ";\n"
                    scheduler_init = scheduler_init + "window.HTMLName = \"" + object_url + "\";\n"
                    scheduled_html_f = open('./rewritten/response', 'w')
                    scheduled_html_f.write(scheduler_init)
                    scheduled_html_f.close()
                    os.system('cat scheduler_siploader.js >> ./rewritten/response')
            elif 'css' in meta['Content-Type']:
                site_name = object_url[0:object_url.rfind('/') + 1]
                os.system("python3 rewrite_css_file.py rewritten/response '" + site_name + "' > rewritten/cssfile")
                os.system("mv rewritten/cssfile rewritten/response")
            if 'gzip' in meta['Content-Encoding']:
                os.system("gzip -c rewritten/response > rewritten/result")
            elif 'br' in meta['Content-Encoding']:
                os.system("brotli rewritten/response -o rewritten/result")
            else:
                os.system("cp rewritten/response rewritten/result")
            
            size = os.path.getsize('rewritten/result')
            protobuf_util.replace_body('./rewritten/%s' % filename, 'rewritten/result')
            protobuf_util.update_header('./rewritten/%s' % filename, b'Content-Length', bytes(str(size), encoding = "utf8"))
            os.system("rm rewritten/result")
        protobuf_util.update_header('./rewritten/%s' % filename, b'Access-Control-Allow-Origin', b'*')
        os.system("rm rewritten/response")

    os.system("mv rewritten " + rewritten_folder)   
    