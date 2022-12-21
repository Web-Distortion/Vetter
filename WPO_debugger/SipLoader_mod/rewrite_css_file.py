import sys
import re
from urllib import parse

in_file = sys.argv[1]
site = sys.argv[2]

url_bracket_pattern = r"(url\(.*?\))"
url_pattern = r"url\([\"']?(.*?)[\"']?\)"

def url_repl(matchobj):
    print('url("%s")' % parse.urljoin(site, matchobj.group(1)))
    return 'url("%s")' % parse.urljoin(site, matchobj.group(1))

def url_bracket_repl(matchobj):
    matched_url_bracket = matchobj.group(1)
    matched_url = re.search(url_pattern, matched_url_bracket)
    # print(matched_url.group(1))
    if matched_url.group(1).startswith('data:'):
        return matched_url_bracket
    re.sub(url_pattern, url_repl, matched_url_bracket, flags=re.IGNORECASE)

css = ''
with open(in_file) as f:
    for line in f:
        css = css + line

print(re.sub(url_bracket_pattern, url_bracket_repl, css, flags=re.IGNORECASE))