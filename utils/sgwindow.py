import PySimpleGUI as sg
import os
import time


def input_messages():
    flyDate = format(time.strftime("%Y-%m-%d", time.localtime()))
    errmsg = ''
    while True:
        layout = [[sg.Text('飞行账户', justification='right'),
                   sg.In(key='user')],
                  [sg.Text('航线日期', justification='right'),
                   sg.In(flyDate, key="Date"),
                   sg.CalendarButton(button_text="选择日期", size=(15, 1), target='Date', format='%Y-%m-%d')],
                  [sg.Text('照片路径', justification='right'),
                   sg.In(errmsg, key='Folder'),
                   sg.FolderBrowse('选择文件夹', size=(15, 1), target='Folder')],
                  [sg.Button("开始上传"), sg.Cancel("退出")], ]

        window = sg.Window('Test', layout, font=("宋体", "15"), default_element_size=(50, 5))

        event, values = window.read()

        if event in (None, '退出'):  # 如果用户关闭窗口或点击`Cancel`
            exit()
        if event != '开始上传':  # 如果用户关闭窗口或点击`Cancel`
            exit()

        flyUser = values['user']
        flyDate = values['Date']
        photoFolder = values['Folder']

        try:
            assert os.path.isdir(photoFolder), "文件夹不能为空"
            break
        except AssertionError:
            errmsg = "请选择文件夹"
            print(errmsg)

    window.close()

    print('User:', flyUser)
    print('Date:', flyDate)
    print('Folder:', photoFolder)

    return flyUser, flyDate, photoFolder


def up_status(Tcount, vfImgCnt, validImgCnt, invalidImgCnt, repeatCnt):
    sg.one_line_progress_meter('上传进度',  # 窗口名称
                               vfImgCnt,  # 当前进度
                               Tcount,  # 总进度
                               f"关联成功:{validImgCnt} 无效照片:{invalidImgCnt} 重复照片:{repeatCnt}",
                               orientation='h',  # 进度条方向h是横向，v是纵向
                               bar_color=('#AAFFAA', '#FFAAFF'),  # 进度条颜色
                               # size=(30, 30),
                               # keep_on_top=True,
                               no_titlebar=True,
                               no_button=True
                               )
