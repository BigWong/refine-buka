布卡漫画下载文件提取工具
========================
从布卡下载文件中抽取出漫画图片，并自动重命名其文件夹。

## 功能
支持提取布卡漫画现有的多种格式（包括.buka，.jpg.view，.bup.view），保存为普通图片，并自动对文件夹重命名为漫画名和卷名。

## 版本历史
### 2.4 版本
* 加入 -n, --keepwebp 选项保留 WebP 文件
* 日志输出漫画名
* 修复重命名问题

### 2.3 版本
* 优化错误处理、稳定性
* 默认启用 Pillow 来转换 PNG 到 JPG

### 2.2 版本
* 优化 Windows 下用户体验。默认输出位置改为与输入文件夹**相同**目录，而不是“当前文件夹”。

### 2.1 版本
* 修正几个重命名问题，dwebp 解码优先。

### 2.0 版本
* 将各类文件格式用对象表示，可访问属性及操作。
  * `BukaFile` 对 .buka 文件的解析与提取
  * `ComicInfo` 对 chaporder.dat 文件的解析
* `buildfromdb` 解析iOS平台下数据库 buka_store.sql，并实现其对 chaporder.dat 的转换。
* `DirMan` 实现自动重命名
* `DwebpMan` 实现 dwebp 进程池
* `DwebpPILMan` 实现 PIL 解码器线程池
* 重写重命名部分，实现规范化的命名逻辑。
* 日志模块，简化错误报告
* ……

可通过 `import buka` 来进行研究和扩展功能。

~~如果有 Pillow (PIL) 模块并支持 WebP，可直接解码成 png。~~
加 `--pil` 参数使用 Pillow (PIL) 模块直接解码成 jpg。见以下**问题**部分。

## 用法

必须使用 Python 3 运行程序。

**Windows 发行版**：直接将待转换文件/文件夹拖入软件图标即可，**不要**直接双击运行。在命令行环境将以下所有 `[python3] buka.py` 替换为 `buka.exe`。

```
用法: buka.py [-h] [-p NUM] [-c] [-l] [-n] [--pil] [--dwebp DWEBP]
               [-d buka_store.sql]
               input [output]

转换布卡漫画下载的漫画文件。

固定参数:
  input                 .buka 文件或包含下载文件的文件夹
                        通常位于 (安卓SD卡) /sdcard/ibuka/down
  output                指定输出文件夹 (默认 = ./output)

可选参数:
  -h, --help            显示帮助信息并退出
  -p NUM, --process NUM
                        dwebp 的最大进程数 / PIL 解码的最大线程数
                        (默认 = CPU 核心数)
  -c, --current-dir     默认输出文件夹改为 <当前目录>/output.
                        当指定 <output> 时忽略
  -l, --log             强制保存错误日志
  -n, --keepwebp        保留 WebP 格式图片，不转换
  --pil                 PIL/Pillow 解码优先，速度更快，但可能导致
                        内存泄漏。(Windows 编译发行版本不可用)
  --dwebp DWEBP         指定 dwebp 解码器位置
  -d buka_store.sql, --db buka_store.sql
                        指定 iOS 设备中 buka_store.sql 文件位置
                        此文件提供了额外的重命名信息
```

python3 buka.py -h
```
usage: buka.py [-h] [-p NUM] [-c] [-l] [-n] [--pil] [--dwebp DWEBP]
               [-d buka_store.sql]
               input [output]

Converts comics downloaded by Buka.

positional arguments:
  input                 The .buka file or the folder containing files
                        downloaded by Buka, which is usually located in
                        (Android) /sdcard/ibuka/down
  output                The output folder. (Default = ./output)

optional arguments:
  -h, --help            show this help message and exit
  -p NUM, --process NUM
                        The max number of running dwebp's. (Default = CPU
                        count)
  -c, --current-dir     Change the default output dir to ./output. Ignored
                        when specifies <output>
  -l, --log             Force logging to file.
  -n, --keepwebp        Keep WebP, don't convert them.
  --pil                 Perfer PIL/Pillow for decoding, faster, and may cause
                        memory leaks.
  --dwebp DWEBP         Locate your own dwebp WebP decoder.
  -d buka_store.sql, --db buka_store.sql
                        Locate the 'buka_store.sql' file in iOS devices, which
                        provides infomation for renaming.
```

可省略输出路径，默认为与输入文件夹同目录的output，加-c为当前目录下的output。
此output文件夹可能被重命名为适当的符合输入文件(夹)的名称。

然后就可以使用各种图片浏览器、漫画阅读器欣赏漫画。

## 问题
因为采用了 no WIC 版本的 dwebp.exe，对 Windows SP2 及以下操作系统已兼容。

如果采用外部程序 dwebp 解码，由于仅将 .bup/webp 格式直接转换成 png 格式，所以文件大小偏大。用户可自行转换成 jpg 以减小文件体积( `python3 png2jpg.py 目录` )。如果因内存泄漏导致崩溃，请再运行一次。

PIL/Pillow 解码的 webp 解码器存在内存泄漏，不适合处理上百张图片；而 png 文件太大，所以先尝试使用 dwebp 外部解码器，再尝试使用 Pillow 来转换 png。

## 授权

MIT 协议
