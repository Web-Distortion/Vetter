import os
import json
import re
from bs4 import BeautifulSoup, element
import protobuf_util

original_page_folder = '../'

sites = [{'domain': 'amazon.com', 'url': 'https://www.amazon.com/'}]

tag_id = 0
res_id = 0
prev_js_id = 0

html_url = ''

url_to_tag_id = {}
url_to_res_id = {}
id_to_inline_js = {}
is_html_first_js = True

tag_ids = {}
res_ids = {}
inline_js = {}
chunks = {}


def rewrite_css(css):
    pattern = r"url\([\"']?([./a-gi-z][^/].*?)[\"']?\)"
    replacement = r"url(" + html_url + r"\1)"
    first = re.sub(pattern, replacement, css, flags=re.IGNORECASE)
    
    pattern = r"url\([\"']?(//.*?)[\"']?\)"
    replacement = r"url(http:" + r"\1)"
    return re.sub(pattern, replacement, first, flags=re.IGNORECASE)

def traverse_dom(node):
    global tag_id, res_id, id_to_inline_js, prev_js_id, is_html_first_js
    for child in node.children:
        data_src = False
        if isinstance(child, element.Tag):
            node_style = child.get('style')
            if (node_style != None and node_style != ''):
                child['style'] = rewrite_css(node_style)
            if (child.name == 'img' or child.name == 'script' or child.name == 'iframe' or child.name == 'link'):
                if (child.name == 'link'):
                    if ((child['rel'][0] == 'canonical') or (child['rel'][0] == 'alternate')):
                        original_src = ''
                    else:
                        original_src = child.get('href')
                else:
                    original_src = child.get('src')
                    if (original_src == None or original_src == ''):
                        original_src = child.get('data-src')
                        data_src = True
                if (original_src != None and original_src != ''):
                    if (child.name == 'script'):
                        del child['src']
                        if (data_src):
                            del child['data-src']
                    elif (child.name == 'link'):
                        child['href'] = ''
                    else:
                        child['src'] = ''
                        if ( data_src ):
                            child['data-src'] = ''
                    
                    # if ( child.name == 'img' or child.name == 'iframe' or child.name == 'link' ):
                    child['tag_id'] = tag_id
                    if (original_src in url_to_res_id):
                        url_to_tag_id[original_src].append(tag_id)
                    else:
                        url_to_res_id[original_src] = res_id
                        url_to_tag_id[original_src] = [tag_id]
                        res_id += 1
                    if child.name == 'script':
                        id_to_inline_js[tag_id] = {}
                        id_to_inline_js[tag_id]['code'] = 'NO_INLINE'
                        id_to_inline_js[tag_id]['prev_js_id'] = -1 if is_html_first_js else prev_js_id
                        is_html_first_js = False
                        prev_js_id = tag_id
                    tag_id += 1
                    # else:
                    #     url_to_tag_id[original_src] = ['null']
                elif child.name == 'script':
                    js_code = child.string
                    if js_code != '':
                        child.string = ''
                        child['tag_id'] = tag_id
                        id_to_inline_js[tag_id] = {}
                        id_to_inline_js[tag_id]['code'] = js_code
                        id_to_inline_js[tag_id]['prev_js_id'] = -1 if is_html_first_js else prev_js_id
                        is_html_first_js = False
                        prev_js_id = tag_id
                        tag_id += 1
            traverse_dom(child)

def similar(w1, w2):
    w1 = w1 + ' ' * (len(w2) - len(w1))
    w2 = w2 + ' ' * (len(w1) - len(w2))
    return sum(1 if i == j else 0 for i, j in zip(w1, w2)) / float(len(w1))

for site in sites:
    domain = site['domain']
    url = site['url']

    record_dir = '%s/%s' % (original_page_folder, domain)

    # recorded folder to be copied and rewritten
    recorded_folder = record_dir
    
    # temp folder to store rewritten protobufs
    os.system("rm -rf rewritten")
    os.system( "cp -r " + recorded_folder + " rewritten" )

    files = os.listdir("rewritten")

    tag_id = 0
    res_id = 0
    prev_js_id = 0

    tag_ids = {}
    res_ids = {}
    inline_js = {}
    chunks = {}

    for filename in files:
        # print(domain, filename)

        url_to_tag_id = {}
        url_to_res_id = {}
        id_to_inline_js = {}
        is_html_first_js = True

        meta = protobuf_util.get_meta('./rewritten/%s' % filename)
        # print(meta)
        html_url = 'http' if meta['scheme'] == 'HTTP' else 'https'
        html_url += ('://' + meta['Host'] + meta['first_line'].split(' ')[1])

        # print(html_url)
        response_body = protobuf_util.get_response_body('./rewritten/%s' % filename)
        # print(response_body)

        with open('./rewritten/response', 'wb') as f:
            f.write(response_body)
        

        if 'html' in meta['Content-Type']:
            if 'chunked' in meta['Transfer-Encoding']:
                # break
                os.system('python3 unchunk.py rewritten/response rewritten/response1')
                os.system('mv rewritten/response1 rewritten/response')
            if 'gzip' in meta['Content-Encoding']:
                os.system('gzip -d -c rewritten/response > rewritten/response1')
                os.system('mv rewritten/response1 rewritten/response')
            try:
                if similar(html_url, url) > 0.85:
                    soup = BeautifulSoup(open('rewritten/response', 'r', encoding='utf-8'), "html.parser")
                    traverse_dom(soup)
                        
                    output = soup.prettify()
                    # print(output)
                    chunked = output.split('\n')
                    clean_chunked = []
                    for line in chunked:
                        clean_chunked.append(line.replace("</script>", "<\/script>"))
                    
                    res_ids[html_url] = url_to_res_id
                    tag_ids[html_url] = url_to_tag_id
                    inline_js[html_url] = id_to_inline_js
                    chunks[html_url] = clean_chunked
            except Exception as e:
                print(e)
    # break
    json.dump(chunks, open('./chunked_html/%s.json' % (domain), 'w'))
    json.dump(res_ids, open('./url_ids/%s_res_id.json' % (domain), 'w'))
    json.dump(tag_ids, open('./url_ids/%s_tag_id.json' % (domain), 'w'))
    json.dump(inline_js, open('./inline_js/%s.json' % (domain), 'w'))
    os.system("rm -rf rewritten")
