let fs = require('fs');
const parseNodesFromHar = (nodes) => {
  let initTime = new Date(nodes[0].startedDateTime);
  let nodeList = [];
  for (let node of nodes) {
    let tmp = {};
    tmp.name = node.request.url.match(/.+\/(.*)$/)[1]; 
    tmp.endTime = (new Date(node.startedDateTime) - initTime) + node.time;
    tmp.size = node.response.content.size;
    tmp.realName = '';
    nodeList.push(tmp);
  }
  nodeList.sort((a, b) => a.endTime - b.endTime);
  return JSON.parse(JSON.stringify(nodeList));
}
const getFileInfoFromFolder = (folderUrl) => {
  let fileNameList = fs.readdirSync(folderUrl);
  let sizeMap = new Map();
  fileNameList.forEach(file => {
    let fileSize = fs.statSync(folderUrl + '/' + file).size
    if (!sizeMap.has(fileSize)) {
      sizeMap.set(fileSize, []);
    }
    sizeMap.get(fileSize).push(file);
  })
  return sizeMap;
}

const mappingHarToFile = (parsed, sizeMap) => {
  let parsed_map = new Map();
  for (let p of parsed) {
    let sizeList = sizeMap.get(p.size);
    if (sizeList === undefined) {
      p.realName = '';
    }
    else {
      p.realName = sizeList[0];
    }
    parsed_map.set(p.name, p);
  }
  return parsed_map;
}

/**
 * main
 */
let nodes_ori = JSON.parse(fs.readFileSync('src/example.com_ori.har')).log.entries;
let parsed_ori = parseNodesFromHar(nodes_ori);
let nodes_comp = JSON.parse(fs.readFileSync('src/example.com_comp.har')).log.entries;
let parsed_comp = parseNodesFromHar(nodes_comp);


let size_map_ori = getFileInfoFromFolder('src/example_ori_files');
let map_ori = mappingHarToFile(parsed_ori, size_map_ori); // Map
// fs.writeFileSync('ori.json', JSON.stringify(parsed_ori))
// console.log(map_ori)
// console.log(parsed_ori)
let size_map_comp = getFileInfoFromFolder('src/example_comp_files');
let map_comp = mappingHarToFile(parsed_comp, size_map_comp);
// fs.writeFileSync('comp.json', JSON.stringify(parsed_comp))
// console.log(parsed_comp);

let re = [];
parsed_ori.forEach(ori_node => {
  let comp_node = map_comp.get(ori_node.name);
  if (comp_node === undefined) {
    re.push({
      name: ori_node.name,
      realNameOri: ori_node.realName,
      realNameComp: '',
      sizeOri: ori_node.size,
      sizeComp: 0
    });
    return;
  }
  else if (ori_node.size === comp_node.size)
    return;
  else {
    re.push({
      name: ori_node.name,
      realNameOri: ori_node.realName,
      realNameComp: comp_node.name,
      sizeOri: ori_node.size,
      sizeComp: comp_node.size
    });
  }
})
console.log(re)

for (let r of re) {
  if (r.sizeComp == 0 && r.realNameOri != '') {
    console.log("original name: " + r.realNameOri);
    console.log("compressed name: " + r.realNameComp);
    break;
  }
}