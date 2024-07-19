import os
import sys
import m3u8
import time
import requests
import traceback
import threadpool
from urllib.parse import urlparse
from Cryptodome.Cipher import AES

# 全局配置和变量
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36"
}

m3u8TryCountConf = 10
processCountConf = 50

# 全局变量
taskThreadPool = None
m3u8Url = None
rootUrlPath = None
title = None
sumCount = 0
doneCount = 0
cachePath = None
logPath = None
logFile = None
downloadedBytes = 0
downloadSpeed = 0
saveRootDirPath = None

def getM3u8Info():
    global m3u8Url
    global logFile
    global rootUrlPath
    tryCount = m3u8TryCountConf
    while True:
        if tryCount < 0:
            print("\t{0}下载失败！".format(m3u8Url))
            logFile.write("\t{0}下载失败！".format(m3u8Url))
            return None
        tryCount = tryCount - 1
        try:
            response = requests.get(m3u8Url, headers=headers, timeout=20)
            if response.status_code == 301:
                nowM3u8Url = response.headers["location"]
                print("\t{0}重定向至{1}！".format(m3u8Url, nowM3u8Url))
                logFile.write("\t{0}重定向至{1}！\n".format(m3u8Url, nowM3u8Url))
                m3u8Url = nowM3u8Url
                rootUrlPath = m3u8Url[0:m3u8Url.rindex('/')]
                continue

            contentLength = response.headers.get('Content-Length')
            if contentLength:
                expected_length = int(contentLength)
                actual_length = len(response.content)
                if expected_length > actual_length:
                    raise Exception("m3u8下载不完整")

            print("\t{0}下载成功！".format(m3u8Url))
            logFile.write("\t{0}下载成功！".format(m3u8Url))
            rootUrlPath = m3u8Url[0:m3u8Url.rindex('/')]
            break
        except:
            print("\t{0}下载失败！正在重试".format(m3u8Url))
            logFile.write("\t{0}下载失败！正在重试".format(m3u8Url))
    m3u8Info = m3u8.loads(response.text)
    if m3u8Info.is_variant:
        print("\t{0}为多级码流！".format(m3u8Url))
        logFile.write("\t{0}为多级码流！".format(m3u8Url))
        for rowData in response.text.split('\n'):
            if rowData.endswith(".m3u8"):
                scheme = urlparse(m3u8Url).scheme
                netloc = urlparse(m3u8Url).netloc
                m3u8Url = scheme + "://" + netloc + rowData
                rootUrlPath = m3u8Url[0:m3u8Url.rindex('/')]
                return getM3u8Info()
        print("\t{0}响应未寻找到m3u8！".format(response.text))
        logFile.write("\t{0}响应未寻找到m3u8！".format(response.text))
        return None
    else:
        return m3u8Info

def getKey(keyUrl):
    global logFile
    tryCount = m3u8TryCountConf
    while True:
        if tryCount < 0:
            print("\t{0}下载失败！".format(keyUrl))
            logFile.write("\t{0}下载失败！".format(keyUrl))
            return None
        tryCount = tryCount - 1
        try:
            response = requests.get(keyUrl, headers=headers, timeout=20, allow_redirects=True)
            if response.status_code == 301:
                nowKeyUrl = response.headers["location"]
                print("\t{0}重定向至{1}！".format(keyUrl, nowKeyUrl))
                logFile.write("\t{0}重定向至{1}！\n".format(keyUrl, nowKeyUrl))
                keyUrl = nowKeyUrl
                continue
            expected_length = int(response.headers.get('Content-Length'))
            actual_length = len(response.content)
            if expected_length > actual_length:
                raise Exception("key下载不完整")
            print("\t{0}下载成功！key = {1}".format(keyUrl, response.content.decode("utf-8")))
            logFile.write("\t{0}下载成功！ key = {1}".format(keyUrl, response.content.decode("utf-8")))
            break
        except :
            print("\t{0}下载失败！".format(keyUrl))
            logFile.write("\t{0}下载失败！".format(keyUrl))
    return response.text

def mutliDownloadTs(playlist):
    global logFile
    global sumCount
    global doneCount
    global taskThreadPool
    global downloadedBytes
    global downloadSpeed
    taskList = []
    for index in range(len(playlist)):
        dict = {"playlist": playlist, "index": index}
        taskList.append((None, dict))
    doneCount = 0
    sumCount = len(taskList)
    printProcessBar(sumCount, doneCount, 50)
    requests = threadpool.makeRequests(downloadTs, taskList)
    [taskThreadPool.putRequest(req) for req in requests]
    while doneCount < sumCount:
        beforeDownloadedBytes = downloadedBytes
        time.sleep(1)
        downloadSpeed = downloadedBytes - beforeDownloadedBytes
        printProcessBar(sumCount, doneCount, 50, True)
    print("")
    return True

def downloadTs(playlist, index):
    global logFile
    global sumCount
    global doneCount
    global cachePath
    global rootUrlPath
    global downloadedBytes
    succeed = False
    while not succeed:
        outputPath = cachePath + "/" + "{0:0>8}.ts".format(index)
        outputFp = open(outputPath, "wb+")
        if playlist[index].startswith("http"):
            tsUrl = playlist[index]
        else:
            tsUrl = rootUrlPath + "/" + playlist[index]
        try:
            response = requests.get(tsUrl, timeout=5, headers=headers, stream=True)
            if response.status_code == 200:
                expected_length = int(response.headers.get('Content-Length'))
                actual_length = len(response.content)
                downloadedBytes += actual_length
                if expected_length > actual_length:
                    raise Exception("分片下载不完整")
                outputFp.write(response.content)
                doneCount += 1
                printProcessBar(sumCount, doneCount, 50, isPrintDownloadSpeed=True)
                logFile.write("\t分片{0:0>8} url = {1} 下载成功！".format(index, tsUrl))
                succeed = True
        except Exception as exception:
            logFile.write("\t分片{0:0>8} url = {1} 下载失败！正在重试...msg = {2}".format(index, tsUrl, exception))
        outputFp.close()

def mergeTs(tsFileDir, outputFilePath, cryptor, count):
    global logFile
    outputFp = open(outputFilePath, "wb+")
    for index in range(count):
        printProcessBar(count, index + 1, 50)
        logFile.write("\t{0}\n".format(index))
        inputFilePath = tsFileDir + "/" + "{0:0>8}.ts".format(index)
        if not os.path.exists(outputFilePath):
            print("\n分片{0:0>8}.ts, 不存在，已跳过！".format(index))
            logFile.write("分片{0:0>8}.ts, 不存在，已跳过！\n".format(index))
            continue
        inputFp = open(inputFilePath, "rb")
        fileData = inputFp.read()
        try:
            if cryptor is None:
                outputFp.write(fileData)
            else:
                outputFp.write(cryptor.decrypt(fileData))
        except Exception as exception:
            inputFp.close()
            outputFp.close()
            print(exception)
            return False
        inputFp.close()
    print("")
    outputFp.close()
    return True

def removeTsDir(tsFileDir):
    for root, dirs, files in os.walk(tsFileDir, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(tsFileDir)
    return True

def ffmpegConvertToMp4(inputFilePath, ouputFilePath):
    global logFile
    if not os.path.exists(inputFilePath):
        print(inputFilePath + " 路径不存在！")
        logFile.write(inputFilePath + " 路径不存在！\n")
        return False
    cmd = r'.\lib\ffmpeg -i "{0}" -vcodec copy -acodec copy "{1}"'.format(inputFilePath, ouputFilePath)
    if sys.platform == "darwin":
        cmd = r'./lib/ffmpeg -i "{0}" -vcodec copy -acodec copy "{1}"'.format(inputFilePath, ouputFilePath)
    if os.system(cmd) == 0:
        print(inputFilePath + "转换成功！")
        logFile.write(inputFilePath + "转换成功！\n")
        return True
    else:
        print(inputFilePath + "转换失败！")
        logFile.write(inputFilePath + "转换失败！\n")
        return False

def printProcessBar(sumCount, doneCount, width, isPrintDownloadSpeed=False):
    global downloadSpeed
    precent = doneCount / sumCount
    useCount = int(precent * width)
    spaceCount = int(width - useCount)
    precent = precent*100
    if isPrintDownloadSpeed:
        if downloadSpeed > 1048576:
            print('\r\t{0}/{1} {2}{3} {4:.2f}% {5:>7.2f}MiB/s'.format(sumCount, doneCount, useCount * '■', spaceCount * '□', precent, downloadSpeed / 1048576),
                  file=sys.stdout, flush=True, end='')
        elif downloadSpeed > 1024:
            print('\r\t{0}/{1} {2}{3} {4:.2f}% {5:>7.2f}KiB/s'.format(sumCount, doneCount, useCount * '■', spaceCount * '□', precent, downloadSpeed / 1024),
                  file=sys.stdout, flush=True, end='')
        else:
            print('\r\t{0}/{1} {2}{3} {4:.2f}% {5:>7.2f}B/s  '.format(sumCount, doneCount, useCount * '■', spaceCount * '□', precent, downloadSpeed),
                  file=sys.stdout, flush=True, end='')
    else:
        print('\r\t{0}/{1} {2}{3} {4:.2f}%'.format(sumCount, doneCount, useCount*'■', spaceCount*'□', precent), file=sys.stdout, flush=True, end='')

def m3u8VideoDownloader():
    global title
    global logFile
    global m3u8Url
    global cachePath
    global downloadedBytes
    global downloadSpeed
    global saveRootDirPath
    print("\t1、开始下载m3u8...")
    logFile.write("\t1、开始下载m3u8...\n")
    m3u8Info = getM3u8Info()
    if m3u8Info is None:
        return False
    tsList = [playlist.uri for playlist in m3u8Info.segments]
    keyText = ""
    cryptor = None
    if (len(m3u8Info.keys) != 0) and (m3u8Info.keys[0] is not None):
        key = m3u8Info.keys[0]
        if key.method != "AES-128":
            print("\t{0}不支持的解密方式！".format(key.method))
            logFile.write("\t{0}不支持的解密方式！\n".format(key.method))
            return False
        keyUrl = key.uri
        if not keyUrl.startswith("http"):
            keyUrl = m3u8Url.replace("index.m3u8", keyUrl)
        print("\t2、开始下载key...")
        logFile.write("\t2、开始下载key...\n")
        keyText = getKey(keyUrl)
        if keyText is None:
            return False
        if key.iv is not None:
            cryptor = AES.new(bytes(keyText, encoding='utf8'), AES.MODE_CBC, bytes(key.iv, encoding='utf8'))
        else:
            cryptor = AES.new(bytes(keyText, encoding='utf8'), AES.MODE_CBC, bytes(keyText, encoding='utf8'))
    print("\t3、开始下载ts...")
    logFile.write("\t3、开始下载ts...\n")
    downloadSpeed = 0
    downloadedBytes = 0
    if mutliDownloadTs(tsList):
        logFile.write("\tts下载完成---------------------\n")
    print("\t4、开始合并ts...")
    logFile.write("\t4、开始合并ts...\n")
    if mergeTs(cachePath, cachePath + "/cache.flv", cryptor, len(tsList)):
        logFile.write("\tts合并完成---------------------\n")
    else:
        print(keyText)
        print("\tts合并失败！")
        logFile.write("\tts合并失败！\n")
        return False
    print("\t5、开始mp4转换...")
    logFile.write("\t5、开始mp4转换...\n")
    if not ffmpegConvertToMp4(cachePath + "/cache.flv", saveRootDirPath + "/" + title + ".mp4"):
        return False
    return True

def m3u8VideoDownloaderFromList(m3u8_list,
                                saveRootDirPathParam="./output",
                                errorM3u8InfoDirPath="./output/error.txt",
                                m3u8TryCountConf=10,
                                processCountConf=50):
    global title
    global logFile
    global m3u8Url
    global cachePath
    global downloadedBytes
    global downloadSpeed
    global saveRootDirPath
    saveRootDirPath = saveRootDirPathParam

    global taskThreadPool
    global rootUrlPath

    taskThreadPool = threadpool.ThreadPool(processCountConf)

    cachePath = saveRootDirPath + "/cache"
    logPath = cachePath + "/log.log"

    if not os.path.exists(saveRootDirPath):
        os.mkdir(saveRootDirPath)
    if not os.path.exists(errorM3u8InfoDirPath):
        open(errorM3u8InfoDirPath, 'w+')
    if not os.path.exists(cachePath):
        os.makedirs(cachePath)
    logFile = open(logPath, "w+", encoding="utf-8")
    errorM3u8InfoFp = open(errorM3u8InfoDirPath, "a+", encoding="utf-8")

    for m3u8Info in m3u8_list:
        title = m3u8Info[0]
        m3u8Url = m3u8Info[1]

        title = title.replace('\\', ' ', sys.maxsize)
        title = title.replace('/', ' ', sys.maxsize)
        title = title.replace(':', ' ', sys.maxsize)
        title = title.replace('*', ' ', sys.maxsize)
        title = title.replace('?', ' ', sys.maxsize)
        title = title.replace('"', ' ', sys.maxsize)
        title = title.replace('<', ' ', sys.maxsize)
        title = title.replace('>', ' ', sys.maxsize)
        title = title.replace('|', ' ', sys.maxsize)

        try:
            print("{0} 开始下载:".format(m3u8Info[0]))
            logFile.write("{0} 开始下载:\n".format(m3u8Info[0]))
            if m3u8VideoDownloader():
                logFile.seek(0)
                logFile.truncate()
                print("{0} 下载成功！".format(m3u8Info[0]))
            else:
                errorM3u8InfoFp.write(title + "," + m3u8Url + '\n')
                errorM3u8InfoFp.flush()
                print("{0} 下载失败！".format(m3u8Info[0]))
                logFile.write("{0} 下载失败！\n".format(m3u8Info[0]))
        except Exception as exception:
            print(exception)
            traceback.print_exc()

    logFile.close()
    errorM3u8InfoFp.close()
    print("----------------下载结束------------------")

# 新增：从命令行获取输入进行单个下载
def m3u8VideoDownloaderFromArgs(title, m3u8Url):
    global saveRootDirPath
    saveRootDirPath = "./output"
    global cachePath
    global logPath
    global logFile
    global taskThreadPool
    global rootUrlPath
    global m3u8TryCountConf
    global processCountConf

    taskThreadPool = threadpool.ThreadPool(processCountConf)
    cachePath = saveRootDirPath + "/cache"
    logPath = cachePath + "/log.log"

    if not os.path.exists(saveRootDirPath):
        os.mkdir(saveRootDirPath)
    if not os.path.exists(cachePath):
        os.makedirs(cachePath)
    logFile = open(logPath, "w+", encoding="utf-8")

    title = title.replace('\\', ' ', sys.maxsize)
    title = title.replace('/', ' ', sys.maxsize)
    title = title.replace(':', ' ', sys.maxsize)
    title = title.replace('*', ' ', sys.maxsize)
    title = title.replace('?', ' ', sys.maxsize)
    title = title.replace('"', ' ', sys.maxsize)
    title = title.replace('<', ' ', sys.maxsize)
    title = title.replace('>', ' ', sys.maxsize)
    title = title.replace('|', ' ', sys.maxsize)

    try:
        print("{0} 开始下载:".format(title))
        logFile.write("{0} 开始下载:\n".format(title))
        if m3u8VideoDownloader():
            logFile.seek(0)
            logFile.truncate()
            print("{0} 下载成功！".format(title))
        else:
            print("{0} 下载失败！".format(title))
            logFile.write("{0} 下载失败！\n".format(title))
    except Exception as exception:
        print(exception)
        traceback.print_exc()
    logFile.close()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        video_title = sys.argv[1]
        video_url = sys.argv[2]
        m3u8VideoDownloaderFromArgs(video_title, video_url)
    else:
        print("用法: python m3u8_download.py <视频标题> <m3u8链接>")
