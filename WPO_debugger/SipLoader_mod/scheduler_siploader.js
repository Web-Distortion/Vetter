// window.siploaderGraph
// window.siploaderTagId
// window.siploaderResId
// window.siploaderChunkedHTML
// window.siploaderInlineJS
// window.siploaderPERF

const MAX_CONNECTION = 24;
const MESSAGE_POOL_INIT = 'MESSAGE_POOL_INIT';
const MESSAGE_RESPONSE_RECEIVED = 'MESSAGE_RESPONSE_RECEIVED';
const MESSAGE_OBJECT_EVALUATED = 'MESSAGE_OBJECT_EVALUATED';

var pendingPool = [];
var inflightPool = [];
var waitingForEvalPool = {};
var urlEvaled = new Set();

console.log('Initialize SipLoader successfully!');
console.log(HTMLName);

for ( var i = 0; i < siploaderChunkedHTML.length; i++ ) {
    if (siploaderChunkedHTML[i].indexOf("<\\/script>") != -1) {
        siploaderChunkedHTML[i] = "</sc" + "ript>";
    }
}

// inflate html

(() => {
    if ( document.body == null ) {
        var c = document.createElement("body");
        document.firstChild.appendChild(c);
    }

    var rawHTML = '';
    
    for (var i = 0; i < siploaderChunkedHTML.length; i++) {
        rawHTML += siploaderChunkedHTML[i] + '\n';
    }
    if (HTMLName != document.URL) {
        return;
    }
    document.body.innerHTML = rawHTML;
    // console.log(rawHTML);
    
    console.log('Finished inflating HTML');
})();

// init graph data

var nodeAncestors = {}
var nodeDescendants = {}
var ancestorGraphCosts = {};
var ancestorGraphGains = {};
var bestOrder = [];
var idToUrl = {};
var nodeRemoved = [];
var nodeNumber = 0;
var linkNumber = 0;

var maxAvgWeight = -1;
var maxAvgWeightNode = 0;


// console.log(siploaderResId)
// Create items array
var items = Object.keys(siploaderResId).map(function(key) {
    return [key, siploaderResId[key]];
  });
  
// Sort the array based on the second element
items.sort(function(first, second) {
    return first[1] - second[1];
});
for (let item of items) {
    bestOrder.push(item[0]);
}
// console.log(bestOrder);
for (var url of bestOrder) {
    idToUrl[siploaderTagId[url]] = url;
}

function initPools() {
    // Pending Pool
    for (let url in siploaderTagId) {
        var urlFormatted = new URL(url, window.location.href);
        var hostname = urlFormatted.hostname;
        pendingPool.push(url);
    }

    pendingPool = pendingPool.sort((a, b) => (bestOrder.indexOf(a) == -1 ? Number.MAX_VALUE : bestOrder.indexOf(a)) - (bestOrder.indexOf(b) == -1 ? Number.MAX_VALUE : bestOrder.indexOf(b)));

    window.top.postMessage([MESSAGE_POOL_INIT, pendingPool], '*');

    // Eval pool

    for (var id in siploaderInlineJS) {
        waitingForEvalPool[id] = siploaderInlineJS[id];
        waitingForEvalPool[id].evaled = false;
    }
}

initPools();

function eventHandler(event) {
    // console.log(event);

    if (event.data[0] == MESSAGE_POOL_INIT) {
        handlePendingPool();
    } else if (event.data[0] == MESSAGE_RESPONSE_RECEIVED) {
        handlePendingPool();
        handleResponse(event.data[1]);
        handleEvalPool();
    } else if (event.data[0] == MESSAGE_OBJECT_EVALUATED) {
        if (event.data[1]) {
            handleEvalPool();
        }
    }
}

window.addEventListener('message', eventHandler, false);

function handleResponse(requested_url) {
    var url = new URL(requested_url, window.location.href);
    var hostname = url.hostname;

    var index = inflightPool.indexOf(requested_url);
    if (index >= 0) {
        inflightPool.splice(index, 1);
    }
    
}

function handlePendingPool() {
    while (inflightPool.length < MAX_CONNECTION && pendingPool.length > 0) {
        var url = pendingPool.shift();
        inflightPool.push(url);

        var request = new XMLHttpRequest();
        request.original_host = new URL(url, window.location.href).hostname;
        request.requested_url = url;

        if (url.indexOf('js') == -1) {
            request.responseType = "blob";
        }

        request.open('GET', url, true);

        request.send();
    }
}

function handleEvalPool() {
    // console.log(waitingForEvalPool);

    var evalMore = false;
    var bestScript = -1;
    var priority = Number.MAX_VALUE;
    for (var id in waitingForEvalPool) {
        if (!waitingForEvalPool[id].evaled && waitingForEvalPool[id].prev_js_id < 0 && waitingForEvalPool[id].code != 'NO_INLINE') {
            if (bestScript == -1) {
                bestScript = id;
                var new_priority = bestOrder.indexOf(idToUrl[id]);
                priority = new_priority < 0 ? Number.MAX_VALUE : new_priority;
            } else {
                var new_priority = bestOrder.indexOf(idToUrl[id]);
                if (new_priority >= 0 && new_priority < priority) {
                    bestScript = id;
                    priority = new_priority;
                }
            }
        } else if (!waitingForEvalPool[id].evaled && waitingForEvalPool[id].prev_js_id >= 0 && waitingForEvalPool[waitingForEvalPool[id].prev_js_id].evaled && waitingForEvalPool[id].code != 'NO_INLINE') {
            if (bestScript == -1) {
                bestScript = id;
                var new_priority = bestOrder.indexOf(idToUrl[id]);
                priority = new_priority < 0 ? Number.MAX_VALUE : new_priority;
            } else {
                var new_priority = bestOrder.indexOf(idToUrl[id]);
                if (new_priority >= 0 && new_priority < priority) {
                    bestScript = id;
                    priority = new_priority;
                }
            }
        }
    }
    if (bestScript != -1) {
        try {
            window.eval(waitingForEvalPool[bestScript].code);
        } catch (error) {
            // console.log(error)
        } finally {
            waitingForEvalPool[bestScript].evaled = true;
            evalMore = true;
        }
    }

    setTimeout(() => {
        window.top.postMessage([MESSAGE_OBJECT_EVALUATED, evalMore], '*');
    }, 5);
}

function onResponseReceived() {
    // console.log(this);

    if (siploaderTagId.hasOwnProperty(this.requested_url)) {
        var tagIds = siploaderTagId[this.requested_url];
        // console.log(tagIds);

        for (let id of tagIds) {
            // console.log(id);
            var element = document.querySelector(`[tag_id="${id}"]`);
            // console.log(element);

            if (element == null) {
                continue;
            }

            if (element.tagName.toLowerCase() == 'img') {
                var objUrl = window.URL.createObjectURL(this.response);
                // console.log(objUrl)
                element.setAttribute('src', objUrl);
                urlEvaled.add(this.requested_url);
            } else if (element.tagName.toLowerCase() == 'link') {
                var objUrl = window.URL.createObjectURL(this.response);
                // console.log(objUrl)
                element.setAttribute('href', objUrl);
                urlEvaled.add(this.requested_url);
            } else if (element.tagName.toLowerCase() == 'script') {
                waitingForEvalPool[id].code = this.responseText;
            } else {
                this.onload_native();
            }
        }        
    }
    window.top.postMessage([MESSAGE_RESPONSE_RECEIVED, this.requested_url], '*');
}

var _xhrsend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.send = function(){
    this.onload_native= this.onload;
    this.onload = onResponseReceived;

    if (this.requested_url) {
        console.log(this.requested_url);
    }

    _xhrsend.call(this)
};

document.currentScript.parentElement.removeChild(document.currentScript);

</script>
