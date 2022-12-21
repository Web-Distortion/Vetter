# Vetter: Visual-Aware Testing and Debugging for Web Performance Optimization

![license](https://img.shields.io/badge/License-MIT-blue "MIT") ![license](https://img.shields.io/badge/System-Vetter-green "System") ![license](https://img.shields.io/badge/Version-Beta-yellow "Version")

## 0. Table of Contents

[1. Overview](#1-overview)

[2. Prerequisites](#2-prerequisites)

[3. Usage](#3-usage)

[4. Defects Found using Vetter](#4-defects-found-using-vetter)

[5. Data Release](#5-data-release)



## 1. Overview

<div align="center">
    <img src="https://raw.githubusercontent.com/web-distortion/Vetter/main/.github/images/system_overview.png">
</div>

This is the artifact README for the paper #3353 "Visual-Aware Testing and Debugging for Web Performance Optimization". In this paper, we present Vetter, a novel and effective system for automatically testing and debugging visual distortions from the perspective of how modern web pages are generated.

The above figure shows the architecture overview of Vetter, which contains three major components: **WPO Runtime Logger**, **Distortion Detector**, and **WPO Debugger**. WPO Runtime Logger records the WPO’s function call stacks and runtime logs. This component is built upon [gdb](https://www.sourceware.org/gdb/), [Go Execution Tracer](https://blog.gopheracademy.com/advent-2017/go-execution-tracer/), and [OpenTelemetry](https://opentelemetry.io/). Distortion Detector records the page’s resources and their loading sequence using Mahimahi. It also records the SkPaint API invocations with the Skia `web_to_skp` tool during page loading to construct and compare the morphological segment trees (MSTs) of two web pages. Finally, WPO Debugger uses the puppeteer library to monitor and manipulate the page loading process for debugging visual distortions. The source code together with the detailed documentation of the three components are placed in three folders: `WPO_runtime_logger/`, `Distortion_detector/`, and `WPO_debugger/` correspondingly.



## 2. Prerequisites

To use Vetter for testing and debugging WPO-incurred visual distortions, we highly recommend that you line up with the following hardware/software environments to avoid unexpected bugs.

- **Hardware Setups.** You should at least prepare two servers and one client for using Vetter: one server (dubbed as S1 for short) acts as the web page server that holds the web contents; the other server (S2) is the WPO server that runs a specific WPO. The client should have access to the two servers.

- **Software Environments.** 

  S1 is a typical web page server, which should have the following pre-requisites for use.
  
+ Ubuntu 16.04 (*recommended*)
  + Nginx 1.10 or latter

  S2 is a WPO server, where we should also deploy the WPO runtime logger. To run the four WPOs and their corresponding runtime loggers on S2, the following environment should be satisfied.
  
  + Ubuntu 16.04 (*recommended*)
  + Python 3.7
  + Java 1.8 or latter
  + Go 1.19.1 or latter
+ Node.js 17.0
  + OpenSSL 1.0 or latter

  For the client, the recommended environments are listed below.
  
  + Ubuntu 16.04 (*recommended*)
  
  + Google Chrome v95
  
  + Mahimahi 0.98
  
    
## 3. Usage

### 3.1 WPO Runtime Logger

WPO runtime logger sits side by side with the WPO server (*i.e.,* S2). The WPO runtime logger should fit the specific implementation of the WPO. For example, Compy is implemented in Go language, and thus the WPO runtime logger can be directly built based on the Go Execution Tracer (an off-the-shelf tracer in Go that tracks the OS execution events such as goroutine creation/blocking/unblocking and syscall enter, exit, block). For other WPOs including Ziproxy, Fawkes, and SipLoader, we take similar approach by taking advantage of existing tools including gdb and OpenTelemetry for building the WPO runtime logger. The detailed instructions are coming soon.

Below we take building the WPO runtime logger for Compy as a typical example.

+ Download and install Compy.

  ```shell
  apt-get install -y libjpeg8-dev openssl ssl-cert #install the dependencies of Compy
  go get github.com/barnacs/compy
  cd go/src/github.com/barnacs/compy/
  go install
  ```

  To use Compy over HTTPS, generate a certificate for your host using OpenSSL.

  ```shell
  openssl req -x509 -newkey rsa:2048 -nodes -keyout cert.key -out cert.crt -days 3650 -subj '/CN=<your-domain>'
  ```

  Start Compy as the web optimization proxy.

  ```shell
  cd go/src/github.com/barnacs/compy/
  compy -cert cert.crt -key cert.key -ca ca.crt -cakey ca.key
  ```

+ Install the `pprof`, the core module of Go Execution Tracer by executing the following command.

  ```shell
  go install github.com/google/pprof@latest
  ```

  The binary will be installed in `$GOPATH/bin` (`$HOME/go/bin` by default).

+ **(Optional)** Install the `graphviz` to generate graphic visualizations of  the results output by`pprof`.

  ```shell
  brew install graphviz || apt-get install graphviz
  ```

+ Start `pprof` to monitor the function call stacks and runtime logs of Compy.

  ```shell
  cd go/src/github.com/barnacs/compy/
  go test -bench=. -cpuprofile=cpu.prof
  go tool pprof -http=:9980 cpu.prof
  ```

+ Visit a web page and the WPO call stacks together with the runtime logs can be found at `http://localhost:9980/ui/`. The function call stacks and runtime logs of WPO are demonstrated as the figure below.

  <div align="center">
      <img src="https://raw.githubusercontent.com/web-distortion/Vetter/main/.github/images/pprof_demo.png">
  </div>

### 3.2 Distortion Detector

Distortion detector mainly contains two parts. First, it records and replays web pages for testing visual distortions. This part of logics resides on the web page server (*i.e.,* S1). Beisdes, the distortion detector also collects the SKPaint logs of the original and optimized web pages, constructs morphological segment trees (MSTs), and calculates the morphological similarity between the two pages. This part of mechanisms works on the client side.

#### 3.2.1 Recording and Replaying Web Pages using Mahimahi

Use the `mm-webrecord` tool of Mahimahi to record the loading process of a certain web page that needs optimization. For example, we can record http://www.example.com by:

~~~shell
# Record http://www.example.com
OUTPUT_DIR=output
WEB_PAGE_URL=http://www.example.com
mm-webrecord ${OUTPUT_DIR} /usr/bin/google-chrome --disable-fre --no-default-browser-check --no-first-run --window-size=1920,1080 --ignore-certificate-errors --user-data-dir=./nonexistent/$(date +%s%N) ${WEB_PAGE_URL}
~~~

The above shell script will launch a Chrome browser instance, automatically navigate to the targe web page, and record the loading process of the original web page. The captured resources are saved in the `OUTPUT_DIR` directory for replay.

Then, we replay the web page so that the WPO can perform optimization before/during the page loading:

~~~shell
# Replay the recorded https://example.com
mm-webreplay ${OUTPUT_DIR}
/usr/bin/google-chrome --disable-fre --no-default-browser-check --no-first-run --window-size=1920,1080 --ignore-certificate-errors --user-data-dir=./nonexistent/$(date +%s%N) ${WEB_PAGE_URL}
~~~

#### 3.2.2 Collecting SKPaint Logs

Before using Skia, make sure that you have successfully installed chrome on the client.

+ Download the latest version of Skia.

  ```shell
  git clone https://skia.googlesource.com/skia.git
  ```

+ Use `web_to_skp` tool to capture the SKPaint logs of a certain web page. The output logs are placed in the folder `./skia/skia_data/`.

  ```shell
  cd ./skia/skia/skia/experimental/tools/
  #collecting the skpaint logs of www.example.com
  ./web_to_skp "/usr/bin/google-chrome" http://www.example.com/ "./skia/skia_data/example.skp"
  ```

+ Convert the SKPaint logs to JSON file for further processing.

  ```shell
  cd ./skia/skia/skia/out/Debug
   ./skp_parser ./skia/skia_data/example.skp >> ./skia/skia_data/example.json
  ```

#### 3.2.3 Constructing and Comparing MSTs of Web Pages

+ Put the collected SKPaint logs of both the original and the optimized web pages in the folder `Distortion_detector/raw_data/`. Then, build the MSTs of the two web pages by running the following command. Note that the two MSTs are output in the same file `MST_output.txt`.

  ```shell
  cd Distortion_detector
  python3 MST_construction.py original_skpaint.data optimized_skpiant.data MST_output.txt
  ```

+ Conduct hierarchy matching and node matching between the two MSTs.

  ```shell
  python3 MST_comparison.py ./raw_data/ result.txt
  ```

+ Calculate the similarity between two MSTs and generate the morphological hints.

  ```shell
  g++ MorphSIM_cal.cpp -o run
  ./run result.txt
  ```



### 3.3 WPO Debugger

WPO Debugger mainly works at the client side. It also cooperates with the distortion detector (works on the web page server S1 and the client) to repeatedly modify and replay the web pages for debugging the visual distortions. Specifically, WPO debugger gradually restores the modified resources/loading sequences to the original ones to see whether the distortion is resolved. If so, the “real culprits” of the distortion are among the most recently restored resources/sequences.

This part details the basic workflow of WPO debugger of Vetter. We use SipLoader coupled with Amazon's landing page as an typical example to illustrate how we can gradually restore the resource loading sequences.

* **Dependencies**

  ```shell
  pip3 install beautifulsoup4
  npm install -g delay puppeteer # May need root privilege, or you can install them locally without the "-g" flag
  ```

#### 3.3.1 Corpus Web Pages

SipLoader directly modifies the recorded web pages offline to perform optimizations. As a result, Vetter debugs SipLoader based on the modified pages in an offline manner as well. Of course, Vetter's morphological causal inference is generalizable to other WPOs that operate on the resources during actual page loading. This depends on how the WPO performs optimization routines.

We take the landing page of [amazon.com](https://www.amazon.com/) as an example. To record amazon.com, simply run the shell script *collect.sh*, which will automatically record the loading process of amazon.com using Mahimahi:

  ```shell
  bash collect.sh
  ```

When the page has been fully loaded, you will see a directory named *amazon.com* with all the resource files recorded in it during page loading.

#### 3.3.2 Manipulating Loading Sequence

+ **Performing Optimization Routines on the Page.** To apply the optimizations of SipLoader on recorded web pages, you need to first `cd` to the *SipLoader_mod* directory, where we provide a modified version of SipLoader that enables you to change the loading sequences after the page is optimized. Then, just run the following commands to install SipLoader to the recorded page:

  ```shell
    # Extracting the resources in HTML files
    python3 prepare_html.py
    # Injecting SipLoader's resource load scheduling logic
    python3 install_siploader.py
  ```

  If everything works fine, you will see a new directory named *amazon.com_reordered*. This directory contains the optimized version of the page.

+ **Changing Loading Orders for the Resources.** The installation process of SipLoader outputs four additional directories, namely `chunked_html`, `inline_js`, and `url_ids`. Specially pay attention to the `url_ids` where you can change the loading sequences for the optimized pages.

  For each optimized web page, there are two corresponding json files in the `url_ids` directory. Take amazon.com as an example, file `amazon.com_tag_id.json` specifies the resources\' parent elements in the DOM tree , while `amazon.com_res_id.json` specifies all the resource URLs and their IDs. In particular, this ID is also the loading order of the resource during the page load scheduling of SipLoader. A smaller ID indicates the corresponding resource will be loaded first. You can manually change the resource loading order to restore the original loading sequence:

  ```json
  // amazon.com_res_id.json
  {
      "https://www.amazon.com/": {
          // ... 
          "https://m.media-amazon.com/images/W/WEBP_402378-T2/images/I/61cYZXdazOL._SX1500_.jpg": 8,
          "https://images-na.ssl-images-amazon.com/images/W/WEBP_402378-T2/images/G/01/AmazonExports/Fuji/2020/May/Dashboard/Fuji_Dash_Returns_1x._SY304_CB432774714_.jpg": 9999, // Set this resource to be loaded at the last
          "https://images-na.ssl-images-amazon.com/images/W/WEBP_402378-T2/images/G/01/AmazonExports/Fuji/2022/February/DashboardCards/GW_CONS_AUS_HPC_HPCEssentials_CatCard_Desktop1x._SY304_CB627424361_.jpg": 10,
          // ...
          "https://images-na.ssl-images-amazon.com/images/W/WEBP_402378-T2/images/G/01/AmazonExports/Fuji/2021/June/Fuji_Quad_Keyboard_1x._SY116_CB667159063_.jpg": 20,
          "https://images-na.ssl-images-amazon.com/images/W/WEBP_402378-T2/images/G/01/AmazonExports/Fuji/2021/June/Fuji_Quad_Mouse_1x._SY116_CB667159063_.jpg": -1, // Set this resource to be loaded first
          "https://images-na.ssl-images-amazon.com/images/W/WEBP_402378-T2/images/G/01/AmazonExports/Fuji/2021/June/Fuji_Quad_Chair_1x._SY116_CB667159060_.jpg": 22,
          // ...
      }
  }
  ```

  Note that the above process only changes the network fetching order of the resources. To further change the actual execution order of JavaScript files, you need to modify the json file in `inline_js` directory so that the execution dependency between JavaScript code pieces can be changed. Specifically, you need to changed the `prev_js_id` field for each JavaScript code segment, which specifies the precedent code needed to be executed before the given code pieces. 

  ```json
  // inline_js/amazon.com.json
  {
      "https://www.amazon.com/": {
          "0": {
              "code": "var aPageStart = (new Date()).getTime();",
              "prev_js_id": -1
          },
          "1": {
              "code": "var ue_t0=ue_t0||+new Date();",
              "prev_js_id": 0
          },
          "5": {
              "code": "\nwindow.ue_ihb ...",
              "prev_js_id": 1
          },
          "6": {
              // ...
          },
          // ...
      }
  }
  ```

  After you have changed the resource loading order in `amazon.com_res_id.json` (and the related JavaScript execution order if needed), you should delete the old `amazon.com_reordered` and run `python3 install_siploader.py` again to generate the new optimized page with restored loading sequence.

#### 3.3.3 Replay & Analysis

We also use Mahimahi to replay the modified web page. In this way, developers can analyze the causal relation between the visual distortion and the restored resource loading sequence for SipLoader. To replay the page, try:

  ```shell
  mm-webreplay amazon.com_reordered/
  node replay.js amazon.com https://www.amazon.com
  ```

And the script will output the CSS selectors and the geometry properties of all web page elements in `element_pos.json` for developers' further investigation.

#### 3.3.4 Debugging Other Web Pages

Apart from the example amazon.com, you can debug SipLoader with other web pages by yourself. To this end, you should first record the web page by:

  ```shell
  DOMAIN_NAME='DOMAIN NAME OF THE PAGE'
  URL='URL OF THE PAGE'
  mm-webrecord ${DOMAIN_NAME} /usr/bin/google-chrome --disable-fre --no-default-browser-check --no-first-run --window-size=1920,1080 --ignore-certificate-errors --user-data-dir=./nonexistent/$(date +%s%N) ${URL}
  ```

Then, you need to modify *prepare_html.py* and *install_siploader.py* to replace the line `sites = [{'domain': 'amazon.com', 'url': 'https://www.amazon.com/'}]` with `sites = [{'domain': DOMAIN_NAME, 'url': URL}]`.

Afterwards, manipulate the web page again following the [above steps](https://github.com/Web-Distortion/Vetter#232-manipulating-loading-sequence) and replay the page by:

  ```shell
  mm-webreplay ${DOMAIN_NAME}_reordered/
  node replay.js ${DOMAIN_NAME} ${URL}
  ```



## 4. Defects Found using Vetter
Below, we list all the defects we have found for four representative WPOs: Compy, Ziproxy, Fawkes, and Siploader. Note that for Ziproxy, we mail the developers of Ziproxy with the defects we have found (together with our suggested fixes) through their official channels, but have not received the reply yet.

### Compy

| Index | Description                                                  | Issue/PR NO.                                                 | Current State     |
| ----- | ------------------------------------------------------------ | ------------------------------------------------------------ | ----------------- |
| 1     | Compy goes wrong when compressing some JPG/PNG images, which makes the images unable to load. | <a href="https://github.com/barnacs/compy/issues/63">Issue-63</a> & <a href="https://github.com/barnacs/compy/pull/70">PR-70</a> | Confirmed & Fixed |
| 2     | Compy fails to parse the compressed images.                  | <a href="https://github.com/barnacs/compy/issues/64">Issue-64</a> | Reported          |
| 3     | Compy can't deal with the websocket, which fails some interaction tasks like chatrooms and online services. | <a href="https://github.com/barnacs/compy/issues/65">Issue-65</a> | Reported          |
| 4     | Compy may block the redirecting process of some websites.    | <a href="https://github.com/barnacs/compy/issues/66">Issue-66</a> & <a href="https://github.com/barnacs/compy/pull/68">PR-68</a> | Confirmed & Fixed |
| 5     | Compy can't support GIF images.                              | <a href="https://github.com/barnacs/compy/pull/70">PR-70</a> | Confirmed & Fixed |

### Ziproxy


| Index | Description                                                  | Issue/PR NO. | Current State     |
| ----- | ------------------------------------------------------------ | ------------ | ----------------- |
| 1     | Ziproxy goes wrong when compressing some contexts, which makes the original contexts become messy code. | -            | Waiting For Reply |
| 2     | Ziproxy disturbs the loading sequence of JS files, leading to loading failure of  web pages. | -            | Waiting For Reply |
| 3     | Ziproxy cannot handle GIF files, leading to image display error transcoding. | -            | Waiting For Reply |
| 4     | Ziproxy causes conflicting fields in response header.        | -            | Waiting For Reply |

### Fawkes


| Index | Description                                                  | Issue/PR NO.                                                 | Current State |
| ----- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------- |
| 1     | Fawkes can't handle some elements whose innerText has multiple lines. | <a href="https://github.com/fawkes-nsdi20/fawkes/issues/14">Issue-14</a> | Reported      |
| 2     | Fawkes mistakenly selects elements in template HTML          | <a href="https://github.com/fawkes-nsdi20/fawkes/issues/13">Issue-13</a> | Reported      |

### SipLoader


| Index | Description                                                  | Issue/PR NO.                                                 | Current State     |
| ----- | ------------------------------------------------------------ | ------------------------------------------------------------ | ----------------- |
| 1     | SipLoader cannot track dependencies triggered by CSS files.  | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/1">Issue-1</a> | Confirmed         |
| 2     | SipLoader cannot handle dependency loops among resources.    | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/2">Issue-2</a> | Confirmed         |
| 3     | SipLoader cannot request cross-origin resources.             | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/3">Issue-3</a> | Confirmed         |
| 4     | Disordered page loading of websites with multiple HTML files. | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/4">Issue-4</a> | Confirmed         |
| 5     | "404 Not Found" error when loading websites with multiple HTML files. | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/5">Issue-5</a> | Confirmed         |
| 6     | SipLoader cannot handle some dynamic resources.              | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/6">Issue-6</a> | Confirmed         |
| 7     | A problem related to Chromium CDP used by SipLoader.         | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/7">Issue-7</a> | Confirmed         |
| 8     | CSS abormality of some websites.                             | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/8">Issue-8</a> & <a href="https://github.com/SipLoader/SipLoader.github.io/pull/9">PR-9</a> | Confirmed & Fixed |
| 9     | SipLoader fails to rewrite web page objects compressed by brotli. | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/10">Issue-10</a> & <a href="https://github.com/SipLoader/SipLoader.github.io/pull/12">PR-12</a> | Confirmed & Fixed |
| 10    | SipLoader cannot distinguish between data URIs and real URLs in CSS files. | <a href="https://github.com/SipLoader/SipLoader.github.io/issues/11">Issue-11</a> & <a href="https://github.com/SipLoader/SipLoader.github.io/pull/9">PR-9</a> | Confirmed & Fixed |



## 5. Data Release

We collected the web page snapshots as well as invocation logs of SKPaint APIs when visiting Alexa top and bottom 2,500 websites on Dec. 9th, 2021, which are available in `snapshot.zip` and `skpdata.tar.gz` respectively in the <a href="https://drive.google.com/drive/folders/186QVPhd5jGKOkaKUp0HYpbm4CQelOJsw?usp=sharing">Google Drive</a>. Besides, we have made part of our dataset available in `results_of_user_study.zip` in <a href="https://drive.google.com/drive/folders/186QVPhd5jGKOkaKUp0HYpbm4CQelOJsw?usp=sharing">Google Drive</a> (the remaining part will be publicly available when the paper is published).

