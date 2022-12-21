const puppeteer = require('puppeteer');
const delay = require('delay');
const fs = require('fs');


var domain = parseInt(process.argv[2]);
var url = process.argv[3];

var viewport = { width: 1920, height: 1080 };

(async () => {
    var browser = await puppeteer.launch({executablePath: '/usr/bin/google-chrome', headless: false,
                                    args: ['--disable-fre', '--no-default-browser-check', '--no-first-run', '--ignore-certificate-errors', `--window-size=${viewport.width},${viewport.height}`, '--no-sandbox']});
    
    await delay(1000);

    var page = await browser.newPage();
    
    await page.setViewport(viewport);
    await page.goto(url);
    await delay(2000);

    var elementPos = await page.evaluate( () => {
        var elements = [];

        function traverse(node, parentSelector) {
            var nodeSelector = node.tagName + ((node.id) ? "#" + node.id : "");
            var selector = parentSelector + ' > ' + nodeSelector;
            try {
                var rect = node.getBoundingClientRect();
                var pos = {}
                pos['selector'] = selector;
                pos['rect'] = JSON.parse(JSON.stringify(rect));;
                elements.push(pos);
            } catch (error) {
                console.log(error);
            }
            
            for (let i = 0; i < node.children.length; i++) {
                traverse(node.children[i], selector);
            }
        }
        
        traverse(document.body, '');

        return elements;
    });
    fs.writeFileSync('element_pos.json', JSON.stringify(elementPos, null, 4), 'utf-8');

    await browser.close();

    process.exit(0);
})();

