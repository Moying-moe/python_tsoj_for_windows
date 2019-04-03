from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import sip

from PyQt5.QtWidgets import QLabel as _QLabel
from PyQt5.QtWidgets import QLineEdit as _QLineEdit

import pyTSOJ

import pickle as pkl
import markdown
import sys
import os
import random
from copy import deepcopy

class QLabel(_QLabel):
    clicked = pyqtSignal()
    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            self.clicked.emit()

class QSLabel(_QLabel): # 专门用来记录题号的标签 maybe remake
    clicked = pyqtSignal(int)
    def __init__(self, args, *, pid=0):
        super().__init__(args)
        self.pid = pid
        
    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == Qt.LeftButton:
            self.clicked.emit(self.pid)

class QLineEdit(_QLineEdit):
    def __init__(self, retDeal=lambda:None):
        _QLineEdit.__init__(self)
        self.retDeal = retDeal
    
    def keyPressEvent(self, event):
        _QLineEdit.keyPressEvent(self, event)
        if event.key() == Qt.Key_Return:
            self.retDeal()

def setFrame(grid,x,y, spanx=1,spany=1):
    frame = QFrame()
    frame.setFrameShape(QFrame.Box)
    frame.setLineWidth(2)
    grid.addWidget(frame, x,y, spanx,spany)

normalStyle = r'QLabel:hover{background-color:#bbbbbb;border:2px solid black;}QLabel{background-color:#f0f0f0;border:2px solid black;}'
selectStyle = r'QLabel{background-color:#bbbbbb;border:2px dashed black;}'
statusTran = {'Accepted':'AC',
              'Wrong Answer':'WA',
              'Compile Error':'CE',
              'Compile Limit Exceeded':'CLE',
              'Runtime Error':'RE',
              'Time Limit Exceeded':'TLE',
              'Memory Limit Exceeded':'MLE',
              'System Error':'SE',
              'Output Limit Exceeded':'OLE',
              'Presentation Error':'PE',
              'Similar Code':'SC'}
tranLevel = ['<font color="#c78b4f"><b>倔强青铜</b></font>',
             '<font color="#626876"><b>秩序白银</b></font>',
             '<font color="#e4cf5a"><b>荣耀黄金</b></font>',
             '<font color="#98bfcc"><b>尊贵铂金</b></font>',
             '<font color="#a1b4cc"><b>永恒钻石</b></font>',
             '<font color="black"><b>最强王者</b></font>']


###################################################################################################

class LoginForm(QWidget):
    def __init__(self):
        if os.path.exists('login.oj'):
            with open('login.oj','rb') as f:
                self.tsoj = pkl.load(f)
            if not self.tsoj.is_online():
                self.tsoj = pyTSOJ.TSOJ() # 已经无效 重新登陆
                os.remove('login.oj') # 删除状态文件
            else:
                global form2
                form2.activeit(self.tsoj)
                return None # 停止打开
        else:
            self.tsoj = pyTSOJ.TSOJ()
        super().__init__()
        self.setWindowTitle('TSOJ登陆')
        self.setWindowIcon(QIcon('icon.ico'))

        self.LoadUI()
        self.show()

        
        try:
            self.tsoj.problem(1001)
        except:
            _re = QMessageBox.warning(self,'警告',
                                     '服务器连接超时\n要退出程序吗? 如果要, 点击Yes',
                                     QMessageBox.No | QMessageBox.Yes)
            if _re == QMessageBox.Yes:
                self.close()

    def LoadUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        lb_username = QLabel(r'<font face="Microsoft YaHei" size="4">用户名:</font>')
        grid.addWidget(lb_username, 0, 0)

        if os.path.exists('save.oj'):
            with open('save.oj','rb') as f:
                userid, pwd = pkl.load(f)
        else:
            userid, pwd = '',''
        self.text_username = QLineEdit(self.make_login)
        self.text_username.setText(userid)
        self.text_username.setPlaceholderText('用户名一般为学号')
        grid.addWidget(self.text_username, 0, 1, 1, 2)

        lb_password = QLabel(r'<font face="Microsoft YaHei" size="4">密&nbsp;&nbsp;&nbsp;&nbsp;码:</font>')
        grid.addWidget(lb_password, 1, 0)

        self.text_password = QLineEdit(self.make_login)
        self.text_password.setEchoMode(QLineEdit.Password)
        self.text_password.setText(pwd)
        self.text_password.setContextMenuPolicy(Qt.NoContextMenu)
        self.text_password.setPlaceholderText('初始密码为111111')
        grid.addWidget(self.text_password, 1, 1, 1, 2)

        lb_verify = QLabel(r'<font face="Microsoft YaHei" size="4">验证码:</font>')
        grid.addWidget(lb_verify, 2, 0)

        self.text_verify = QLineEdit(self.make_login)
        self.text_verify.setPlaceholderText('4位验证码')
        grid.addWidget(self.text_verify, 2, 1)

        vc_b64 = self.tsoj.getVcode()
        self.img_verify = QLabel(r'<img src="%s" alt="验证码" />'%vc_b64)
        self.img_verify.clicked.connect(self.verifyRefresh)
        grid.addWidget(self.img_verify, 2, 2)

        btn_login = QPushButton('登陆')
        btn_login.clicked.connect(self.make_login)
        grid.addWidget(btn_login, 3, 0, 1, 3, alignment=Qt.AlignHCenter)

        self.resize(300, 153)

    def verifyRefresh(self):
        try:
            vc_b64 = self.tsoj.getVcode()
        except:
            _re = QMessageBox.warning(self,'警告',
                                     '服务器连接超时\n要退出程序吗? 如果要, 点击Yes',
                                     QMessageBox.No | QMessageBox.Yes)
            if _re == QMessageBox.Yes:
                self.close()
        self.img_verify.setText('')
        self.img_verify.setText(r'<img src="%s" alt="验证码" />'%vc_b64)

    def make_login(self):
        if self.text_username.text() == '':
            _re = QMessageBox.warning(self,'警告',
                                     '您没有输入用户名\n用户名一般是您的学号',
                                     QMessageBox.Ok)
            self.verifyRefresh()
            return None
        if self.text_password.text() == '':
            _re = QMessageBox.warning(self,'警告',
                                     '您没有输入密码\nTSOJ的初始密码为111111',
                                     QMessageBox.Ok)
            self.verifyRefresh()
            return None
        if len(self.text_verify.text()) != 4:
            _re = QMessageBox.warning(self,'警告',
                                     '请正确输入验证码',
                                     QMessageBox.Ok)
            self.verifyRefresh()
            return None
        
        username = self.text_username.text()
        password = self.text_password.text()
        verifyCode = self.text_verify.text()

        temp = self.tsoj.login(username, password, verifyCode)
        if not temp:
            _re = QMessageBox.warning(self,'警告',
                                     '登录失败！请检查账号密码是否有错，或验证码是否正确填写',
                                     QMessageBox.Ok)
            self.verifyRefresh()
            return None
        else:
            with open('save.oj','wb') as f:
                pkl.dump((username,password),f)
            with open('login.oj','wb') as f:
                pkl.dump(self.tsoj,f)
            global form2
            form2.activeit(self.tsoj)
            self.hide()

        

class MainForm(QWidget):
    def __init__(self):
        # 初始化函数 所有要用的内部变量最好都在这里初始化
        super().__init__()
        self.tsoj = pyTSOJ.TSOJ()
        self.setWindowTitle('TSOJ')
        self.setWindowIcon(QIcon('icon.ico'))

        self.page = 1
        self.nowcid = 0
        self.nowpid = 0
        self.spage = 1
        self.maxspage = 0
        self.rpage = 1
        self.maxrpage = 0

        self.LoadUI()
        self.hide()


    def activeit(self, tsoj):
        # 激活函数 因为部分功能需要登陆才能使用 需要先登陆才能调用的内容在此执行
        self.tsoj = tsoj
        try:
            temp = self.tsoj.is_online()
        except:
            _re = QMessageBox.warning(self,'警告',
                                     '服务器连接超时\n要退出程序吗? 如果要, 点击Yes',
                                     QMessageBox.No | QMessageBox.Yes)
            if _re == QMessageBox.Yes:
                self.close()
        if not temp:
            _re = QMessageBox.warning(self,'警告',
                                     '登录失败！请重试或联系开发者',
                                     QMessageBox.Ok)
            os.remove('login.oj')
            self.close()
        self.setWindowTitle('欢迎使用TSOJ - %s'%self.tsoj.nickname())

        self.FormProlistInit()
        self.FormProblemInit()
        self.FormStateInit()
        self.FormRankInit()
        self.FormMineInit()
        self.subFormProlist.setVisible(True)
        self.subFormProblem.setVisible(False)
        self.subFormState.setVisible(False)
        self.subFormRank.setVisible(False)
        self.subFormMine.setVisible(False)
        self.prolistClick()
        self.state_search(page=1,
                          key=self.tsoj.username,
                          option='user')
        self.txt_search.setText(self.tsoj.username)
        self.rank_search(1)
        self.show()

    def LoadUI(self):
        # 加载UI 左边栏以及附属窗体于此加载
        self.resize(1200,675)
        self.grid = QGridLayout()
        self.setLayout(self.grid)


        self.btn_prolist = QLabel('<div align="center"><img src="./images/code.png" height="75" width="75" /><br />题目</div>')
        self.btn_prolist.setFont(QFont('Microsoft YaHei',20))
        self.btn_prolist.setMaximumSize(150, 300)
        self.grid.addWidget(self.btn_prolist, 0,0)
        
        self.btn_state = QLabel('<div align="center"><img src="./images/state.png" height="75" width="75" /><br />状态</div>')
        self.btn_state.setFont(QFont('Microsoft YaHei',20))
        self.btn_state.setMaximumSize(150, 300)
        self.grid.addWidget(self.btn_state, 1,0)
        
        self.btn_rank = QLabel('<div align="center"><img src="./images/rank.png" height="75" width="75" /><br />排名</div>')
        self.btn_rank.setFont(QFont('Microsoft YaHei',20))
        self.btn_rank.setMaximumSize(150, 300)
        self.grid.addWidget(self.btn_rank, 2,0)
        
        self.btn_mine = QLabel('<div align="center"><img src="./images/mine.png" height="75" width="75" /><br />我的</div>')
        self.btn_mine.setFont(QFont('Microsoft YaHei',20))
        self.btn_mine.setMaximumSize(150, 300)
        self.grid.addWidget(self.btn_mine, 3,0)

        self.subFormProlist = QWidget()
        self.grid.addWidget(self.subFormProlist, 0,1, 4,5)
        self.subFormProlist.setVisible(False)

        self.subFormProblem = QWidget()
        self.grid.addWidget(self.subFormProblem, 0,1, 4,5)
        self.subFormProblem.setMaximumSize(1000,675)
        self.subFormProblem.setMinimumSize(1000,675)
        self.subFormProblem.setVisible(False)

        self.subFormState = QWidget()
        self.grid.addWidget(self.subFormState, 0,1, 4,5)
        self.subFormState.setMaximumSize(1000,675)
        self.subFormState.setMinimumSize(1000,675)
        self.subFormState.setVisible(False)

        self.subFormRank = QWidget()
        self.grid.addWidget(self.subFormRank, 0,1, 4,5)
        self.subFormRank.setMaximumSize(1000,675)
        self.subFormRank.setMinimumSize(1000,675)
        self.subFormRank.setVisible(False)

        self.subFormMine = QWidget()
        self.grid.addWidget(self.subFormMine, 0,1, 4,5)
        self.subFormMine.setMaximumSize(1000,675)
        self.subFormMine.setMinimumSize(1000,675)
        self.subFormMine.setVisible(False)

        self.btn_prolist.clicked.connect(self.prolistClick)
        self.btn_state.clicked.connect(self.stateClick)
        self.btn_rank.clicked.connect(self.rankClick)
        self.btn_mine.clicked.connect(self.mineClick)

        self.nowForm = self.subFormProlist
        self.stateClick() # 初始化状态


    def FormProlistInit(self):
        # 问题列表子窗口初始化
        form = self.subFormProlist
        grid = QGridLayout()
        form.setLayout(grid)


        _tlist = ['0: 练习题']
        temp = self.tsoj.course()
        index = seli = 0
        for each in temp:
            index += 1
            if each['id'] == self.nowcid:
                seli = index
            _tlist.append('%s: %s'%(each['id'],each['name']))
        self.cbb_course = QComboBox()
        self.cbb_course.setFont(QFont('Microsoft YaHei',10))
        self.cbb_course.addItems(_tlist)
        self.cbb_course.setCurrentIndex(seli)
        self.cbb_course.currentIndexChanged.connect(self.selectcourse)
        grid.addWidget(self.cbb_course, 0,0, 1,2)

        lb_pid = QLabel(r'<div align="left"><b>题目编号</b></div>')
        lb_pid.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(lb_pid, 1,0)

        lb_title = QLabel(r'<div align="left"><b>标题</b></div>')
        lb_title.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(lb_title, 1,1, 1,3)

        lb_ac = QLabel(r'<div align="left"><b>通过数</b></div>')
        lb_ac.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(lb_ac, 1,4)

        lb_subm = QLabel(r'<div align="left"><b>提交数</b></div>')
        lb_subm.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(lb_subm, 1,5)

        lb_lv = QLabel(r'<div align="left"><b>难度等级</b></div>')
        lb_lv.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(lb_lv, 1,6)

        lb_st = QLabel(r'<div align="left"><b>题目状态</b></div>')
        lb_st.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(lb_st, 1,7)

        if self.nowcid == 0:
            _maxcount, temp = self.tsoj.proList(self.page)
        else:
            _maxcount, temp = self.tsoj.proList(self.page,
                                                cid = self.nowcid)
        self.tlb1 = []
        self.tlb2 = []
        self.tlb3 = []
        self.tlb4 = []
        self.tlb5 = []
        self.tlb6 = []
        for i in range(20):
            if i>=len(temp):
                lb1 = QLabel()
                grid.addWidget(lb1, i+2,0)
                self.tlb1.append(lb1)
                lb2 = QLabel()
                grid.addWidget(lb2, i+2,1, 1,3)
                self.tlb2.append(lb2)
                lb3 = QLabel()
                grid.addWidget(lb3, i+2,4)
                self.tlb3.append(lb3)
                lb4 = QLabel()
                grid.addWidget(lb4, i+2,5)
                self.tlb4.append(lb4)
                lb5 = QLabel()
                grid.addWidget(lb5, i+2,6)
                self.tlb5.append(lb5)
                lb6 = QLabel()
                grid.addWidget(lb6, i+2,7)
                self.tlb6.append(lb6)
            else:
                e = deepcopy(temp[i])

                lb1 = QLabel(str(e['pid']))
                lb1.setFont(QFont('Microsoft YaHei',10))
                grid.addWidget(lb1, i+2,0)
                self.tlb1.append(lb1)

                lb2 = QSLabel(str(e['title']),pid=e['pid'])
                lb2.setFont(QFont('Microsoft YaHei',10))
                lb2.setStyleSheet(r'QLabel{text-decoration:underline;color:black;}'
                                  'QLabel:hover{text-decoration:underline;color:#337ab7;}')
                lb2.clicked.connect(self.proinfo)
                grid.addWidget(lb2, i+2,1, 1,3)
                self.tlb2.append(lb2)

                lb3 = QLabel((str(e['accept']) if e['accept']!=-1 else '--'))
                lb3.setFont(QFont('Microsoft YaHei',10))
                grid.addWidget(lb3, i+2,4)
                self.tlb3.append(lb3)

                lb4 = QLabel((str(e['submit']) if e['submit']!=-1 else '--'))
                lb4.setFont(QFont('Microsoft YaHei',10))
                grid.addWidget(lb4, i+2,5)
                self.tlb4.append(lb4)

                temptext = ['<font color="#c78b4f"><b>倔强青铜</b></font>',
                            '<font color="#626876"><b>秩序白银</b></font>',
                            '<font color="#e4cf5a"><b>荣耀黄金</b></font>',
                            '<font color="#98bfcc"><b>尊贵铂金</b></font>',
                            '<font color="#a1b4cc"><b>永恒钻石</b></font>',
                            '<font color="black"><b>最强王者</b></font>'][e['level']]
                lb5 = QLabel(temptext)
                lb5.setFont(QFont('Microsoft YaHei',10))
                grid.addWidget(lb5, i+2,6)
                self.tlb5.append(lb5)

                temptext = ''
                if e['state'] == 0:
                    temptext = '<font color="red">Accepted</font>'
                elif e['state'] == 1:
                    temptext = '<font color="limegreen">Attempted</font>'
                else:
                    temptext = '<font color="#337ab7">To Do</font>'
                lb6 = QLabel(temptext)
                lb6.setFont(QFont('Microsoft YaHei',10))
                grid.addWidget(lb6, i+2,7)
                self.tlb6.append(lb6)


        self.btn_leftpage = QPushButton('<<')
        self.btn_leftpage.clicked.connect(lambda: self.prolist_page(0))
        grid.addWidget(self.btn_leftpage, 22,2, alignment=Qt.AlignHCenter)
        self.btn_leftpage.setEnabled(False)

        self._maxpage = _maxcount//20+1
        self.btn_rightpage = QPushButton('>>')
        self.btn_rightpage.clicked.connect(lambda: self.prolist_page(1))
        grid.addWidget(self.btn_rightpage, 22,5, alignment=Qt.AlignHCenter)


        self.lb_pagenow = QLabel('%s/%s'%(self.page,self._maxpage))
        self.lb_pagenow.setFont(QFont('Microsoft YaHei',9))
        grid.addWidget(self.lb_pagenow, 22,3, 1,2, alignment=Qt.AlignHCenter)

    def FormProblemInit(self):
        # 问题详情页面初始化
        self.nowForm = self.subFormProblem

        form = self.subFormProblem
        grid = QGridLayout()
        form.setLayout(grid)

        lb_back = QLabel('<<返回')
        lb_back.setFont(QFont('Microsoft YaHei',10))
        lb_back.setStyleSheet(r'QLabel{text-decoration:underline;color:black;}'
                              r'QLabel:hover{text-decoration:underline;color:#337ab7;}')
        lb_back.setMaximumSize(125,17)
        lb_back.clicked.connect(self.prolistClick)
        grid.addWidget(lb_back, 0,0)

        self.lb_ptitle = QLabel('题目标题/如果你看到这个，说明你卡了，或者你很厉害')
        self.lb_ptitle.setFont(QFont('Microsoft YaHei',20))
        self.lb_ptitle.setMaximumSize(860,50)
        grid.addWidget(self.lb_ptitle, 0,1, 1,2)

        self.lb_pinfo = QLabel('题目相关信息')
        self.lb_pinfo.setFont(QFont('Microsoft YaHei',9))
        self.lb_pinfo.setMaximumSize(985, 25)
        grid.addWidget(self.lb_pinfo, 1,0, 1,3)

        self.lb_pcontent = QTextBrowser()
        self.lb_pcontent.setFont(QFont('Microsoft YaHei',10))
        self.lb_pcontent.setOpenLinks(False)
        self.lb_pcontent.setOpenExternalLinks(False)
        self.lb_pcontent.setMinimumSize(985,305)
        self.lb_pcontent.setMaximumSize(985,320)
        grid.addWidget(self.lb_pcontent, 2,0, 1,3)

        wgt = QWidget()
        wgt.setMinimumSize(985,30)
        wgt.setMaximumSize(985,30)
        grid.addWidget(wgt, 3,0, 1,3)

        lb_moban = QLabel('代码模板:',wgt)
        lb_moban.setFont(QFont('Microsoft YaHei',10))
        lb_moban.setMinimumSize(75,30)
        lb_moban.setMaximumSize(75,30)
        lb_moban.move(0,0)

        btn_duozu1 = QPushButton('标准多组输入1(while)',wgt)
        btn_duozu1.setMinimumSize(175,30)
        btn_duozu1.setMaximumSize(175,30)
        btn_duozu1.clicked.connect(lambda: self.duozu_code(1))
        btn_duozu1.move(75,0)

        btn_duozu2 = QPushButton('标准多组输入2(for)',wgt)
        btn_duozu2.setMinimumSize(175,30)
        btn_duozu2.setMaximumSize(175,30)
        btn_duozu2.clicked.connect(lambda: self.duozu_code(2))
        btn_duozu2.move(260,0)

        btn_duozu3 = QPushButton('空模板',wgt)
        btn_duozu3.setMinimumSize(175,30)
        btn_duozu3.setMaximumSize(175,30)
        btn_duozu3.clicked.connect(lambda: self.duozu_code(3))
        btn_duozu3.move(445,0)

        self.txt_code = QTextEdit()
        self.txt_code.setFont(QFont('Microsoft YaHei',8))
        self.txt_code.setMinimumSize(985,175)
        self.txt_code.setMaximumSize(985,190)
        self.txt_code.setTabStopWidth(16)
        grid.addWidget(self.txt_code, 4,0, 1,3)

        btn_psubmit =QPushButton('提交')
        btn_psubmit.setFont(QFont('Microsoft YaHei',10))
        btn_psubmit.setMaximumSize(100,30)
        btn_psubmit.clicked.connect(self.submit_code)
        grid.addWidget(btn_psubmit, 5,1, 1,3)

    def refresh_problem(self, pid, cid):
        # 刷新问题详情页的内容
        proc = self.tsoj.problem(pid, cid)
        self.lb_ptitle.setText(r'<p align="left">&nbsp;&nbsp;%s</p>'%(proc['title']))
        self.lb_pcontent.setText('%s'%(markdown.markdown(proc['content'])))
        self.lb_pinfo.setText('时间限制:<font color="red">%sms</font>, 空间限制:<font color="red">%s</font>, 通过数/提交数: <font color="red">%s</font>/<font color="red">%s</font>,\
通过率:<font color="red">%.2f%%</font>'%(proc['timeLimit'],
                                                                                proc['spaceLimit'],
                                                                                proc['passCount'],
                                                                                proc['submitCount'],
                                                                                (proc['passCount']*100/proc['submitCount'] if proc['submitCount']!=0 else 0)))
        self.txt_code.clear()
        self.txt_code.setText(r'''// TSOJ-%s %s

int main()
{
    
    return 0;
}'''%(pid,proc['title'].split(':',1)[1]))
        self.txt_code.setFocus()

    def FormStateInit(self):
        # 状态页初始化
        self.nowForm = self.subFormState

        form = self.subFormState
        grid = QGridLayout()
        form.setLayout(grid)

        self.txt_search = QLineEdit()
        self.txt_search.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(self.txt_search, 0,0, 1,2)

        self.cbb_userpro = QComboBox()
        self.cbb_userpro.setFont(QFont('Microsoft YaHei',10))
        self.cbb_userpro.addItems(['学生学号/姓名','题目编号/标题'])
        grid.addWidget(self.cbb_userpro, 0,2)

        btn_search = QPushButton('搜索')
        btn_search.setMaximumSize(100,40)
        btn_search.clicked.connect(self.search_click)
        grid.addWidget(btn_search, 0,3)

        self.tb_search = QTableWidget(20,9)
        self.tb_search.setMaximumSize(985, 600)
        self.tb_search.setFont(QFont('Microsoft YaHei',9))
        self.tb_search.setHorizontalHeaderLabels(['用户名','姓名','题目','题目名称','评测结果','内存','耗时','语言','提交时间'])
        self.tb_search.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可编辑
        self.tb_search.setSelectionBehavior(QAbstractItemView.SelectRows) # 整行选中
        self.tb_search.verticalHeader().setVisible(False) # 隐藏首列
        temp = (120,75,45,260,70,85,90,45,165)
        for i in range(9):
            self.tb_search.setColumnWidth(i,temp[i])
        self.tb_search.horizontalHeader().setDisabled(True) # 固定列宽
        for i in range(20):
            self.tb_search.setRowHeight(i,10)
        
        grid.addWidget(self.tb_search, 1,0, 1,5)

        self.btn_sleftpage = QPushButton('<<')
        self.btn_sleftpage.setMaximumSize(100,40)
        self.btn_sleftpage.clicked.connect(lambda: self.state_page(0))
        self.btn_sleftpage.setEnabled(False)
        grid.addWidget(self.btn_sleftpage, 2,1)

        self.lb_spage = QLabel('<p align="center">0/0</p>')
        self.lb_spage.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(self.lb_spage, 2,2)

        self.btn_srightpage = QPushButton('>>')
        self.btn_srightpage.setMaximumSize(100,40)
        self.btn_srightpage.clicked.connect(lambda: self.state_page(1))
        grid.addWidget(self.btn_srightpage, 2,3)

    def FormRankInit(self):
        # 排名页初始化
        self.nowForm = self.subFormRank

        form = self.subFormRank
        grid = QGridLayout()
        form.setLayout(grid)

        self.tb_rank = QTableWidget(50,9)
        self.tb_rank.setMaximumSize(985, 600)
        self.tb_rank.setFont(QFont('Microsoft YaHei',9))
        self.tb_rank.setHorizontalHeaderLabels(['排名','学号','姓名','昵称','学院','专业','年级','通过数','提交数'])
        self.tb_rank.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可编辑
        self.tb_rank.setSelectionBehavior(QAbstractItemView.SelectRows) # 整行选中
        self.tb_rank.verticalHeader().setVisible(False) # 隐藏首列
        temp = (45,120,70,170,155,240,45,55,55)
        for i in range(9):
            self.tb_rank.setColumnWidth(i,temp[i])
        self.tb_rank.horizontalHeader().setDisabled(True) # 固定列宽
        for i in range(50):
            self.tb_rank.setRowHeight(i,10)
        
        grid.addWidget(self.tb_rank, 0,0, 1,5)

        self.tb_myrank = QTableWidget(1,9)
        self.tb_myrank.setMaximumSize(985, 30)
        self.tb_myrank.setFont(QFont('Microsoft YaHei',9))
        self.tb_myrank.setEditTriggers(QAbstractItemView.NoEditTriggers) # 不可编辑
        self.tb_myrank.setSelectionBehavior(QAbstractItemView.SelectRows) # 整行选中
        self.tb_myrank.horizontalHeader().setVisible(False) # 隐藏首列
        self.tb_myrank.verticalHeader().setVisible(False) # 隐藏首列
        temp = (45,120,70,170,155,240,45,55,55)
        for i in range(9):
            self.tb_myrank.setColumnWidth(i,temp[i])
        self.tb_myrank.setRowHeight(0,10)
        self.tb_myrank.setItem(0,4,QTableWidgetItem('请不要多次点击"刷新'))
        self.tb_myrank.setItem(0,5,QTableWidgetItem('我的排名"否则程序可能会卡死'))
        
        grid.addWidget(self.tb_myrank, 1,0, 1,5)

        self.btn_rleftpage = QPushButton('刷新我的排名')
        self.btn_rleftpage.setMaximumSize(150,40)
        self.btn_rleftpage.clicked.connect(self.get_myrank)
        grid.addWidget(self.btn_rleftpage, 2,0)

        self.btn_rleftpage = QPushButton('<<')
        self.btn_rleftpage.setMaximumSize(100,40)
        self.btn_rleftpage.clicked.connect(lambda: self.rank_page(0))
        self.btn_rleftpage.setEnabled(False)
        grid.addWidget(self.btn_rleftpage, 2,1)

        self.lb_rpage = QLabel('<p align="center">0/0</p>')
        self.lb_rpage.setFont(QFont('Microsoft YaHei',10))
        grid.addWidget(self.lb_rpage, 2,2)

        self.btn_rrightpage = QPushButton('>>')
        self.btn_rrightpage.setMaximumSize(100,40)
        self.btn_rrightpage.clicked.connect(lambda: self.rank_page(1))
        grid.addWidget(self.btn_rrightpage, 2,3)

    def FormMineInit(self):
        # 我的 初始化
        self.nowForm = self.subFormMine
        form = self.subFormMine

        sinfo = self.tsoj.userinfo()
        self.tsoj.saveAvatar(r'./images/temp/avatar', sinfo['avatar'])
        self.tsoj.generateImg(r'./images/temp/', sinfo['acceptednum'],
                              sinfo['wrongnum'],sinfo['weeksubmit'])

        self.av_mask = QBitmap('./images/avatar_mask.jpg')
        av_img = QPixmap('./images/temp/avatar').scaled(150,150)
        av_img.setMask(self.av_mask)

        self.img_avatar = QLabel(form)
        self.img_avatar.setMaximumSize(150,150)
        self.img_avatar.setPixmap(av_img)
        self.img_avatar.move(15,5)

        self.lb_nickname = QLabel(sinfo['nickname'],form)
        self.lb_nickname.setFont(QFont('Microsoft YaHei',25))
        self.lb_nickname.resize(self.lb_nickname.fontMetrics().width(sinfo['nickname']),self.lb_nickname.fontMetrics().height())
        self.lb_nickname.move(185,35)

        self.btn_changenn = QPushButton('修改',form)
        self.btn_changenn.setFont(QFont('Microsoft YaHei',8))
        self.btn_changenn.setMaximumSize(50,self.btn_changenn.height())
        self.btn_changenn.clicked.connect(self.do_reviseN)
        self.btn_changenn.move(195+self.lb_nickname.fontMetrics().width(sinfo['nickname']),50)

        self.lb_description = QLabel(sinfo['description'],form)
        self.lb_description.setFont(QFont('Dengb',12))
        self.lb_description.resize(self.lb_description.fontMetrics().width(sinfo['description']),self.lb_description.fontMetrics().height())
        self.lb_description.move(185,100)

        self.btn_changedes = QPushButton('修改',form)
        self.btn_changedes.setFont(QFont('Microsoft YaHei',8))
        self.btn_changedes.setMaximumSize(50,self.btn_changedes.height())
        self.btn_changedes.clicked.connect(self.do_reviseD)
        self.btn_changedes.move(195+self.lb_description.fontMetrics().width(sinfo['description']),100)

        btn_logout = QPushButton('退出帐号',form)
        btn_logout.setFont(QFont('Microsoft YaHei',14))
        btn_logout.setStyleSheet(r'QPushButton{width:145px;height:40px;background-color:#ff6868;border-radius:10px;}'
                                 r'QPushButton:hover{width:145px;height:40px;background-color:#ff8f8f;border-radius:10px;}')
        btn_logout.clicked.connect(self.logout)
        btn_logout.move(855,0)

        btn_uploada = QPushButton('上传头像',form)
        btn_uploada.setFont(QFont('Microsoft YaHei',12))
        btn_uploada.setStyleSheet(r'QPushButton{width:120px;height:40px;background-color:#5cb85c;border-radius:10px;}'
                                 r'QPushButton:hover{width:120px;height:40px;background-color:#69d169;border-radius:10px;}')
        btn_uploada.clicked.connect(self.do_upload)
        btn_uploada.move(30,165)

        self.lb_username = QLabel('用户名: %s'%sinfo['username'],form)
        self.lb_username.setFont(QFont('Microsoft YaHei',12))
        self.lb_username.setStyleSheet(r'QLabel{height:40px;}')
        self.lb_username.move(45,270)

        self.lb_realname = QLabel('姓名: %s          '%sinfo['realname'],form)
        self.lb_realname.setFont(QFont('Microsoft YaHei',12))
        self.lb_realname.setStyleSheet(r'QLabel{height:40px;}')
        self.lb_realname.move(45,310)

        self.img_pie = QLabel('<img width="320" height="240" src="./images/temp/pie.png" />',form)
        self.img_pie.setStyleSheet(r'QLabel{width:320px;height:240px;border: 2px dashed black;border-right-width: 0px;}')
        self.img_pie.move(15,400)

        self.img_col = QLabel('<img width="640" height="440" src="./images/temp/column.png" />',form)
        self.img_col.setStyleSheet(r'QLabel{width:640px;height:240px;border: 2px dashed black;}')
        self.img_col.move(345,200)

        temp = self.tsoj.achievement()
        area_achi = QWidget(form)
        area_achi.setMaximumSize(800,50)
        area_achi.setMinimumSize(800,50)
        #area_achi.setStyleSheet(r'background-color:white;')
        area_achi.move(185,140)

        #a_grid = QGridLayout()
        #area_achi.setLayout(a_grid)

        tindex = -1
        for each in temp:
            tindex += 1
            lb_achi = QLabel('<p align="center">%s</p>'%each,area_achi)
            lb_achi.setFont(QFont('Microsoft YaHei',8))
            lb_achi.setStyleSheet(r'QLabel{width:80px;height:25px;background-color:#f0ad4e;color:#fff;font-weight:700;border-radius:10px;}')
            lb_achi.setMaximumSize(80,25)
            lb_achi.setMinimumSize(80,25)
            lb_achi.move((tindex%8)*100,(tindex//8)*25)
            lb_achi.setToolTip(temp[each])

    def do_reviseN(self):
        value, ok = QInputDialog.getText(self, "请输入", "输入新的昵称(不超过12个字):", QLineEdit.Normal, "")
        if ok:
            if len(value)>12:
                QMessageBox.warning(self,'提示',
                                '昵称不能超过12个字哦！',
                                QMessageBox.Ok)
            else:
                _re = self.tsoj.reviseNickname(value)
                if _re:
                    QMessageBox.warning(self,'成功',
                                '修改成功!',
                                QMessageBox.Ok)
                    self.refresh_mine()
                else:
                    QMessageBox.warning(self,'失败',
                                '修改失败! 请稍候重试',
                                QMessageBox.Ok)

    def do_reviseD(self):
        value, ok = QInputDialog.getText(self, "请输入", "输入新的个性签名:", QLineEdit.Normal, "")
        if ok:
            _re = self.tsoj.reviseDescription(value)
            if _re:
                QMessageBox.warning(self,'成功',
                            '修改成功!',
                            QMessageBox.Ok)
                self.refresh_mine()
            else:
                QMessageBox.warning(self,'失败',
                            '修改失败! 请稍候重试',
                            QMessageBox.Ok)

    def do_upload(self):
        filename = QFileDialog.getOpenFileName(caption='头像',filter='*.png\n*.jpg')[0]
        _re = self.tsoj.uploadAvatar(filename)
        if _re:
            QMessageBox.warning(self,'成功',
                        '修改成功!',
                        QMessageBox.Ok)
            self.refresh_mine()
        else:
            QMessageBox.warning(self,'失败',
                        '修改失败! 请稍候重试',
                        QMessageBox.Ok)

    def refresh_prolist(self):
        if self.nowcid == 0:
            _maxcount, temp = self.tsoj.proList(self.page)
        else:
            _maxcount, temp = self.tsoj.proList(self.page,
                                                cid = self.nowcid)
        for i in range(20):
            if i>=len(temp):
                self.tlb1[i].setText('')
                self.tlb2[i].setText('')
                self.tlb3[i].setText('')
                self.tlb4[i].setText('')
                self.tlb5[i].setText('')
                self.tlb6[i].setText('')
            else:
                e = deepcopy(temp[i])

                self.tlb1[i].setText(str(e['pid']))

                self.tlb2[i].setText(str(e['title']))
                self.tlb2[i].pid = e['pid']

                self.tlb3[i].setText((str(e['accept']) if e['accept']!=-1 else '--'))

                self.tlb4[i].setText((str(e['submit']) if e['submit']!=-1 else '--'))

                self.tlb5[i].setText(tranLevel[e['level']])

                temptext = ''
                if e['state'] == 0:
                    temptext = '<font color="red">Accepted</font>'
                elif e['state'] == 1:
                    temptext = '<font color="limegreen">Attempted</font>'
                else:
                    temptext = '<font color="#337ab7">To Do</font>'
                self.tlb6[i].setText(temptext)

        self._maxpage = _maxcount//20+1
        
        self.lb_pagenow.setText('%s/%s'%(self.page,self._maxpage))
        

    def refresh_mine(self):
        sinfo = self.tsoj.userinfo()
        self.tsoj.saveAvatar(r'./images/temp/avatar', sinfo['avatar'])
        self.tsoj.generateImg(r'./images/temp/', sinfo['acceptednum'],
                              sinfo['wrongnum'],sinfo['weeksubmit'])

        av_img = QPixmap('./images/temp/avatar').scaled(150,150)
        av_img.setMask(self.av_mask)

        self.img_avatar.setPixmap(av_img)

        self.lb_nickname.setText(sinfo['nickname'])
        self.lb_nickname.resize(self.lb_nickname.fontMetrics().width(sinfo['nickname']),self.lb_nickname.fontMetrics().height())

        self.btn_changenn.move(195+self.lb_nickname.fontMetrics().width(sinfo['nickname']),50)

        self.lb_description.setText(sinfo['description'])
        self.lb_description.resize(self.lb_description.fontMetrics().width(sinfo['description']),self.lb_description.fontMetrics().height())

        self.btn_changedes.move(195+self.lb_description.fontMetrics().width(sinfo['description']),100)

        self.lb_username.setText('用户名: %s'%sinfo['username'])

        self.lb_realname.setText('姓名: %s'%sinfo['realname'])
        
        self.img_pie.setText('')
        self.img_pie.setText('<img width="320" height="240" src="./images/temp/pie.png" />')

        self.img_col.setText('')
        self.img_col.setText('<img width="640" height="440" src="./images/temp/column.png" />')

    def logout(self):
        _re = QMessageBox.warning(self,'警告',
                                        '要退出登录吗？',
                                        QMessageBox.Ok, QMessageBox.Cancel)
        if _re == QMessageBox.Ok:
            os.remove('login.oj')
            self.close()

    def submit_code(self):
        # 问题详情页"提交"按钮 提交代码
        if self.nowpid == 0:
            QMessageBox.warning(self,'提示',
                                '题目错误！请重新打开题目。\n若仍错误，请联系开发人员。',
                                QMessageBox.Ok)
        else:
            _re = self.tsoj.submit(self.nowpid, self.txt_code.toPlainText(), self.nowcid)
            if not _re:
                QMessageBox.warning(self,'提示',
                                        '提交失败！请稍候重试或重新登陆。\n若仍失败，请联系开发人员。',
                                        QMessageBox.Ok)
            else:
                _re = QMessageBox.warning(self,'提示',
                                        '提交成功！单击"是"查看评测结果，单击"取消"继续做题',
                                        QMessageBox.Ok, QMessageBox.Cancel)
                if _re == QMessageBox.Ok:
                    self.state_search(page=1,
                                      key=self.tsoj.username,
                                      option='user')
                    self.stateClick()
                    pass
                elif _re == QMessageBox.Cancel:
                    self.prolistClick()

    def state_page(self, command):
        # 状态页的翻页按钮逻辑
        if command==0: # 左
            self.spage -= 1
            if self.spage==1:
                self.btn_sleftpage.setEnabled(False)
            self.btn_srightpage.setEnabled(True)
            self.tempdata_page(self.spage)
        else: # 右
            self.spage += 1
            if self.spage==self.maxspage:
                self.btn_srightpage.setEnabled(False)
            self.btn_sleftpage.setEnabled(True)
            self.tempdata_page(self.spage)
        self.lb_spage.setText('<p align="center">%s/%s</p>'%(self.spage,self.maxspage))

    def rank_page(self, command):
        # 排名页的翻页按钮逻辑
        if command==0: # 左
            self.rpage -= 1
            self.rank_search(self.rpage)
            if self.rpage==1:
                self.btn_rleftpage.setEnabled(False)
            self.btn_rrightpage.setEnabled(True)
        else: # 右
            self.rpage += 1
            self.rank_search(self.rpage)
            if self.rpage==self.maxrpage:
                self.btn_rrightpage.setEnabled(False)
            self.btn_rleftpage.setEnabled(True)

    def rank_search(self, page):
        # 排名页内容的获取/显示
        count,temp = self.tsoj.ranklist(only_me=False, by_page=page)
        self.maxrpage = (count-1)//50+1
        self.lb_rpage.setText('<p align="center">%s/%s</p>'%(page,self.maxrpage))

        index = -1
        for each in temp:
            index += 1
            self.tb_rank.setItem(index,0,QTableWidgetItem(str((page-1)*50+index+1)))
            self.tb_rank.setItem(index,1,QTableWidgetItem(each['u_name']))
            self.tb_rank.setItem(index,2,QTableWidgetItem(each['u_realname']))
            self.tb_rank.setItem(index,3,QTableWidgetItem(each['u_nickname']))
            self.tb_rank.setItem(index,4,QTableWidgetItem(each['u_organization']))
            self.tb_rank.setItem(index,5,QTableWidgetItem(each['u_major']))
            self.tb_rank.setItem(index,6,QTableWidgetItem(str(each['u_grade'])))
            self.tb_rank.setItem(index,7,QTableWidgetItem(str(each['u_accept'])))
            self.tb_rank.setItem(index,8,QTableWidgetItem(str(each['u_submit'])))

    def get_myrank(self):
        # 刷新/显示我的排名信息
        c,myrank = self.tsoj.ranklist(only_me=True) # TO DO: only_me模式的timeout优化
        temp = [str(c+1),
                myrank['u_name'],
                myrank['u_realname'],
                myrank['u_nickname'],
                myrank['u_organization'],
                myrank['u_major'],
                str(myrank['u_grade']),
                str(myrank['u_accept']),
                str(myrank['u_submit'])]
        for i in range(len(temp)):
            self.tb_myrank.setItem(0,i,QTableWidgetItem(temp[i]))

    def tempdata_page(self, page):
        # 状态页的缓存翻页功能（不多次搜索
        temp = self.tempsearch
        start = (page-1)*20
        if page*20>len(temp):
            end = len(temp)
        else:
            end = page*20
        index = -1
        for each in temp[start:end]:
            index += 1
            self.tb_search.setItem(index,0,QTableWidgetItem(each['u_name']))
            self.tb_search.setItem(index,1,QTableWidgetItem(each['u_realname']))
            self.tb_search.setItem(index,2,QTableWidgetItem(str(each['p_id'])))
            self.tb_search.setItem(index,3,QTableWidgetItem(each['p_title']))
            self.tb_search.setItem(index,4,QTableWidgetItem(statusTran[each['status']]))
            self.tb_search.setItem(index,5,QTableWidgetItem(each['memory']))
            self.tb_search.setItem(index,6,QTableWidgetItem(each['time']))
            self.tb_search.setItem(index,7,QTableWidgetItem(each['lang']))
            self.tb_search.setItem(index,8,QTableWidgetItem(each['post_time']))
        if index<19:
            for i in range(index+1,20):
                self.tb_search.setItem(i,0,QTableWidgetItem())
                self.tb_search.setItem(i,1,QTableWidgetItem())
                self.tb_search.setItem(i,2,QTableWidgetItem())
                self.tb_search.setItem(i,3,QTableWidgetItem())
                self.tb_search.setItem(i,4,QTableWidgetItem())
                self.tb_search.setItem(i,5,QTableWidgetItem())
                self.tb_search.setItem(i,6,QTableWidgetItem())
                self.tb_search.setItem(i,7,QTableWidgetItem())
                self.tb_search.setItem(i,8,QTableWidgetItem())

    def search_click(self, page=1):
        # 状态页的搜索按钮
        key = self.txt_search.text()
        option = ('user','pro')[self.cbb_userpro.currentIndex()]
        page = 1
        self.state_search(page=page,
                          key=key,
                          option=option)

    def state_search(self, page, key, *, option='user', result='', lang=''):
        # 状态页的搜索逻辑
        # TO DO: 模仿排名页进行函数合并和简化
        temp1,temp = self.tsoj.search(key=key,
                                       option=option,
                                       result=result,
                                       lang=lang)
        count = temp1['solu_num']
        self.maxspage = (count-1)//20+1
        start = (page-1)*20
        if page*20>len(temp):
            end = len(temp)-1
        else:
            end = page*20
        index = -1
        self.tempsearch = temp
        for each in temp[start:end]:
            index += 1
            self.tb_search.setItem(index,0,QTableWidgetItem(each['u_name']))
            self.tb_search.setItem(index,1,QTableWidgetItem(each['u_realname']))
            self.tb_search.setItem(index,2,QTableWidgetItem(str(each['p_id'])))
            self.tb_search.setItem(index,3,QTableWidgetItem(each['p_title']))
            self.tb_search.setItem(index,4,QTableWidgetItem(statusTran[each['status']]))
            self.tb_search.setItem(index,5,QTableWidgetItem(each['memory']))
            self.tb_search.setItem(index,6,QTableWidgetItem(each['time']))
            self.tb_search.setItem(index,7,QTableWidgetItem(each['lang']))
            self.tb_search.setItem(index,8,QTableWidgetItem(each['post_time']))
        self.lb_spage.setText('<p align="center">%s/%s</p>'%(self.spage,self.maxspage))

    def prolist_page(self, command):
        if command == 0: # 左
            self.page -= 1
            if self.page < 1:
                self.page = 1
            if self.page == 1:
                self.btn_leftpage.setEnabled(False)
            self.btn_rightpage.setEnabled(True)
            self.refresh_prolist()
        elif command == 1: # 右
            self.page += 1
            if self.page > self._maxpage:
                self.page = self._maxpage
            if self.page == self._maxpage:
                self.btn_rightpage.setEnabled(False)
            self.btn_leftpage.setEnabled(True)
            self.refresh_prolist()

    def selectcourse(self):
        self.nowcid = int(self.cbb_course.currentText().split(':',1)[0])
        self.page = 1
        self.refresh_prolist()

    def duozu_code(self, t):
        # 套用多组输入模板代码的按钮逻辑
        if self.txt_code.toPlainText() != '':
            _re = QMessageBox.warning(self,'提示',
                                            '您的文本框内有文本，使用模板会清空文本框。\n如果确认要使用模版，请点击"是"，否则点击"取消"。',
                                            QMessageBox.Ok, QMessageBox.Cancel)
            if _re != QMessageBox.Ok:
                return None
        self.txt_code.clear()
        if t == 1:
            cc = '''\t// 在此处定义需要输入的变量
    while(scanf("",)!=EOF) // 请完善此处scanf语句
    {
        // 在此处编写处理逻辑
    }'''
        elif t == 2:
            cc = '''\tint T;
    scanf("%d",&T);
    for(;T--;)
    {
        // 在此处编写处理逻辑
    }'''
        else:
            cc = '\t\t'
        self.txt_code.setText(r'''#include <stdio.h>

int main()
{
%s
    return 0;
}'''%(cc))

    def proinfo(self, pid):
        # 进入问题详情页
        self.nowpid = pid
        self.refresh_problem(pid, self.nowcid)
        self.subFormProlist.setVisible(False)
        self.subFormProblem.setVisible(True)
        self.subFormState.setVisible(False)
    
    def prolistClick(self):
        # 切换到“问题”选择卡
        self.nowpid = 0
        self.refresh_prolist()
        self.subFormProlist.setVisible(True)
        self.subFormProblem.setVisible(False)
        self.subFormState.setVisible(False)
        self.subFormRank.setVisible(False)
        self.subFormMine.setVisible(False)
        self.btn_prolist.setStyleSheet(selectStyle)
        self.btn_state.setStyleSheet(normalStyle)
        self.btn_rank.setStyleSheet(normalStyle)
        self.btn_mine.setStyleSheet(normalStyle)

    def stateClick(self):
        # 切换到“状态”选择卡
        self.subFormProblem.setVisible(False)
        self.subFormProlist.setVisible(False)
        self.subFormState.setVisible(True)
        self.subFormRank.setVisible(False)
        self.subFormMine.setVisible(False)
        self.btn_prolist.setStyleSheet(normalStyle)
        self.btn_state.setStyleSheet(selectStyle)
        self.btn_rank.setStyleSheet(normalStyle)
        self.btn_mine.setStyleSheet(normalStyle)

    def rankClick(self):
        # 切换到“状态”选择卡
        self.subFormProblem.setVisible(False)
        self.subFormProlist.setVisible(False)
        self.subFormState.setVisible(False)
        self.subFormRank.setVisible(True)
        self.subFormMine.setVisible(False)
        self.btn_prolist.setStyleSheet(normalStyle)
        self.btn_state.setStyleSheet(normalStyle)
        self.btn_rank.setStyleSheet(selectStyle)
        self.btn_mine.setStyleSheet(normalStyle)

    def mineClick(self):
        # 切换到“我的”选择卡
        self.subFormProblem.setVisible(False)
        self.subFormProlist.setVisible(False)
        self.subFormState.setVisible(False)
        self.subFormRank.setVisible(False)
        self.subFormMine.setVisible(True)
        self.btn_prolist.setStyleSheet(normalStyle)
        self.btn_state.setStyleSheet(normalStyle)
        self.btn_rank.setStyleSheet(normalStyle)
        self.btn_mine.setStyleSheet(selectStyle)
        
            



if __name__ == '__main__':
    app = QApplication(sys.argv)
    form2 = MainForm()
    form1 = LoginForm()
    app.exit(app.exec_())
