# coding: utf-8

import os

from wxkit import wx, ui, trace, memo

basic_menu_items = [
  ['file;File',
   'new;&New;Ctrl+N',
   'open;&Open ..;Ctrl+O',
   'save;&Save ..;Ctrl+S',
   'folder;&Folder ..',
   '-'
   'tab;&New &Tab;Ctrl+T',
   'close;&Close',
   '-'
   'about;&About',
  ],
  ['dialogs;&Dialogs',
   'info-msg;&Infomation ..',
   'warn-msg;&Warning ..',
   'error-msg;&Error ..',
   '-',
   'yes-no;&Yes or No ..',
   'ok-cancel;&OK or Cancel ..',
   'retry-cancel;&Retry or Cancel ..',
   'abort-retry-ignore;&Abort Retry Ignore ..',
   'input-text;&Input Text ..',
   '-',
   'color;&Color ..',
   'find;&Find ..',
  ]
]

class BasicWX(ui.App):

  @property
  def folder(self):
    fld = self.folder_ent.GetValue().strip()
    if fld == '': fld = os.getcwd()
    return fld

  @folder.setter
  def folder(self, fld):
      self.folder_ent.SetValue(fld)

  @property
  def foreground(self):
    cname = self.foreground_ent.GetValue().strip()
    if cname == '': cname = 'black'
    colour = wx.TheColourDatabase.find(cname)
    return colour

  @foreground.setter
  def foreground(self, colour):
    if type(colour) == str: self.foreground_ent.SetValue(colour); return
    cname = wx.TheColourDatabase.FindName(colour)
    if cname == '': cname = colour.GetAsString(flag=wx.Colour.C2S_HTML_SYNTAX)
    self.foreground_ent.SetValue(cname)

  def perform(self, cmd, event):
    if ui.debug: trace('basic cmd:',cmd,'event:',event)
    cc = self.cc

    if 'ent-input' == cmd:
      ent = self.ent
      cap = self.caption
      value = ent.GetValue()
      cap.SetValue('%s <- input data.' % value)
      return
        
    if 'ent-choise' == cmd:
      # コンボボックスでEnterが押された
      cb = self.combo
      append_combo_entry(cb, cb.GetValue())
      return
        
    elif 'open' == cmd:
      val = self.multiple.IsChecked()
      tt = cc.ask_open_file(multiple=val, initialdir=self.folder)
      if not tt: return
      trace('open file', tt)
            
    elif 'save' == cmd:
      val = self.multiple.IsChecked()
      tt = cc.ask_save_file(initialdir=self.folder)
      if not tt: return
      trace('save target file', tt)

    elif 'folder' == cmd:
      tt = cc.ask_folder(initialdir=self.folder)
      if not tt: return
      trace('target folder', tt)
      self.folder = tt

    elif 'info-msg' == cmd:
      cc.show_info(u'情報メッセージ表示')

    elif 'warn-msg' == cmd:
      cc.show_warning(u'警告メッセージ表示')

    elif 'error-msg' == cmd:
      cc.show_error(u'エラー・メッセージ表示')

    elif 'yes-no' == cmd:
      rc = cc.ask_yes_no(u'処理を継続しますか？')
      cc.status_text = '%s selected.' % rc

    elif 'ok-cancel' == cmd:
      rc = cc.ask_ok_cancel(u'処理を継続しますか？')
      cc.status_text = '%s selected.' % rc

    elif 'retry-cancel' == cmd:
      rc = cc.ask_retry_cacnel(u'処理が継続できません')
      cc.status_text = '%s selected.' % rc

    elif 'abort-retry-ignore' == cmd:
      rc = cc.ask_abort_retry_ignore(u'処理が継続できません')
      cc.status_text = '%s selected.' % rc

    elif 'input-text' == cmd:
      text = cc.input_text(u'テキストを入力ください')
      cc.status_text = 'input text: %s' % text

    elif 'find' == cmd:
      self.find_dialog.open()
      
    elif 'close' == cmd:
      cc.dispose(); return

    elif 'quit' == cmd:
      wx.Exit(); return

    elif 'new' == cmd:
      self.__class__().start()
      return

    elif 'about' == cmd:
      cc.show_info('\n'.join((
          'Python version: ' + sys.version,
          'plastform: ' + sys.platform,
          'wwPython: ' + wx.version(), '', sys.copyright, '',
          'home: ' + os.path.expanduser('~'))), 'about')
      return

  _perform = ui.alert(perform)

  @property
  def find_dialog(self):
    if hasattr(self, '_find_dialog'): return self._find_dialog
    self._find_dialog = dig = self.cc.create_dialog(memo.SearchDialog)
    return dig
  
  def create_menubar(self):
    cc = self.cc
    bar = wx.MenuBar()
    for mn in 'file:dialogs'.split(':'):
      menu = cc.find_menu(mn, basic_menu_items)
      bar.Append(menu, menu.hint[1])
    return bar
        
  def create_widgets(self, base):
    cc = self.cc
    vbox = wx.BoxSizer(wx.VERTICAL)
    panel = wx.Panel(base)
    panel.SetSizer(vbox)
    
    note = wx.Notebook(panel)
    vbox.Add(note, flag=wx.EXPAND, proportion=1) # フレームの大きさ変更に追随する
            
    p1 = self._create_basic_panel(note)
    note.AddPage(p1, 'basic')

    p1 = self._create_dialog_panel(note)
    note.AddPage(p1, 'dialog')

    buf = wx.TextCtrl(note, style=wx.TE_MULTILINE)
    size = ui.text_size(buf, rows=20, cols=50)
    buf.SetSize(size)
    note.AddPage(buf, 'text')
    note.Refresh()
        
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    btn = wx.Button(panel, label='Close')
    cc.Bind(wx.EVT_BUTTON, lambda ev, cmd='close': self._perform(cmd, ev), btn)
    hbox.Add(btn, flag=wx.SHAPED|wx.ALIGN_CENTER)
    vbox.Add(hbox, flag=wx.ALL, border=3)
    base.SetSize(size)


    #self.model = _LocalMemo()
        
  def _create_dialog_panel(self, base):
    cc = self.cc

    vbox = wx.BoxSizer(wx.VERTICAL)
    panel = wx.Panel(base)
    panel.SetSizer(vbox)

    def add_button(caption, hbox):
      cmd, caption = caption.split(';')
      btn = wx.Button(panel, label=caption)
      cc.Bind(wx.EVT_BUTTON, lambda ev, cmd=cmd: self._perform(cmd, ev), btn)
      hbox.Add(btn, flag=wx.LEFT|wx.BOTTOM, border=5)

    # -----------
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    add_button('open;Open', hbox)
    cb = wx.CheckBox(panel, label='Multiple')
    hbox.Add(cb, flag=wx.LEFT, border=5)
    add_button('save;Save', hbox)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)
    self.multiple = cb

    # ----------- フォルダの選択
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Folder:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)

    ent = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
    ent.SetValue(os.getcwd())
    self.folder_ent = ent
    cc.Bind(wx.EVT_TEXT_ENTER, lambda ev, cmd='folder': self._perform(cmd, ev), ent)
    hbox.Add(ent, proportion=1)
    add_button('folder;Folder ..', hbox)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)
    
    # -----------
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    add_button('info-msg;Information', hbox)
    add_button('warn-msg;Warning', hbox)
    add_button('error-msg;Error', hbox)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    add_button('yes-no;Yes or No', hbox)
    add_button('ok-cancel;Okay or Cancel', hbox)
    add_button('retry-cancel;Retry or Cancel', hbox)
    add_button('abort-retry-ignore;Abort Retry Ignore', hbox)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    add_button('input-text;Input Text', hbox)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Foreground:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)

    ent = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
    ent.SetValue('aaa')
    self.foreground = ent
    cc.Bind(wx.EVT_TEXT_ENTER, lambda ev, cmd='foreground': self._perform(cmd, ev), ent)
    hbox.Add(ent, proportion=1)
    add_button('foreground; Color Choise..', hbox)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    return panel




  def _create_basic_panel(self, base):
    cc = self.cc
        
    vbox = wx.BoxSizer(wx.VERTICAL)
    panel = wx.Panel(base)
    panel.SetSizer(vbox)

    # ----------- テキストをコピーできる読み込み専用テキスト
    ent = wx.TextCtrl(panel, value='No Editable Text', style=wx.TE_READONLY|wx.BORDER_NONE)
    ent.SetBackgroundColour(base.GetBackgroundColour())
    self.caption = ent
    vbox.Add(ent, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------　１行入力テキスト (ENTERでイベントに反応する)
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Input:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)

    ent = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
    ent.SetValue('aaa')
    self.ent = ent
    cc.Bind(wx.EVT_TEXT_ENTER, lambda ev, cmd='ent-input': self._perform(cmd, ev), ent)
    hbox.Add(ent, proportion=1)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------　パスワード入力
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Password:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)

    ent = wx.TextCtrl(panel, style=wx.TE_PASSWORD)
    ent.SetValue('bbb')
    hbox.Add(ent, proportion=1)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------　選択候補をもつテキスト入力
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Combobox:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)
        
    ent = wx.ComboBox(panel, style=wx.TE_PROCESS_ENTER)
    self.combo = ent
    ent.SetValue('ccc')
    choise = ( 'xx', 'yy', 'zz' )
    for tt in choise: ent.Append(tt)
    cc.Bind(wx.EVT_TEXT_ENTER, lambda ev, cmd='cb-choise': self._perform(cmd, ev), ent)
    hbox.Add(ent, proportion=1)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    btn = wx.Button(panel, label='Ok')
    cc.Bind(wx.EVT_BUTTON, lambda ev, cmd='ok': self._perform(cmd, ev), btn)
    hbox.Add(btn, flag=wx.LEFT, border=5)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # -----------　複数行入力テキスト
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Text')
    hbox.Add(cap, flag=wx.RIGHT, border=8)

    buf = wx.TextCtrl(panel, style=wx.TE_MULTILINE, size=(200,60))
    buf.SetSize(ui.text_size(buf, rows=10, cols=40))
    hbox.Add(buf, proportion=2)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)
    panel.Fit()
    
    return panel
