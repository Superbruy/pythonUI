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
connect = False  #是否连接的状态
lasttime = ()    #上次接受的心跳包的时间

def heart_loop():
    heartbeat()
    detect_heartbeat()
    root.after(2000,heart_loop)

def detect_heartbeat():
    global heartbeat_time, connect, lasttime
    nowtime = time.localtime(time.time())
    pretime = heartbeat_time[0]
    pretime_num = datetime.datetime(pretime[0], pretime[1], pretime[2], pretime[3], pretime[4], pretime[5])
    nowtime_num = datetime.datetime(nowtime[0], nowtime[1], nowtime[2], nowtime[3], nowtime[4], nowtime[5])
    timedif = (nowtime_num - pretime_num).total_seconds()
    nowtime_str = time.strftime("%Y-%m-%d %H:%M:%S", nowtime)
    pretime_str = time.strftime("%Y-%m-%d %H:%M:%S", pretime)
    if connect == False and timedif < 70 and pretime != lasttime:
        connect = True
        hb_treeview.insert('','end', values=('连接',nowtime_str, pretime_str))
        mh_connect.configure(text='心跳包正常接收中')
        lasttime = pretime
    elif connect == True and timedif > 62 :
        hb_treeview.insert('', 'end', values=('断开',nowtime_str, pretime_str))
        connect = False
        lasttime = pretime
        mh_connect.configure(text='连接已断开')

def heartbeat():
    global heartbeat_time, connect
    sstr = "TCPServer"
    heart_file_list = glob.glob("./{}/log/heartbeat*".format(sstr))
    sort_heart = sorted(heart_file_list, key=lambda x: os.path.getmtime(x))  # Sort by time of most recent modification
    latest_heart_path = sort_heart[-1]  # list member: path
    #temp_list = get_latest_lines(latest_heart_path)
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
            # hadtime = datetime.datetime(hadtime[0], hadtime[1], hadtime[2], hadtime[3], hadtime[4], hadtime[5])
            # nowtime = datetime.datetime(nowtime[0], nowtime[1], nowtime[2], nowtime[3], nowtime[4], nowtime[5])
            # timedif = (nowtime - hadtime).seconds
            # if timedif > 120:
            #     connect = False
            # else:
            #     connect = True
    except EXCEPTION:
        print("read file error\n")




def update_cmblist():  # 更新下拉菜单机器号
    cmb_value = []
    for ckey in sorted(contents_list):
        cmb_value.append(ckey)
    cmb['value'] = cmb_value


def update_contents():  # 更新参数
    global contents, contents_list, machine_ID, unit_list, unit_con
    contents = contents_list[machine_ID]
    unit_con = unit_list[machine_ID]
    change_show()


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


def get_realtime_data(num):  # 读取最近的num个文件的数据并更新全局字典
    global file_num, contents_list
    # 得到最后一个文件的最后一行
    sstr = "TCPServer"
    dd_file_list = glob.glob("./{}/log/DeviceData*".format(sstr))
    sort_dd = sorted(dd_file_list, key=lambda x: os.path.getmtime(x))  # Sort by time of most recent modification
    latest_dd_path = sort_dd[-num:]  # list member: path
    get_latest_lines(latest_dd_path)


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
            return cou-1


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


def gettime():
    # 获取当前时间并转为字符串
    timestr = time.strftime("%H:%M:%S")
    # 重新设置标签文本
    lb.configure(text=timestr)
    # 每隔一秒调用函数gettime自身获取时间
    root.after(1000, gettime)


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

    # print(cur_str)
    path_list = glob.glob("./TCPServer/log/DeviceAlarm*")
    for item in path_list:
        r.append(item.split("\\")[1])
    for path in r:
        if cur_str_l <= path <= cur_str_r:
            sel.append(path)

    # 获取sel中所有报警记录
    alarm_record = []
    alarm_parameter_address_list = [19, 24, 29, 49, 53, 55, 57]
    for file in sel:
        path1 = "./TCPServer/log/" + file
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


def get_last_line(path):
    '''
    得到最后一行的内容
    :param path:
    :return:
    '''
    c = []
    try:
        with open(path) as f:
            for line in f:
                if line.startswith("2021"):
                    line = line.rstrip("\n")
                    c.append(line)
            need = c[-1]
            pre, mid, rear = need.split('\t')
            lists = rear.split('#')
            for i, item in enumerate(lists):
                if item.endswith("Pa"):
                    lists[i] = item.rstrip("Pa")
                elif item.endswith("m3/h"):
                    lists[i] = item.rstrip("m3/h")
                else:
                    lists[i] = item.rstrip("m")
            return lists
    except EXCEPTION:
        print("read file error\n")


def loop():
    get_realtime_data(3)
    update_contents()
    update_cmblist()
    root.after(10000, loop)


# 暂时不用
def show():
    global file_num, contents
    # 得到最后一个文件的最后一行
    sstr = "TCPServer"
    dd_file_list = glob.glob("./{}/log/DeviceData*".format(sstr))
    sort_dd = sorted(dd_file_list, key=lambda x: os.path.getmtime(x))  # Sort by time of most recent modification
    latest_dd_path = sort_dd[-1]  # list member: path
    temp = get_last_line(latest_dd_path)
    contents = temp[1:]

    # 以下四行测试在不同分页上是否显示正常
    # label = tkinter.Label(m11, text='开始接收端口数据', bg='lightblue', fg='red')
    # label.place(x=100, y=100)
    # label = tkinter.Label(m12, text='ddd', bg='lightblue', fg='red')
    # label.place(x=100, y=100)

    # 在不同页面上显示所有的号码，一个页面显示35个
    index_s = ["m3/h", "Pa", "m", "m"]
    index_n = ["Pa"] * 126
    index = index_s + index_n
    num_list = [(str(n).zfill(3) + "#") for n in range(1, 131)]
    # page 1
    for i in range(row_num):
        for j in range(column_num):
            num1 = Label(m11, text=num_list[i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(m11, text=contents[i * column_num + j], fg="red", bg="yellow",
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                         height=value_height)
            unit1 = Label(m11, text="{}".format(index[i * column_num + j]), font=("Arial Bold", 20))
            unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                        width=unit_width, height=unit_height)
    # page 2
    for i in range(row_num):
        for j in range(column_num):
            num1 = Label(m12, text=num_list[36 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(m12, text=contents[36 + i * column_num + j], fg="red", bg="yellow",
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                         height=value_height)
            unit1 = Label(m12, text="{}".format(index[36 + i * column_num + j]), font=("Arial Bold", 20))
            unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                        width=unit_width, height=unit_height)
    # page 3
    for i in range(row_num):
        for j in range(column_num):
            num1 = Label(m13, text=num_list[72 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(m13, text=contents[72 + i * column_num + j], fg="red", bg="yellow",
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                         height=value_height)
            unit1 = Label(m13, text="{}".format(index[72 + i * column_num + j]), font=("Arial Bold", 20))
            unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                        width=unit_width, height=unit_height)
    # page 4
    for i in range(row_num):
        for j in range(column_num):
            if (i * row_num + j) > 21:
                break
            num1 = Label(m14, text=num_list[108 + i * column_num + j], fg="green", bg="pink", font=("Arial Bold", 20))
            num1.place(x=(num_width + x_pad) * j + 20, y=20 + (num_height + value_height) * i, width=num_width,
                       height=num_height)
            value1 = Label(m14, text=contents[108 + i * column_num + j], fg="red", bg="yellow",
                           font=("Arial Bold", 20))
            value1.place(x=(num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i, width=value_width,
                         height=value_height)
            unit1 = Label(m14, text="{}".format(index[108 + i * column_num + j]), font=("Arial Bold", 20))
            unit1.place(x=value_width + (num_width + x_pad) * j + 20, y=60 + (num_height + value_height) * i,
                        width=unit_width, height=unit_height)
    loop()


# topFrame
topFrame = Frame(root, bg="orange", relief=SUNKEN)
topFrame.place(x=0, y=0, width=1100, height=60)

# topFrame在root中，topFrame中有 请在下方选择机器号,实时数据,实时时间
label = Label(topFrame, text="请在下方选择机器号", font=("Arial Bold", 20))
label.place(x=10, y=10)

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
get_realtime_data(10)
cmb_value = []  # 下拉框所有选项
for ckey in sorted(contents_list):
    cmb_value.append(ckey)
cmb['value'] = cmb_value
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






mainloop()
