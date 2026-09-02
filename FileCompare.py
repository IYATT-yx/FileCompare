"""
file: FileCompare.py
description: 文件一致性比对工具
author: IYATT-yx
copyright:   Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""
from buildtime import buildTime

import os
import hashlib
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

dragDropAvailable = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    baseTk = TkinterDnD.Tk
    dragDropAvailable = True
except ImportError:
    baseTk = tk.Tk

class FileCompareApp(baseTk):
    def __init__(self):
        super().__init__()

        self.title(f'文件一致性比对工具 by IYATT-yx {buildTime}')
        self.geometry('780x560')
        self.resizable(True, True)
        iconPath = os.path.join(os.path.dirname(__file__), 'icon.ico')            
        self.iconbitmap(iconPath)

        # 默认启用窗口置顶，方便从文件夹拖拽文件
        self.isTopmost = tk.BooleanVar(value=True)
        self.attributes('-topmost', True)

        self._initUi()

    def _initUi(self):
        # 顶部说明与置顶控制区
        topFrame = ttk.Frame(self, padding=10)
        topFrame.pack(fill=tk.X)

        titleLabel = ttk.Label(
            topFrame,
            text='文件二进制内容比对器',
            font=('Microsoft YaHei UI', 14, 'bold')
        )
        titleLabel.pack(side=tk.LEFT, anchor=tk.W)

        # 置顶开关（位置：右上角）
        chkTopmost = ttk.Checkbutton(
            topFrame,
            text='📌 窗口置顶',
            variable=self.isTopmost,
            command=self._toggleTopmost
        )
        chkTopmost.pack(side=tk.RIGHT, anchor=tk.E, padx=(0, 5))

        descText = (
            '仅基于文件字节大小与 SHA-256 哈希值比对文件差异、'
            '\n支持文件选择与文件资源管理器直接拖入。'
        )
        descLabel = ttk.Label(
            self,
            text=descText,
            foreground='#555555',
            font=('Microsoft YaHei UI', 9),
            padding=(10, 0, 10, 5)
        )
        descLabel.pack(anchor=tk.W)

        # 文件选择区域
        filesFrame = ttk.LabelFrame(self, text=' 比对目标文件 ', padding=15)
        filesFrame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)

        # 文件 A
        lblA = ttk.Label(filesFrame, text='文件 A:', font=('Microsoft YaHei UI', 10))
        lblA.grid(row=0, column=0, sticky=tk.NW, pady=5)

        self.txtFile1 = tk.Text(filesFrame, height=2.5, width=65, font=('Consolas', 9), wrap=tk.CHAR)
        self.txtFile1.grid(row=0, column=1, padx=8, pady=5, sticky=tk.EW)

        btnBrowse1 = ttk.Button(filesFrame, text='浏览...', command=lambda: self._selectFile(1))
        btnBrowse1.grid(row=0, column=2, sticky=tk.NW, pady=5)

        # 文件 B
        lblB = ttk.Label(filesFrame, text='文件 B:', font=('Microsoft YaHei UI', 10))
        lblB.grid(row=1, column=0, sticky=tk.NW, pady=5)

        self.txtFile2 = tk.Text(filesFrame, height=2.5, width=65, font=('Consolas', 9), wrap=tk.CHAR)
        self.txtFile2.grid(row=1, column=1, padx=8, pady=5, sticky=tk.EW)

        btnBrowse2 = ttk.Button(filesFrame, text='浏览...', command=lambda: self._selectFile(2))
        btnBrowse2.grid(row=1, column=2, sticky=tk.NW, pady=5)

        filesFrame.columnconfigure(1, weight=1)

        # 绑定拖拽事件 (若库可用)
        if dragDropAvailable:
            self.txtFile1.drop_target_register(DND_FILES)
            self.txtFile1.dnd_bind('<<Drop>>', lambda e: self._onDrop(e, 1))
            self.txtFile2.drop_target_register(DND_FILES)
            self.txtFile2.dnd_bind('<<Drop>>', lambda e: self._onDrop(e, 2))
            
            hintLbl = ttk.Label(
                filesFrame, 
                text='[提示] 窗口已置顶，可直接从资源管理器拖拽文件至上方多行文本框中', 
                foreground='#008000', 
                font=('Microsoft YaHei UI', 8)
            )
            hintLbl.grid(row=2, column=1, sticky=tk.W, pady=(2, 0))
        else:
            hintLbl = ttk.Label(
                filesFrame, 
                text='[提示] 如需支持拖拽功能，请先运行: pip install tkinterdnd2', 
                foreground='#888888', 
                font=('Microsoft YaHei UI', 8)
            )
            hintLbl.grid(row=2, column=1, sticky=tk.W, pady=(2, 0))

        # 操作与进度区
        actionFrame = ttk.Frame(self, padding=10)
        actionFrame.pack(fill=tk.X)

        self.btnCompare = ttk.Button(
            actionFrame, 
            text='开始比对', 
            command=self._startCompareThread
        )
        self.btnCompare.pack(side=tk.LEFT, padx=(5, 15))

        self.progress = ttk.Progressbar(actionFrame, mode='indeterminate', length=400)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 结果显示区
        resultFrame = ttk.LabelFrame(self, text=' 比对结果 ', padding=10)
        resultFrame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        self.lblResult = tk.Label(
            resultFrame, 
            text='等待比对...', 
            font=('Microsoft YaHei UI', 12, 'bold'), 
            fg='#666666',
            anchor='w'
        )
        self.lblResult.pack(fill=tk.X, pady=(0, 5))

        self.txtDetails = tk.Text(resultFrame, height=5, font=('Consolas', 9), state=tk.DISABLED, bg='#F8F9FA')
        self.txtDetails.pack(fill=tk.BOTH, expand=True)

    def _toggleTopmost(self):
        '''动态切换窗口置顶状态'''
        self.attributes('-topmost', self.isTopmost.get())

    def _setTextPath(self, widget, path):
        widget.delete('1.0', tk.END)
        widget.insert('1.0', path)

    def _getTextPath(self, widget):
        return widget.get('1.0', tk.END).strip().strip("'").strip('"')

    def _selectFile(self, fileIdx):
        path = filedialog.askopenfilename(
            title=f'选择文件 {fileIdx}',
            filetypes=[('所有文件', '*.*'), ('PDF 文件', '*.pdf'), ('3D 模型文件', '*.step;*.stp')]
        )
        if path:
            path = os.path.normpath(path)
            if fileIdx == 1:
                self._setTextPath(self.txtFile1, path)
            else:
                self._setTextPath(self.txtFile2, path)

    def _onDrop(self, event, fileIdx):
        path = event.data.strip('{}')  # 处理路径中的空格与花括号
        path = os.path.normpath(path)
        if fileIdx == 1:
            self._setTextPath(self.txtFile1, path)
        else:
            self._setTextPath(self.txtFile2, path)

    def _setDetails(self, text):
        self.txtDetails.config(state=tk.NORMAL)
        self.txtDetails.delete('1.0', tk.END)
        self.txtDetails.insert(tk.END, text)
        self.txtDetails.config(state=tk.DISABLED)

    def _startCompareThread(self):
        f1 = self._getTextPath(self.txtFile1)
        f2 = self._getTextPath(self.txtFile2)

        if not f1 or not f2:
            messagebox.showwarning('警告', '请先选择需要比对的两个文件！')
            return

        if not os.path.exists(f1) or not os.path.exists(f2):
            messagebox.showerror('错误', '指定的文件路径不存在，请检查！')
            return

        self.btnCompare.config(state=tk.DISABLED)
        self.progress.start(10)
        self.lblResult.config(text='比对中，请稍候...', fg='#0066CC')
        self._setDetails('正在校验文件大小与计算 SHA-256 哈希值...\n')

        # 使用多线程避免 GUI 界面假死
        threading.Thread(target=self._runCompare, args=(f1, f2), daemon=True).start()

    def _runCompare(self, f1, f2):
        try:
            size1 = os.path.getsize(f1)
            size2 = os.path.getsize(f2)

            detailMsg = f'文件 A 大小: {size1:,} 字节\n文件 B 大小: {size2:,} 字节\n\n'

            # 1. 快速大小比对
            if size1 != size2:
                self.after(0, self._updateResult, False, '文件大小不一致（内容必然不同）', detailMsg)
                return

            # 2. 计算 SHA-256
            sha1 = self._calcSha256(f1)
            sha2 = self._calcSha256(f2)

            detailMsg += f'文件 A SHA-256: {sha1}\n文件 B SHA-256: {sha2}\n'

            if sha1 == sha2:
                self.after(0, self._updateResult, True, '两份文件二进制内容完全一致！', detailMsg)
            else:
                self.after(0, self._updateResult, False, '文件大小相同，但二进制数据不同！', detailMsg)

        except Exception as e:
            self.after(0, self._updateResult, None, f'比对出现异常: {e}', '')

    def _calcSha256(self, path):
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192 * 1024):  # 8MB 缓存读取
                sha256.update(chunk)
        return sha256.hexdigest()

    def _updateResult(self, isSame, title, details):
        self.progress.stop()
        self.btnCompare.config(state=tk.NORMAL)

        if isSame is True:
            self.lblResult.config(text=f'[✓] {title}', fg='#008800')
        elif isSame is False:
            self.lblResult.config(text=f'[X] {title}', fg='#CC0000')
        else:
            self.lblResult.config(text=f'[!] {title}', fg='#FF8800')

        self._setDetails(details)

if __name__ == '__main__':
    app = FileCompareApp()
    app.mainloop()