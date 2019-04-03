<p align="center">
    <a href="https://github.com/996icu/996.ICU/blob/master/LICENSE">
        <img alt="996icu" src="https://img.shields.io/badge/license-NPL%20(The%20996%20Prohibited%20License)-blue.svg">
    </a>
</p>

# PCOJ
一个使用python+PyQt5制作的客户端式的TSOJ。

所有数据来源以及数据上传接口均来自TSOJ: [web_TSOJ](https://acm.nuist.edu.cn/)

A executable-style programe for TSOJ using python + PyQt5.

The source of data and its API is powered by TSOJ: [web_TSOJ](https://acm.nuist.edu.cn/)

---

另注：工地英语警告！

NOTE: BROKEN ENGLISH IN THIS PAGE!

## 依赖库  Dependent Libraries
> pyqt5<br />
> SIP<br />
> markdown<br />
> requests

SIP安装可能会出现各种错误，百度有解决方案。

There may be some error while installing `SIP`, you can get the solution by google.

## 文件结构  File Structure
./images/        # 图片资源 用户数据的缓存  image resources and cache

./icon.ico      # UI的图标  logo for main form

./main.py       # UI的主要代码  source code

./pyTSOJ.py     # TSOJ的API  API for TSOJ

./small.ico     # 较小尺寸的icon 用于exe文件的图标  smaller icon using for the executable file

以下文件将会在运行过程中被创建

./images/temp/  # 存储用户头像、统计图  user's avantar and cartograms

./save.oj       # 存储用户登录状态  save user's login state

./login.oj      # 存储用户的用户名和密码(may be unsafe, whatever~)  save user's username and password

## 已知的BUG  knowing bug
修改头像时若单击“取消”会导致程序崩溃。

Click the 'cancel' button while editing avantar may cause crashes or throws exceptions.
