'''
# date： 2021.10.12
# objection：修改U101，每个数据的单位单独保存并显示
# author： Superbruy, Yang JH
'''
import tkinter
from tkinter import *
from tkinter import ttk
import os, glob
import time
import datetime
import psutil
from tkinter.messagebox import *
from tkinter.filedialog import askdirectory
import sqlite3
import json
from rili import Calendar as ca

root = Tk()
root.title('传感器信息显示')  # 窗口名字
root.geometry('1100x700')  # 设置主窗口大小

# 一些关键的全局变量
number_list = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
current_machine = "TCPServer"
machine_path_list = glob.glob("./{}/log/*.txt".format(current_machine))  # get all txt files
file_num = len(machine_path_list)
num_width = 150
num_height = 40
value_width = 90
value_height = 40
unit_width = 60
unit_height = 40
x_pad = 30
y_pad = 10
row_num = 6
column_num = 6
contents_list = {}
machine_ID = ''
contents = []
vallist = []
unit_list = {}  # ‘2711’：[pa, m...]
unit_con = []  # 对应contents
unit_con2 = []  # 对应vallist
heartbeat_time = []
connect = False  # 是否连接的状态
lasttime = ()  # 上次接受的心跳包的时间
directory_address = ''  # 选择文件夹的全局变量
directory_address_show = StringVar()
total_lines = 0  # 用于统计devicedata中数据有无变化
sensor_dict = {}
info_name = '' #查询的传感器表名
sensor_query_id = '所有机器'

def date_str_gain():
    global info_name, sensor_query_id
    x, y = root.winfo_x()+20, root.winfo_y()+200
    date_str=''
    for date in [ca((x, y), 'lr').selection()]:
        if date:
            date_choose_str1.set(date)
        date_str = date.replace('-', '_')
    info_name = 'machine_info'+'_'+date_str
    l_count = cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name = '{}'".format(info_name))
    for count in l_count :
        if count[0]== 0:
            showinfo('警告', '当天无记录，请选择其他日期')
            return
    sensor_id_list = cur.execute('SELECT distinct mid FROM {}'.format(info_name))
    id_list_temp = ['所有机器']
    for i in sensor_id_list:
        id_list_temp.append(i)
    sensor_id_choose['value'] = id_list_temp
    sensor_query_id = '所有机器'
    sensor_id_choose.current(0)



# 选择文件夹按钮的执行函数，将文件夹路径存入到全局变量中，并显示在框内
def choose_directory():
    global directory_address
    directory_address = tkinter.filedialog.askdirectory()
    directory_address = directory_address.replace("/", "\\")
    directory_address_show.set(directory_address)
    if directory_address.endswith('log'):
        pass
    elif directory_address.endswith('TCPServer'):
        directory_address += '/log'
    else:
        showinfo('警告', '文件夹选择错误，请选择正确文件夹')
    get_realtime_data(10)
    update_cmblist()


'''
心跳报警部分
'''


# 心跳报警循环函数
def heart_loop():
    heartbeat()
    detect_heartbeat()
    root.after(2000, heart_loop)


# 心跳信息读取
def heartbeat():
    global heartbeat_time, connect
    if directory_address == '':
        return
    heart_file_list = glob.glob("{}/heartbeat*".format(directory_address))
    sort_heart = sorted(heart_file_list, key=lambda x: os.path.getmtime(x))  # Sort by time of most recent modification
    latest_heart_path = sort_heart[-1]  # list member: path
    c = []
    try:
        with open(latest_heart_path) as f:
            for line in f:
                if line.startswith("20"):
                    line = line.rstrip("\n")
                    c.append(line)
            need = c[-1]
            pre, mid, rear = need.split('\t')
            hadtime = time.strptime(pre, "%Y-%m-%d %H:%M:%S")
            nowtime = time.localtime(time.time())
            if len(heartbeat_time) == 0 or heartbeat_time[0] != hadtime:
                heartbeat_time = [hadtime, nowtime]
    except EXCEPTION:
        print("read file error\n")


# 心跳信号判断
def detect_heartbeat():
    global heartbeat_time, connect, lasttime
    if directory_address == '':
        return
    nowtime = time.localtime(time.time())
    pretime = heartbeat_time[0]
    pretime_num = datetime.datetime(pretime[0], pretime[1], pretime[2], pretime[3], pretime[4], pretime[5])
    nowtime_num = datetime.datetime(nowtime[0], nowtime[1], nowtime[2], nowtime[3], nowtime[4], nowtime[5])
    timedif = (nowtime_num - pretime_num).total_seconds()
    nowtime_str = time.strftime("%Y-%m-%d %H:%M:%S", nowtime)
    pretime_str = time.strftime("%Y-%m-%d %H:%M:%S", pretime)
    if connect == False and timedif < 70 and pretime != lasttime:
        connect = True
        if lasttime != ():
            hb_treeview.insert('', 'end', values=('连接', nowtime_str, pretime_str))
        mh_connect.configure(text='心跳包正常接收中')
        lasttime = pretime
    elif connect == True and timedif > 62:
        hb_treeview.insert('', 'end', values=('断开', nowtime_str, pretime_str))
        connect = False
        lasttime = pretime
        mh_connect.configure(text='连接已断开')


'''
传感器参数显示部分，包括下拉菜单机器号选择
'''


# 判断devicedata是否有变化，每次打开都会新建一个dd文件，所以total_lines可以初始化为0
def is_change():
    global total_lines
    c = []
    dd_file_list = glob.glob("./{}/log/DeviceData*".format(current_machine))
    sort_dd = sorted(dd_file_list, key=lambda x: os.path.getmtime(x))  # Sort by time of most recent modification
    latest_file = sort_dd[-1]
    with open(latest_file) as f:
        for line in f:
            if line.startswith('202'):
                line = line.rstrip('\n')
                c.append(line)
    if len(c) != total_lines:
        total_lines = len(c)
        return c[-1]
    else:
        return False


def write_into_db(item):
    global sensor_dict
    pre, mid, rear = item.split("\t")
    _, time_v = pre.split(" ")
    rear = rear.split("#")
    m_v = rear[0]
    for k in range(1, 131):
        key = "sensor{}".format(k)
        sensor_dict.update({key: rear[k]})
    sensor_v = json.dumps(sensor_dict)
    cur.execute("insert into {}(time, mid, sensor_info) values(?,?,?)".format(today_sheet), (time_v, m_v, sensor_v))
    conn.commit()


# 显示参数部分循环函数
def loop():
    get_realtime_data(3)
    # 判断dd文件是否更新，更新则修改数据库内容
    last_line_c = is_change()
    if last_line_c:
        write_into_db(last_line_c)
    update_contents()
    update_cmblist()
    root.after(10000, loop)


def get_realtime_data(num):  # 读取最近的num个文件的数据并更新全局字典
    global file_num, contents_list, directory_address
    # 必须选择log文件夹或TCPServer文件夹
    dd_file_list = glob.glob("{}/DeviceData*".format(directory_address))
    sort_dd = sorted(dd_file_list, key=lambda x: os.path.getmtime(x))  # Sort by time of most recent modification
    latest_dd_path = sort_dd[-num:]  # list member: path
    get_latest_lines(latest_dd_path)


def get_latest_lines(path_list):
    global contents_list, unit_list
    for path in path_list:
        c = []
        try:
            with open(path) as f:
                for line in f:
                    if line.startswith('202'):
                        line = line.rstrip('\n')
                        c.append(line)
                for need in c:
                    pre, mid, rear = need.split('\t')
                    rear = rear.split('#')
                    v = []
                    unit = []
                    for i, item in enumerate(rear):
                        if '.' in item:
                            p1, p2 = item.split('.')
                            depart = get_point(p2)
                            value_part = p1 + '.' + p2[:depart]
                            unit_part = p2[depart:]
                            v.append(value_part)
                            unit.append(unit_part)
                        else:
                            depart = get_point(item)
                            value_part = item[:depart]
                            unit_part = item[depart:]
                            v.append(value_part)
                            unit.append(unit_part)
                    contents_list[rear[0]] = v[1:]
                    unit_list[rear[0]] = unit[1:]
        except EXCEPTION:
            print("read file error\n")


def get_point(arr):
    '''
    字符串中第一个不是数字的字符的位置
    :return:
    '''
    cou = 1
    for chars in arr:
        if chars in number_list:
            cou += 1
        else:
            return cou - 1


def update_contents():  # 更新参数
    global contents, contents_list, machine_ID, unit_list, unit_con
    contents = contents_list[machine_ID]
    unit_con = unit_list[machine_ID]
    change_show()


def update_cmblist():  # 更新下拉菜单机器号
    cmb_value = []
    for ckey in sorted(contents_list):
        cmb_value.append(ckey)
    cmb['value'] = cmb_value


def choose_machine(event):  # 下拉菜单事件绑定
    global contents_list, contents, machine_ID, unit_list, unit_con
    # if cmb.get() != '选择机器ID':
    machine_ID = cmb.get()
    contents = contents_list[machine_ID]
    unit_con = unit_list[machine_ID]
    change_show()
    loop()


def change_show():
    global contents, vallist, unit_con, unit_con2
    i = 0
    j = 0
    for con in contents:
        vallist[i].configure(text=con)
        i = i + 1
    for noc in unit_con:
        unit_con2[j].configure(text=noc)
        j = j + 1


'''
实时时间显示
'''


def gettime():
    # 获取当前时间并转为字符串
    timestr = time.strftime("%H:%M:%S")
    # 重新设置标签文本
    lb.configure(text=timestr)
    # 每隔一秒调用函数gettime自身获取时间
    root.after(1000, gettime)


'''
报警部分
'''


def alarm_loop():
    print(u'当前进程的内存使用：%.4f GB' % (psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024 / 1024))
    info = psutil.virtual_memory()
    print(u'电脑总内存: %.4f GB' % (info.total / 1024 / 1024 / 1024))
    print(u'当前使用的总内存占比： ', info.percent)
    print(u'cpu个数: ', psutil.cpu_count())
    root.after(30000, alarm_logic)


def alarm_logic():
    global alarm_con
    today = datetime.date.today()
    r = []  # 收集所有alarm文件
    sel = []  # 获得符合时间范围的文件
    month = today.month
    last_month = month - 1
    if month < 10:
        month = '0' + str(month)
        last_month = '0' + str(last_month)
    elif month == 10:
        month = str(month)
        last_month = '0' + str(last_month)
    else:
        month = str(month)
        last_month = str(last_month)
    date = today.day
    if date < 10:
        date = '0' + str(date)
    date = str(date)

    cur_str_r = "DeviceAlarm_2021" + month + date + "_"  # 本月记录
    cur_str_l = "DeviceAlarm_2021" + last_month + date + "_"  # 上月记录
    path_list = glob.glob("{}/DeviceAlarm*".format(directory_address))
    for item in path_list:
        r.append(item.split("\\")[-1])
    for path in r:
        if cur_str_l <= path <= cur_str_r:
            sel.append(path)

    # 获取sel中所有报警记录
    alarm_record = []
    alarm_parameter_address_list = [19, 24, 29, 49, 53, 55, 57]
    for file in sel:
        if directory_address.endswith('log'):
            path1 = os.path.join(directory_address, file)
        elif directory_address.endswith('TCPServer'):
            path1 = os.path.join(directory_address, 'log', file)
        with open(path1) as f:
            for line in f:
                line = line.strip('\n')
                if line:
                    # 加工每一行内容，再添加到alarm record中
                    j = 0
                    parameter = []
                    for i in alarm_parameter_address_list:
                        temp = line[j:i]
                        parameter.append(temp)
                        j = i + 1
                    parameter.append(line[line.rfind('#') + 1:])
                    alarm_record.append(parameter)
    alarm_con = alarm_record
    # print(len(alarm_record))

    # show in alarm page， 每次都重新读取所有文件
    num_record = len(alarm_record)
    page = 1
    count = 0

    item_dict = {"1": "压力", "2": "液位", "3": "温度", "4": "流量", "5": "可燃", "6": "有毒", "7": "含氧量"}
    tree_dict = {"1": tree1, "2": tree2, "3": tree3, "4": tree4, "5": tree5, "6": tree6, "7": tree7, "8": tree8,
                 "9": tree9}
    alarm_type_dict = {"1": "高报警", "2": "高高报警", "3": "高高高报警", "0": "低报警"}

    for uu in range(1, 10):
        tree = tree_dict['{}'.format(uu)]
        x = tree.get_children()
        for items in x:
            tree.delete(items)

    while (count < num_record):
        # show
        pick_record = alarm_record[count]

        # c_tree = exec("tree"+str(page))
        try:
            tree_dict["{}".format(page)].insert("", count, text="line" + str(count + 1),
                                                values=(pick_record[-5], '#' + pick_record[-4],
                                                        item_dict["{}".format(pick_record[-3])],
                                                        alarm_type_dict["{}".format(pick_record[-2])],
                                                        pick_record[-1]))
        except AttributeError:
            print("该错误不影响显示\n")

        count += 1
        if count % 10 == 0:
            page += 1

    alarm_loop()


'''
主体框架
'''
# 连接数据库，没有则创建
conn = sqlite3.connect("machine_info.db")
cur = conn.cursor()
# 创建当天对应的数据表，已经有了则忽视
today_time = time.strftime("%Y_%m_%d", time.localtime())

today_sheet = "machine_info" + '_' + today_time
cur.execute(
    "CREATE TABLE IF NOT EXISTS {}(time TEXT PRIMARY KEY NOT NULL,mid TEXT,sensor_info TEXT)".format(today_sheet))
#cur.execute("SELECT * FROM ")
# 添加记录报警的数据库
con_alarm = sqlite3.connect("machine_alarm.db")
cur_a = con_alarm.cursor()
# 创建当天对应的数据表，已经有了则忽视
today_ala_sheet = "machine_alarm" + '_' + today_time
cur_a.execute(
    "CREATE TABLE IF NOT EXISTS {}(hour TEXT, min TEXT, sec TEXT, mid TEXT,sid TEXT, atype TEXT, strength TEXT, a_v, TEXT)".format(today_ala_sheet))

# topFrame
topFrame = Frame(root, bg="orange", relief=SUNKEN)
topFrame.place(x=0, y=0, width=1100, height=60)

# topFrame在root中，topFrame中有 请在下方选择机器号,实时数据,实时时间
# 选择文件夹及路径显示
label_choosefile = Label(topFrame, text='目标路径')
label_choosefile.place(x=5, y=10)
entry_choosefile = Entry(topFrame, textvariable=directory_address_show, state="readonly")
entry_choosefile.place(x=60, y=12, width=300)
b2 = Button(topFrame, text='选择文件夹', command=choose_directory)
b2.place(x=365, y=8)

b1 = Button(topFrame, text="实时数据", font=("Arial Bold", 20))
b1.place(x=450, y=5)

label = Label(topFrame, text="实时时间：", font=("Arial Bold", 20))  # 在哪个frame中，标签内容为
label.place(x=800, y=10)
lb = Label(topFrame, text='', fg='blue', font=("黑体", 20))
lb.place(x=950, y=12)
gettime()

# bottomFrame
bottomFrame = Frame(root, bg="blue")
bottomFrame.place(x=0, y=60, width=1100, height=700)

# 在bottomFrame中创建notebook，多机器选择
major_note = ttk.Notebook(bottomFrame, width=1100, height=700)

# m1对应传感器数据，ma对应报警
m1 = tkinter.Frame()
ma = tkinter.Frame()
major_note.add(m1, text="实时传感器数据")
major_note.add(ma, text="报警记录")
major_note.grid(row=0, column=1, padx=2)

# 往m1中有top与bot两个frame
subTopF = Frame(m1, relief=SUNKEN)  # 宽度， 边框样式
subTopF.place(x=0, y=0, width=1100, height=50)
subBotF = Frame(m1, bg="yellow")
subBotF.place(x=0, y=50, width=1100, height=800)

# m1中bot的内容
# 传感器多页选择，notebook，共四页可以显示130个传感器信息
page_note = ttk.Notebook(subBotF, width=1100, height=700)
m11 = tkinter.Frame()
m12 = tkinter.Frame()
m13 = tkinter.Frame()
m14 = tkinter.Frame()

index_s = ["m3/h", "Pa", "m", "m"]
index_n = ["Pa"] * 126
index = index_s + index_n
num_list = [(str(n).zfill(3) + "#") for n in range(1, 131)]

# 在四页中显示框架
# page 1
for i in range(row_num):
    for j in range(column_num):
        num1 = Label(m11, text=num_list[i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
        num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                   height=num_height)
        value1 = Label(m11, fg="red", bg="yellow",
                       font=("Arial Bold", 20))
        value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                     height=value_height)
        vallist.append(value1)
        unit1 = Label(m11, font=("Arial Bold", 20))
        unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                    width=unit_width, height=unit_height)
        unit_con2.append(unit1)
# page 2
for i in range(row_num):
    for j in range(column_num):
        num1 = Label(m12, text=num_list[36 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
        num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                   height=num_height)
        value1 = Label(m12, fg="red", bg="yellow",
                       font=("Arial Bold", 20))
        value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                     height=value_height)
        vallist.append(value1)
        unit1 = Label(m12, font=("Arial Bold", 20))
        unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                    width=unit_width, height=unit_height)
        unit_con2.append(unit1)
# page 3
for i in range(row_num):
    for j in range(column_num):
        num1 = Label(m13, text=num_list[72 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
        num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                   height=num_height)
        value1 = Label(m13, fg="red", bg="yellow",
                       font=("Arial Bold", 20))
        value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                     height=value_height)
        vallist.append(value1)
        unit1 = Label(m13, font=("Arial Bold", 20))
        unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                    width=unit_width, height=unit_height)
        unit_con2.append(unit1)
# page 4
for i in range(row_num):
    for j in range(column_num):
        if (i * row_num + j) > 21:
            break
        num1 = Label(m14, text=num_list[108 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
        num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                   height=num_height)
        value1 = Label(m14, fg="red", bg="yellow",
                       font=("Arial Bold", 20))
        value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                     height=value_height)
        vallist.append(value1)
        unit1 = Label(m14, font=("Arial Bold", 20))
        unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                    width=unit_width, height=unit_height)
        unit_con2.append(unit1)

# m1中top的内容，实现下拉框
cmb = ttk.Combobox(subTopF)
cmb['value'] = ['选择机器ID']
cmb.current(0)
cmb.place(x=5, y=5)
cmb.bind('<<ComboboxSelected>>', choose_machine)
page_note.add(m11, text="页面1")
page_note.add(m12, text="页面2")
page_note.add(m13, text="页面3")
page_note.add(m14, text="页面4")
page_note.grid(row=0, column=1, padx=2)

# ma 中显示报警记录
ma_subTopF = Frame(ma, relief=SUNKEN)  # 宽度， 边框样式
ma_subTopF.place(x=0, y=0, width=1100, height=50)
ma_subBotF = Frame(ma, bg="yellow")
ma_subBotF.place(x=0, y=50, width=1100, height=800)

# ma中top的内容
ma_label = tkinter.Label(ma_subTopF, text='报警记录', bg='lightblue', fg='red', font=("Arial Bold", 20))
ma_label.place(x=200, y=5)
bm1 = Button(ma_subTopF, text="开启", font=("Arial Bold", 20), command=alarm_logic)
bm1.place(x=700, y=0)

# ma中bot的内容
# 多页选择
page_note = ttk.Notebook(ma_subBotF, width=1100, height=700)
# 创建三个frame，每个对应一个机器中显示的内容
ma1 = tkinter.Frame()
ma2 = tkinter.Frame()
ma3 = tkinter.Frame()
ma4 = tkinter.Frame()
ma5 = tkinter.Frame()
ma6 = tkinter.Frame()
ma7 = tkinter.Frame()
ma8 = tkinter.Frame()
ma9 = tkinter.Frame()

page_note.add(ma1, text="页面1")
page_note.add(ma2, text="页面2")
page_note.add(ma3, text="页面3")
page_note.add(ma4, text="页面4")
page_note.add(ma5, text="页面5")
page_note.add(ma6, text="页面6")
page_note.add(ma7, text="页面7")
page_note.add(ma8, text="页面8")
page_note.add(ma9, text="页面9")

p_dict = {"1": ma1, "2": ma2, "3": ma3, "4": ma4, "5": ma5, "6": ma6, "7": ma7, "8": ma8, "9": ma9}
# 表格
for mm in range(1, 10):
    locals()["tree" + str(mm)] = ttk.Treeview(p_dict["{}".format(mm)])
    locals()["tree" + str(mm)]["columns"] = ("报警时间", "编号", "类型", "等级", "数值")  # #定义列
    locals()["tree" + str(mm)].column("报警时间", width=400)  # #设置列
    locals()["tree" + str(mm)].column("编号", width=100)
    locals()["tree" + str(mm)].column("类型", width=100)
    locals()["tree" + str(mm)].column("等级", width=100)
    locals()["tree" + str(mm)].column("数值", width=100)
    locals()["tree" + str(mm)].heading("报警时间", text="报警时间")  # #设置显示的表头名
    locals()["tree" + str(mm)].heading("编号", text="编号")
    locals()["tree" + str(mm)].heading("类型", text="编号")
    locals()["tree" + str(mm)].heading("等级", text="等级")
    locals()["tree" + str(mm)].heading("数值", text="数值")
    # print(locals()["tree" + str(mm)])
    # print(type(locals()["tree" + str(mm)]))
    locals()["tree" + str(mm)].pack()

page_note.grid(row=0, column=1, padx=2)

# 断网报警页
mh = tkinter.Frame()
major_note.add(mh, text="断网报警")

mh_subTopF = Frame(mh, relief=SUNKEN)  # 宽度， 边框样式
mh_subTopF.place(x=0, y=0, width=1100, height=50)
mh_subBotF = Frame(mh)
mh_subBotF.place(x=0, y=50, width=1100, height=800)
mh_label = tkinter.Label(mh_subTopF, text='心跳断连报警记录', bg='lightblue', fg='red', font=("Arial Bold", 20))
mh_label.place(x=200, y=5)
mh_connect = tkinter.Label(mh_subTopF, text='连接断开中', fg='green', font=("Arial Bold", 20))
mh_connect.place(x=700, y=5)

columns = ("类型", "发生时间", "最近心跳时间")
hb_treeview = ttk.Treeview(mh_subBotF, height=18, show="headings", columns=columns)  # 表格

hb_treeview.column("类型", width=200, anchor='center')  # 表示列,不显示
hb_treeview.column("发生时间", width=500, anchor='center')  # 表示列,不显示
hb_treeview.column("最近心跳时间", width=500, anchor='center')

hb_treeview.heading("类型", text="类型")
hb_treeview.heading("发生时间", text="发生时间")  # 显示表头
hb_treeview.heading("最近心跳时间", text="最近心跳时间")

hb_treeview.pack(fill=BOTH)

heart_loop()


#数据库交互
mj = tkinter.Frame()
major_note.add(mj, text="过往数据查询")
mj_subTopF = Frame(mj, relief=SUNKEN)  # 宽度， 边框样式
mj_subTopF.place(x=0, y=0, width=1100, height=25)
mj_subBotF = Frame(mj)
mj_subBotF.place(x=0, y=25, width=1100, height=800)

page_choose = ttk.Notebook(mj_subBotF, width=1100, height=800)
mj1 = tkinter.Frame()
mj2 = Frame()
mj3 = Frame()
page_choose.add(mj1, text="传感器参数")
page_choose.add(mj2, text="报警信息记录")
page_choose.add(mj3, text="心跳报警记录")
page_choose.grid(row=0, column=1, padx=2)

def sensor_query():
    global info_name, sensor_query_id
    sh, sm, ss = start_h.get(), start_m.get(), start_s.get()
    start_time = sh + ':' + sm + ':' + ss
    eh, em, es = end_h.get(), end_m.get(), end_s.get()
    end_time = eh + ':' + em + ':' + es
    child_si = si_treeview.get_children()
    for item in child_si:
        si_treeview.delete(item)
    if start_time == '00:00:00' and end_time == '24:00:00':
        if sensor_query_id == '所有机器':
            info_sensor = cur.execute("SELECT * FROM {}".format(info_name))
            for it in info_sensor:
                si_treeview.insert('', 'end', values=it)
        else:
            info_sensor = cur.execute("SELECT * FROM {} WHERE mid == {}".format(info_name, sensor_query_id))
            for it in info_sensor:
                si_treeview.insert('', 'end', values=it)
    else:
        if sensor_query_id == '所有机器':
            info_sensor = cur.execute("SELECT * FROM {} WHERE time >= '{}' and time < '{}'".format(info_name, start_time, end_time))
            for it in info_sensor:
                si_treeview.insert('', 'end', values=it)
        else:
            info_sensor = cur.execute("SELECT * FROM {} WHERE mid == {} and time >= '{}' and time < '{}'".format(info_name, sensor_query_id, start_time, end_time))
            for it in info_sensor:
                si_treeview.insert('', 'end', values=it)

#传感器
#日期选择
date_choose_str1 = StringVar()
dateshow_1 = ttk.Entry(mj1, textvariable=date_choose_str1)
dateshow_1.place(x=68, y=8)
tkinter.Button(mj1, text='日期选择', command=date_str_gain).place(x=5, y=5, width=60)
#时间区间选择
def reset_time():
    start_h.delete(0, END)
    start_h.insert(0, '00')
    start_m.delete(0, END)
    start_m.insert(0, "00")
    start_s.delete(0, END)
    start_s.insert(0, "00")
    end_h.delete(0, END)
    end_h.insert(0, "24")
    end_m.delete(0, END)
    end_m.insert(0, "00")
    end_s.delete(0, END)
    end_s.insert(0, "00")
sensor_time_frame = tkinter.Frame(mj1)
sensor_time_frame.place(x=500, y=8)
sensor_time_label = Label(sensor_time_frame, text='时间区间选择')
sensor_time_label.grid(row=0, column=0)
start_h = Entry(sensor_time_frame, width=3)
start_h.insert(0, "00")
start_h.grid(row=0, column=1)
Label(sensor_time_frame, text=':').grid(row=0, column=2)
start_m = Entry(sensor_time_frame, width=3)
start_m.insert(0, "00")
start_m.grid(row=0, column=3)
Label(sensor_time_frame, text=':').grid(row=0, column=4)
start_s = Entry(sensor_time_frame, width=3)
start_s.insert(0, "00")
start_s.grid(row=0, column=5)
Label(sensor_time_frame, text='至', width=4).grid(row=0, column=6)
end_h = Entry(sensor_time_frame, width=3)
end_h.insert(0, "24")
end_h.grid(row=0, column=7)
Label(sensor_time_frame, text=':').grid(row=0, column=8)
end_m = Entry(sensor_time_frame, width=3)
end_m.insert(0, "00")
end_m.grid(row=0, column=9)
Label(sensor_time_frame, text=':').grid(row=0, column=10)
end_s = Entry(sensor_time_frame, width=3)
end_s.insert(0, "00")
end_s.grid(row=0, column=11)
tkinter.Button(sensor_time_frame, text='重置回所有时间段', command=reset_time).grid(row=0, column=12, padx=10)


#编号选择
def choose_sensor_id(event):
    global sensor_query_id
    sensor_query_id = sensor_id_choose.get()
sensor_id_choose = ttk.Combobox(mj1)
sensor_id_choose['value'] = ['所有机器']
sensor_id_choose.current(0)
sensor_id_choose.place(x=300, y=8)
sensor_id_choose.bind('<<ComboboxSelected>>', choose_sensor_id)

#查询按钮
tkinter.Button(mj1, text='查询', command=sensor_query, bd=8, fg='red').place(x=950, y=2, width=80)

tree_frame1 = Frame(mj1)
tree_frame1.place(x=0, y=50, width=1100, height=700)
columns = ("时间", "编号", "参数")
si_treeview = ttk.Treeview(tree_frame1, height=18, show="headings", columns=columns)  # 表格

si_treeview.column("时间", width=200, anchor='center')
si_treeview.column("编号", width=200, anchor='center')  #
si_treeview.column("参数", width=680, anchor='center')

si_treeview.heading("时间", text="时间")
si_treeview.heading("编号", text="编号")
si_treeview.heading("参数", text="参数")

si_treeview.pack()

#双击展开
def show_in_new_page(event):
    global num_width, num_height, x_pad, y_pad
    contents_choose = ''
    for item in si_treeview.selection():
        item_text = si_treeview.item(item, 'values')
        contents_choose = item_text[2]
    contents_choose_list = []
    for i in contents_choose.split(','):
        contents_choose_list.append(i.split(':')[1][2:-1])
    child_top = Toplevel(width=1100, height=500)
    #child_top.withdraw()
    page_note_child = ttk.Notebook(child_top, width=1100, height=500)
    c11 = tkinter.Frame(child_top)
    c12 = tkinter.Frame(child_top)
    c13 = tkinter.Frame(child_top)
    c14 = tkinter.Frame(child_top)
    index_s = ["m3/h", "Pa", "m", "m"]
    index_n = ["Pa"] * 126
    index = index_s + index_n
    num_list = [(str(n).zfill(3) + "#") for n in range(1, 131)]
    for i in range(row_num):
        for j in range(column_num):
            num1 = Label(c11, text=num_list[i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(c11, fg="red", bg="yellow", text=contents_choose_list[i * column_num + j],
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=num_width,
                         height=value_height)
            vallist.append(value1)

    # page 2
    for i in range(row_num):
        for j in range(column_num):
            num1 = Label(c12, text=num_list[36 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(c12, fg="red", bg="yellow", text=contents_choose_list[36+i * column_num + j],
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=num_width,
                         height=value_height)
            vallist.append(value1)

    # page 3
    for i in range(row_num):
        for j in range(column_num):
            num1 = Label(c13, text=num_list[72 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(c13, fg="red", bg="yellow", text=contents_choose_list[72+i * column_num + j],
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=num_width,
                         height=value_height)
            vallist.append(value1)

    # page 4
    for i in range(row_num):
        for j in range(column_num):
            if (i * row_num + j) > 21:
                break
            num1 = Label(c14, text=num_list[108 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(c14, fg="red", bg="yellow", text=contents_choose_list[108+i * column_num + j],
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=num_width,
                         height=value_height)
            vallist.append(value1)

    page_note_child.add(c11, text="页面1")
    page_note_child.add(c12, text="页面2")
    page_note_child.add(c13, text="页面3")
    page_note_child.add(c14, text="页面4")
    page_note_child.pack()
si_treeview.bind('<Double-1>',show_in_new_page)


mainloop()
