
# m3u8_downloader

## 原作者
     https://github.com/hestyle/m3u8_downloader
---
## 项目简介
`m3u8_downloader` 是一个用于下载和合并 m3u8 视频流的 Python 脚本。该脚本支持多线程下载、AES-128 解密和视频格式转换，能够将 m3u8 视频流下载为 mp4 文件。

## 功能特性
- **下载 m3u8 视频流**：支持从 m3u8 链接下载视频流，适用于各种流媒体网站。
- **HTTP 重定向支持**：自动处理 HTTP 重定向，确保下载过程不中断。
- **多线程下载**：利用多线程技术，加速 ts 分片文件的下载速度。
- **AES-128 解密**：支持对加密的 m3u8 视频进行 AES-128 解密，确保视频文件可正常播放。
- **合并 ts 分片**：自动将下载的 ts 分片文件合并为一个完整的视频文件。
- **视频格式转换**：使用 ffmpeg 将合并后的 ts 文件转换为 mp4 格式，方便播放和存储。

## 安装
安装所需依赖项：
```bash
pip install m3u8 requests pycryptodome threadpool
```

## 使用说明

### 直接下载单个 m3u8 视频流
你可以通过命令行直接下载单个 m3u8 视频流：
```bash
python m3u8_down.py <视频标题> <m3u8链接>
```
例如：
```bash
python m3u8_down.py 广西xx https://resources.xxxxx.life/xxx.m3u8
```

### 从列表下载多个 m3u8 视频流

你也可以在代码中定义一个包含多个 m3u8 视频流链接的列表，并批量下载这些视频流。

#### 方法一：导入整个模块
根据 `demo.py` 示例，内容如下：
```python
import m3u8_down

if __name__ == '__main__':
    m3u8_list = [
        ["标题1", "https://xxx.m3u8"],
        ["标题2", "https://xxx.m3u8"]
    ]
    m3u8_down.m3u8VideoDownloaderFromList(m3u8_list)
```

然后运行这个脚本。


#### 方法二：导入函数
根据 `demo.py` 示例，内容如下：
```python
from m3u8_down import m3u8VideoDownloaderFromList

if __name__ == '__main__':
    m3u8_list = [
        ["标题1", "https://xxx.m3u8"],
        ["标题2", "https://xxx.m3u8"]
    ]
    m3u8VideoDownloaderFromList(m3u8_list)
```

然后运行这个脚本：
```bash
python demo.py
```

## 配置
在 `m3u8_down.py` 中，你可以配置以下全局变量：
- `m3u8TryCountConf`: 尝试下载 m3u8 文件的次数，默认为 10。
- `processCountConf`: 下载 ts 分片的线程数，默认为 50。
- `headers`: HTTP 请求头配置。

## 日志
下载过程中的日志信息会记录在 `log.log` 文件中，如果有下载失败的 m3u8 链接，会记录在 `error.txt` 文件中。

## 注意事项
- 在./lib下，有默认的ffmpeg压缩包，解压即可，如果不解压，程序会报错，如需要自行安装ffmpeg到电脑，则注意以下两点：
- 请确保系统中已安装 `ffmpeg`，并且其路径已添加到环境变量中。
- 该脚本默认使用 `ffmpeg` 进行视频格式转换，请将 `ffmpeg` 二进制文件放在 `./lib` 目录下。脚本会检查该目录下是否存在 `ffmpeg` 文件。

## 输出说明
- **输出目录**：下载和处理后的文件会输出到 `./output` 目录下。
  - **cache**：存放下载的 ts 分片文件。
  - **log.log**：记录下载过程中的日志信息。
  - **error.txt**：记录下载失败的 m3u8 链接信息。

## 贡献
欢迎提交 issue 和 pull request 来帮助改进该项目。

## 许可证
该项目使用 Apache License 许可证。

---
## 声明
### 以上源码仅作为Python技术学习、交流之用，切勿用于其他任何可能造成违法场景，否则后果自负！
