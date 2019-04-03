import sys
import os
import time

absPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0,absPath)

import matplotlib.pyplot as plt

import re
import requests
import base64
import json
from PIL import Image

import pickle as pkl

'''
依赖库:
requests
PIL
'''

class Urls:
    def __init__(self):
        self.root = r'https://acm.nuist.edu.cn' # 根目录
        self.login = self.root + r'/login' # 登陆
        self.home = self.root + r'/home' # 主页面
        self.info = self.root + r'/getuserinfo' # 个人信息
        self.prolist = self.root + r'/index/search' # 题目列表
        self.courlist = self.root + r'/course' # 课程列表
        self.course = self.root + r'/course/problem' # 课程题目
        self.search = self.root + r'/solution/search' # 状态搜索
        self.verify = self.root + r'/verify_refresh' # 验证码
        self.submit = self.root + r'/problem/submit' # 提交代码
        self.ranklist = self.root + r'/problem/ranklist/search' # 排行榜搜索
        self.avatar = self.root + r'/static/uploads/avatar/' # 头像
        self.image = self.root + r'/image' # 上传头像
        self.config = self.root + r'/info' # 修改昵称/签名

class VerifyCodeError(Exception):
    def __init__(self):
        self.args = ('请先获取验证码',)
        self.message = '请先获取验证码'
        self.code = 1

class WrongKeyError(Exception):
    def __init__(self, keyname, keyvalue):
        self.args = ('键值不正确，键"%s"的值不能为%s'%(keyname,keyvalue),)
        self.message = '键值不正确，键"%s"的值不能为%s'%(keyname,keyvalue)
        self.code = 2



URL = Urls()

class TSOJ:
    def __init__(self, timeout=5):
        self.sess = requests.Session()
        self.vcode = False
        self.online = False
        self.timeout = timeout

    def is_online(self):
        '''
检测当前是否还在线（在线是否还有效）
在线返回True 否则返回False
'''
        r = self.sess.get(URL.home, timeout=self.timeout)
        if r.status_code == 403:
            self.__init__(timeout = self.timeout)
            return False
        else:
            return True

    def getVcode(self):
        '''
返回一个base64码 为验证码图片
'''
        r = self.sess.get(URL.verify, timeout=self.timeout)
        b64code = r'data:image/png;base64,'+base64.b64encode(r.content).decode()
        self.vcode = True
        return b64code

    def login(self, uid, pwd, vcode):
        '''
登陆并保存状态
@uid - 用户名 一般为12或11位纯数字学号
@pws - 密码 初始密码为111111
@vcode - 验证码 4位字母数字 不区分大小写 以最后一次调用getVcode获得的图片为准
登录成功返回True 失败则返回False
'''
        find_xsrf = re.compile(r'<input type="hidden" name="_xsrf" value="([0-9a-zA-Z|]+)"/>')
        if not self.vcode: # 没调用过getvcode
            raise error.VerifyCodeError
        r = self.sess.get(URL.login, timeout=self.timeout).content.decode()
        temp = find_xsrf.search(r)
        _xsrf = temp.group(1) # 从登陆页面获取_xsrf

        data = {'username':uid,
                'password':pwd,
                'verifyCode':vcode,
                '_xsrf':_xsrf}
        self.username = uid
        r = self.sess.post(URL.login, data=data, timeout=self.timeout)
        if r.url == URL.login: # 登录失败
            return r.content.decode()
        self.online = True
        return True

    def course(self):
        '''
查看自己的课程列表
返回课程列表(只返回允许访问的)
'''
        headers = {'x-requested-with':'XMLHttpRequest',
                    'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        data = r'{"page":"1","perpage":10,"type":0}'
        r = self.sess.post(URL.courlist, data=data, headers=headers, timeout=self.timeout).json()
        count = r[0]['course_num'] # 获取课程总数
        data = r'{"page":"1","perpage":%s,"type":0}'%count
        r = self.sess.post(URL.courlist, data=data, headers=headers, timeout=self.timeout).json()[1:]
        ret = []
        for each in r:
            if each['select'] and each['status'] == '课程正在进行中':
                ret.append(each)
        return ret

    def proList(self, page, per_page=20, cid=0):
        '''
查看题目列表
@page - 第几页
@per_page - 每页返回多少条
@cid - 课程编号 为0则表示为练习题
返回(总个数,题目列表)
'''
        if cid == 0:
            headers = {'x-requested-with':'XMLHttpRequest',
                       'x-xsrftoken':self.sess.cookies.get('_xsrf')}
            data = r'{"key":"","page":%s,"perpage":"%s","level":""}'%(page,per_page)
            r = self.sess.post(URL.prolist, data=data, headers=headers, timeout=self.timeout).json()
            slidec = (len(r)+1)//2
            te,state = r[1:slidec],r[slidec:]
            pro = [{'pid':te[i][0],
                    'title':te[i][1],
                    'level':te[i][2],
                    'submit':te[i][3],
                    'accept':te[i][4],
                    'state':state[i]} for i in range(len(te))]
            return (r[0],pro)
        else:
            headers = {'x-requested-with':'XMLHttpRequest',
                       'x-xsrftoken':self.sess.cookies.get('_xsrf'),}
            # 先用GET方法访问problem?kcbs=[cid] 获得伪造码
            self.sess.get(URL.course, data={'kcbs':cid}, headers=headers, timeout=self.timeout)
            # 然后再用POST方法获得问题列表
            data = r'{"page":"%s","perpage":%s,"c_id":%s}'%(page,per_page,cid)
            r = self.sess.post(URL.course, data=data, headers=headers, timeout=self.timeout).json()
            pro = [{'pid':r[i]['id'],
                    'cid':cid,
                    'title':r[i]['title'],
                    'level':1,
                    'submit':-1,
                    'accept':-1,
                    'state':(0 if r[i]['status']=='Accepted' else
                             (2 if r[i]['status']=='To Do' else 1))} for i in range(1,len(r))]
            return (r[0],pro)

    def problem(self, pid, cid=0):
        '''
查看题目内容及相关信息
@pid - 题号
@cid - 课程编号 为0则表示为练习题
成功返回题目字典 失败返回None
'''
        if cid == 0:
            r = self.sess.get(URL.submit, data={'tw':pid}, timeout=self.timeout)
        else:
            if 'course%s'%cid not in self.sess.cookies:
                headers = {'x-requested-with':'XMLHttpRequest',
                           'x-xsrftoken':self.sess.cookies.get('_xsrf'),}
                # 先用GET方法访问problem?kcbs=[cid] 获得伪造码
                self.sess.get(URL.course, data={'kcbs':cid}, headers=headers, timeout=self.timeout)
            r = self.sess.get(URL.submit, data={'tw':pid,
                                                'ck':cid}, timeout=self.timeout)
        r = r.content.decode()
        title = re.search(r'<h2>\s*([0-9]{4}\s*:.*?)\s*</h2>',r)
        timelim = re.search(r'<font size="3">时间限制:&nbsp;</font>\n?<font size="3" color=".+">([0-9]+)MS</font>',r)
        spacelim = re.search(r'<font size="3">空间限制:&nbsp;</font>\n?<font size="3" color=".+">([0-9a-zA-Z]+)</font>',r)
        submitcount = re.search(r'<font size="3">提交数:&nbsp;</font>\n?<font size="3" color=".+">([0-9]+)</font>',r)
        passcount = re.search(r'<font size="3">通过数:&nbsp;</font>\n?<font size="3" color=".+">([0-9]+)</font>',r)
        content = re.search(r'<textarea id="text-input">((?:\n|.)+?)</textarea>',r)
        if content == None:
            return None
        else:
            return {'title':title.group(1),
                    'timeLimit':timelim.group(1),
                    'spaceLimit':spacelim.group(1),
                    'submitCount':int(submitcount.group(1)),
                    'passCount':int(passcount.group(1)),
                    'content':content.group(1)}

    def submit(self, pid, code, cid=0):
        '''
提交代码
@pid - 题号
@code - 代码
@cid - 课程编号 为0表示练习题
成功返回True 失败返回False
'''
        if cid != 0:
            if 'course%s'%cid not in self.sess.cookies:
                headers = {'x-requested-with':'XMLHttpRequest',
                           'x-xsrftoken':self.sess.cookies.get('_xsrf'),}
                # 先用GET方法访问problem?kcbs=[cid] 获得伪造码
                self.sess.get(URL.course, data={'kcbs':cid}, headers=headers, timeout=self.timeout)
            r = self.sess.get(URL.submit, data={'tw':pid,
                                                'ck':cid}, timeout=self.timeout)
        data = {'hb':pid,
                'chb':cid,
                'language':1,
                'sourcecode':code}
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        r = self.sess.post(URL.submit, data=data, headers=headers, timeout=self.timeout)
        r = r.json()
        if r['status'] == 0:
            return True
        else:
            return False


    def search(self, key, *, option='user', result='', lang=''):
        '''
查询状态情况
@key - 查询的键值
@option - 查询的类型 pro表示按题目查询 user表示按用户查询
@result - 筛选结果 为一个字符串 空字符串表示不筛选 0-AC 7-WA -1-CE -2-CLE 4-RE 1-TLE 3-MLE 5-SE 6-OLE 8-PE 9-SC
@lang - 筛选语言 为一个字符串 空字符串表示不筛选 0-C 1-C++ 2-C++14 3-java
返回一个元组 前面为相关信息（有多少条 字典） 后者为具体数据（列表 列表中是字典）
'''
        if option not in ('user','pro'):
            raise WrongKeyError('option',option)
        if result not in ('-2','-1','0','1','3','4','5','6','7','8','9',''):
            raise WrongKeyError('result',result)
        if lang not in ('0','1','2','3',''):
            raise WrongKeyError('lang',lang)
        
        data = {'key':str(key),
                'page':1,
                'option':option,
                'perpage':'500',
                'result':result,
                'lang':lang,
                'status':1,
                'cid':'0'}
        data = json.dumps(data)
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        r = self.sess.post(URL.search, data=data, headers=headers, timeout=self.timeout).json()
        return r[0],r[1:]

    def nickname(self):
        '''
获得用户的昵称
返回一个字符串 为用户设置的昵称
'''
        data = {'key':'none'}
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        r = self.sess.post(URL.info, data=data, headers=headers, timeout=self.timeout).json()
        return r[0][0]

    def userinfo(self):
        '''
获得用户的个人信息
返回一个字典 其中包含用户的昵称、真实姓名、帐号(学号)、头像、
                            签名、正误数、最近提交数
'''
        nickname = self.nickname()
        
        data = {'key':self.username,
                'page':1,
                'option':'user',
                'perpage':'1',
                'result':'',
                'lang':'',
                'status':1,
                'cid':'0'}
        data = json.dumps(data)
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        r = self.sess.post(URL.search, data=data, headers=headers, timeout=self.timeout).json()[1]
        uid = r['u_id']
        realname = r['u_realname']
        username = r['u_name']
        avatar = URL.avatar + str(uid) + '.jpg'

        r = self.sess.get(URL.home, headers=headers, timeout=self.timeout).content.decode()
        description = re.search(r'<h4 id="u_description">(.*?)</h4>',r).group(1)
        wrongc = re.search(r"\['错误率', ([0-9]+?)\]",r).group(1)
        rightc = re.search(r"name: '通过率',\ny: ([0-9]+?),",r).group(1)
        _submit = re.search(r'submit = \[([0-9, ]{40,})\]',r).group(1).split(',')
        week_submit = re.search(r'submit = \[([0-9, ]{1,40})\]',r).group(1).split(',')

        r_submit = []
        rweek_submit = []
        for each in _submit:
            r_submit.append(int(each))
        for each in week_submit:
            rweek_submit.append(int(each))

        return {'realname':realname,
                'username':username,
                'nickname':nickname,
                'avatar':avatar,
                'description':description,
                'acceptednum':int(rightc),
                'wrongnum':int(wrongc),
                'submit':r_submit,
                'weeksubmit':rweek_submit}

    def saveAvatar(self, path, url):
        '''
保存头像文件
@path - 保存的路径 格式为.jpg
@url - 由userinfo返回的avatar值
无返回值
'''
        r = self.sess.get(url).content
        with open(path, 'wb') as f:
            f.write(r)

    def generateImg(self, path, acceptednum, wrongnum, weeksubmit):
        '''
生成正误饼状图和提交柱状图
@path - 生成图片的存储地址
            若为str 则饼状图命名为pie.png 主张图命名为column.png
            若为list/tuple 则以其给出的文件名与地址存储
@acceptednum - 正确数
@wrongnum - 错误数
@weeksubmit - 周提交数
无返回值
'''
        plt.rc('font', family='SimHei', weight='bold', size='20')
        plt.rcParams['axes.unicode_minus'] = False
        
        size = acceptednum, wrongnum
        label = '正确率\n%.1f%%'%(100*acceptednum/(acceptednum+wrongnum)), \
                 '错误率\n%.1f%%'%(100*wrongnum/(acceptednum+wrongnum))
        color = '#f7a35c','#7cb5ec'
        explode = 0.1,0
        pie = plt.pie(size, colors=color, explode=explode, labels=label, startangle=90)
        plt.xlim(-1.2,1.2)
        plt.ylim(-1.2,1.2)
        if isinstance(path,str):
            plt.savefig(os.path.join(path,'pie.png'))
        else:
            plt.savefig(path[0])
        plt.close()

        plt.rc('font', family='SimHei', weight='bold', size='15')
        tempt = time.time()//86400*86400
        tempx = []
        for i in range(4):
            tempt -= 86400
            tb = time.localtime(tempt)
            tempt -= 86400*6
            ta = time.localtime(tempt)
            tempx.insert(0,'%d.%02d.%02d-\n%d.%02d.%02d'%(
                                           ta.tm_year,ta.tm_mon,ta.tm_mday,
                                           tb.tm_year,tb.tm_mon,tb.tm_mday))
        color = '#7cb5ec','#f7a35c','#90ed7d','#8085e9'
        tx = range(len(weeksubmit))
        ac = plt.bar(x=tx, height=weeksubmit,
                     width=0.4, alpha=1, color=color)
        plt.xticks(tx, tempx)
        plt.ylabel('submit次数')
        plt.ylim(0,max(weeksubmit)//5*5+5)
        plt.yticks([i for i in range(0,max(weeksubmit)//5*5+6,5)])
        plt.grid(True, 'major', 'y', color='gray', ls='-')
        ax = plt.gca()
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['left'].set_visible(False)
        index = -1
        for rect in ac:
            index += 1
            height = rect.get_height()
            plt.text(rect.get_x() + rect.get_width() / 2, height, str(height), ha="center",
                     va="bottom", color=color[index])
        if isinstance(path,str):
            plt.savefig(os.path.join(path,'column.png'))
        else:
            plt.savefig(path[1])
        plt.close()

    def ranklist(self, only_me=False, by_page=0):
        '''
查询ranklist
@only_me - 为True时只返回自己的信息 为False时返回全部
@by_page - 为0时返回全部信息 非0时返回以每页50个为规格的第by_page页的信息
返回(总数/排名,列表)
tips: 当only_me为True时，by_page参数不生效
'''
        headers = {'x-requested-with':'XMLHttpRequest',
                    'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        if by_page and not only_me:
            data = '{"perpage":"50","page":%s}'%(by_page)
            r = self.sess.post(URL.ranklist, data=data, headers=headers, timeout=self.timeout).json()
            return r[0]['found_rows'],r[1:]
        else:
            data = '{"perpage":"20","page":1}'
            r = self.sess.post(URL.ranklist, data=data, headers=headers, timeout=self.timeout).json()
            count = r[0]['found_rows']
            data = '{"perpage":"%s","page":1}'%(count)
            r = self.sess.post(URL.ranklist, data=data, headers=headers, timeout=10).json()[1:] #因为有极大概率卡住 所以设置10秒的timeout
            if only_me:
                for i in range(len(r)):
                    each = r[i]
                    if each['u_name'] == self.username:
                        return i,each
                return None
            else:
                return count,r

    def uploadAvatar(self, avatarPath):
        '''
上传头像
@avatarPath - 头像路径
上传成功返回True 否则返回False
'''
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        r = self.sess.get(URL.home, headers=headers, timeout=self.timeout).content.decode()
        _xsrf = re.search(r'<input type="hidden" name="_xsrf" value="(.+?)"/>',r).group(1)

        
        im = Image.open(avatarPath)
        files = {'file':(os.path.split(avatarPath)[1], open(avatarPath,'rb'), 'image/%s'%im.format.casefold()),
                 'x':(None,'0'),
                 'y':(None,'0'),
                 'w':(None,'400'),
                 'h':(None,'400'),
                 '_xsrf':(None,_xsrf)}
        r = self.sess.post(URL.image, files=files, headers=headers, timeout=5) # 上传可能会比较慢
        if r.status_code != 200:
            return False
        else:
            return True

    def reviseNickname(self, nickname):
        '''
修改昵称
@nickname - 将要修改成的昵称
上传成功返回True 否则返回False
'''
        if nickname == '':
            nickname = self.userinfo()['realname']
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        data = {'column':'u_nickname',
                'column_value':nickname}
        r = self.sess.post(URL.config, data=data, headers=headers, timeout=self.timeout)
        if r.status_code != 200:
            return False
        else:
            return True

    def reviseDescription(self, description):
        '''
修改签名
@description - 将要修改成的签名
上传成功返回True 否则返回False
'''
        headers = {'x-requested-with':'XMLHttpRequest',
                   'x-xsrftoken':self.sess.cookies.get('_xsrf')}
        data = {'column':'u_description',
                'column_value':description}
        r = self.sess.post(URL.config, data=data, headers=headers, timeout=self.timeout)
        if r.status_code != 200:
            return False
        else:
            return True

    def achievement(self):
        '''
返回达成的成就
'''
        achi = {}
        uinfo = self.userinfo()
        if uinfo['realname'] != uinfo['nickname']:
            achi['独树一帜'] = '修改了自己的昵称 就感觉自己很牛批！'
        if uinfo['description'] != '您还没有设置个性签名哦':
            achi['自我介绍'] = '有了自己的个性签名'
        t_rate = uinfo['acceptednum'] / (uinfo['wrongnum']+uinfo['acceptednum'])
        if t_rate > 0.5:
            achi['常胜将军']='AC率达到50%以上'
        if t_rate > 0.7:
            achi['是个大佬']='AC率达到70%以上'
        if t_rate < 0.3:
            achi['耐心']='AC率没有达到30% 这说明你还是蛮有耐心的'
        if uinfo['acceptednum'] >= 100:
            achi['百题斩']='AC数达到100'
        if uinfo['wrongnum'] >= 100:
            achi['坚韧不倒']='错误数达到100'
        if sum(uinfo['weeksubmit']) >= 10:
            achi['勤奋好学']='这周提交了10次以上'
        rkl = self.ranklist(by_page=1)[1]+self.ranklist(by_page=2)[1]
        for each in rkl:
            if each['u_name'] == uinfo['username']:
                achi['过关斩将']='处于总排行榜前100'
        state = self.search(key = self.username)[1]
        ac = 0
        wa = 0
        for each in state:
            if each['status'] == 'Accepted':
                ac += 1
                wa = 0
            else:
                wa += 1
                ac = 0
            if ac>=20:
                achi['渐入佳境']='连续AC了20次不间断'
            if ac>=40:
                achi['五 五 开']='连续AC了40次不间断'
            if wa>=10:
                achi['百折不挠']='连续失败10次'
        return achi
        

if __name__ == '__main__':
    pass
