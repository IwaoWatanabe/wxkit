# coding: utf-8

import os, sys
import codecs

from wxkit import wx, ui, trace

class MemoApp01(ui.App):
  def create_widgets(self, base):
    buf = wx.TextCtrl(base, style=wx.TE_MULTILINE)
    font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    buf.SetFont(font)
    buf.SetSize(ui.text_size(buf, rows=10, cols=30))
    

memo_menu_items = [
  ['file;ファイル',
   'new;新規メモ',
   'open;メモを開く ..;Ctrl+O',
   'close;メモを閉じる;Ctrl+W',
   '-',
   'about;メモについて',
  ],
  ['edit;編集',
   'copy;&Copy;Ctrl+C',
   'select-all;全て選択;Ctrl+A',
   '-',
   'search;&Search;Ctrl+F',
   'goto-line;&Goto Line ..;Ctrl+L',
  ],
  ['view;表示',
   'font;フォント;',
   '-',
   'big;拡大;Ctrl++',
   'small;縮小;Ctrl+-',
  ],
  ['shortcut;',
   'copy;複製;Ctrl+C',
   'select-all;全て選択;Ctrl+A',
   '-',
   'search;&Search;Ctrl+F',
   'goto-line;&Goto Line;Ctrl+L',
   '-',
   'open;メモを開く ..;Ctrl+O',
   'close;メモを閉じる;Ctrl+W',
  ],
]


class _LocalMemo():
  default_encoding = sys.getfilesystemencoding()
  
  def readlines(self, filename, lines=100, encoding='', ws='\r\n'):
    '指定した行単位でテキスト・ファイルを読み込む'
    buf = []
    with codecs.open(filename, encoding=encoding) as fh:
      if not encoding: encoding = self.default_encoding
      ct = 0
      line = fh.readline()
      while line:
        buf.append(line.rstrip(ws))
        ct += 1
        if ct >= lines:
          res = '\n'.join(buf); buf = []; ct = 0; yield res
        line = fh.readline()

    if buf: res = '\n'.join(buf); buf = None; yield res

  def load_tsv(self, path, encoding='', step=100, ws='\r\n'):
    "TSVファイルからテキストを指定する行数単位で読み込む"
    if not encoding: encoding = self.default_encoding
    fctx = gzip.open(path) if path.endswith('.gz') else open(path)
    with fctx as fh:
      tt = fh.readline()
      buf = []
      while tt:
        ta = tuple(tt.rstrip(ws).decode(encoding).split('\t'))
        buf.append(ta)
        if len(buf) == step:
          yield buf
          buf = []
        tt = fh.readline()

      if buf: yield buf
    
    
class MemoApp02(ui.App):
  def create_widgets(self, base):
    buf = wx.TextCtrl(base, style=wx.TE_MULTILINE)
    font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    buf.SetFont(font)
    buf.SetSize(ui.text_size(buf, rows=10, cols=30))
    self.buf = buf
    cc = self.cc
    short_cut = cc.find_menu('shortcut', memo_menu_items)

    def _popup(ev):
      pos = ev.GetPosition()
      pos = buf.ScreenToClient(pos)
      buf.PopupMenu(short_cut, pos)
            
    buf.Bind(wx.EVT_CONTEXT_MENU, _popup) # コンテキストメニューの登録

  def create_menubar(self):
    cc = self.cc
    bar = wx.MenuBar()
    for mn in 'file:edit:view'.split(':'):
      menu = cc.find_menu(mn, memo_menu_items)
      bar.Append(menu, menu.hint[1])
    return bar

  def perform(self, cmd, event):
    'メニュー・アイテムが選択されたらこちらが呼び出される'
    if ui.debug: trace(cmd, event, file=sys.stderr)
    buf = self.buf
    cc = self.cc
    
    if 'copy' == cmd:
      buf.Copy();return
        
    elif 'select-all' == cmd:
      buf.SelectAll(); return

    elif 'goto-line' == cmd:
      ln = buf.GetNumberOfLines()
      msg = 'Input Line Number 1..%d' % ln
      msg = u'移動行を入力ください (範囲 1..%d)' % ln
      line = cc.input_text(msg)
      if not line: return

      pos = 0
      for nn in xrange(0, int(line) - 1):
        pos += buf.GetLineLength(nn) + 1
                
      trace('goto line:%s of %s -> pos:%s', line, ln, pos)
      if pos >= 0:
        buf.SetInsertionPoint(pos)
        buf.ShowPosition(pos)

    elif 'open' == cmd:
      tt = cc.ask_open_file()
      if not tt: return
      buf.Clear() 
      wx.BeginBusyCursor()
      cc.execute('load', text_file=tt)
      
    elif 'close' == cmd:
      cc.dispose(); return

    elif 'quit' == cmd:
      wx.Exit(); return

    elif 'new' == cmd:
      self.__class__().start(); return

    elif 'about' == cmd:
      cc.show_info('\n'.join((
          'Python version: ' + sys.version,
          'plastform: ' + sys.platform,
          'wwPython: ' + wx.version(), '', sys.copyright, '',
          'home: ' + os.path.expanduser('~'))), 'メモについて')
      return
    
  memo = _LocalMemo()
  
  def execute_task(self, cmd, *closure, **opts):
    #trace("#execute task", cmd, closure)
    cc = self.cc
    memo = self.memo
    buf = self.buf
    
    if 'load' == cmd:
      text_file = opts.get('text_file')
      if not text_file: return
      step = opts.get('step', 1000)
      try:
        for tt in memo.readlines(text_file, lines=step):
          #trace("readlines", len(tt), "bytes.")
          cc.invoke_lator('append-text', text=tt)
          #wx.Sleep(2)
      finally: cc.invoke_lator('done')
          
    # 以下はEDTで動作    
    elif 'append-text' == cmd:
      buf.AppendText(opts.get('text','')); return
      buf.SetInsertionPoint(pos)
      buf.ShowPosition(0)

    elif 'done' == cmd:
      wx.EndBusyCursor()
      pos = 0
      buf.SetInsertionPoint(pos)
      buf.ShowPosition(pos)
      return

  def search_forward(self, term, nocase=None, regexp=None):
    """順方向に検索する"""
    if not term: return
    buf = self.buf
    ipos = buf.GetInsertionPoint()
    trace("ipos", ipos)

    pos = buf.GetValue()[ipos:].indexOf(term)
    if pos < 0: return
    buf.SetSelection(pos, ipos + len(term))
        
  def search_backward(self, term, nocase=None, regexp=None):
    """逆方向に検索する"""
    if not term: return
    buf = self.buf
    ipos = buf.GetInsertionPoint()
    trace("ipos", ipos)

    pos = buf.GetValue()[:ipos].rindexOf(term)
    if pos < 0: return
    buf.SetSelection(pos, ipos + len(term))

  @property
  def font(self):
    attr = buf.GetDefaultStyle()
    return attr.GetFont()
    # http://d.hatena.ne.jp/morchin/20071030

  @font.setter
  def font(self, font):
    attr = buf.GetDefaultStyle()
    attr.SetFont(font)
    
    
def _append_term(self, ent, *terms, **opts):
  'コンボボックスに要素を追加する'
  replace = opts.get('replace', False)
  if replace: ent.SetItems(terms); return
  for tt in terms: ent.Append(tt)


class SearchDelegator():
  '検索ダイアログから呼び出される処理'
  def find_forward(self, term, ignore_case=True, **opts):
    print 'forward:', term, ignore_case, opts

  def find_backward(self, term, ignore_case=True, **opts):
    print 'backward:', term, ignore_case, opts

  def replace_term(self, term):
    print 'replaece', term


class SearchDialog(ui.App):
  '素朴な検索ダイアログ'
  @property
  def search_term(self):
    return self.search_ent.GetValue()

  @search_term.setter
  def search_term(self, term):
    return self.search_ent.SetValue(term)

  @property
  def replace_term(self):
    return self.replace_ent.GetValue()

  @replace_term.setter
  def replaece_term(self, text):
    return self.replace_ent.SetValue(term)

  def create_widgets(self, base):
    cc = self.cc
    vbox = wx.BoxSizer(wx.VERTICAL)
    panel = wx.Panel(base)
    panel.SetSizer(vbox)

    # ------- 検索キーワード
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Search:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)
        
    ent = wx.ComboBox(panel, style=wx.TE_PROCESS_ENTER)
    ent.SetValue('search term')
    self.search_ent = ent
    hbox.Add(ent, proportion=1)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # ------- 置換キーワード
    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cap = wx.StaticText(panel, label='Replace:')
    hbox.Add(cap, flag=wx.RIGHT, border=8)
        
    ent = wx.ComboBox(panel, style=wx.TE_PROCESS_ENTER)
    ent.SetValue('replaece term')
    self.replace_ent = ent
    hbox.Add(ent, proportion=1)
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    # ------- オプション

    hbox = wx.BoxSizer(wx.HORIZONTAL)
    cb = wx.CheckBox(panel, label=u'大文字と小文字を区別しない')
    cb.SetValue(True)
    self.ignore_case = cb
    hbox.Add(cb, flag=wx.LEFT, border=5)

    fdir = map(lambda tt: tt.split(':'), ('backward:上へ', 'forward:下へ'))
    #print fdir
    rbox = wx.RadioBox(panel, label=u'検索方向', choices=[tt[0] for tt in fdir])
    for rkey, label in fdir:
      rbox.SetItemLabel(rbox.FindString(rkey), label)
    self.fdir = rbox
    
    hbox.Add(rbox, flag=wx.LEFT, border=5)

    btn = wx.Button(panel, label='Find')
    cc.Bind(wx.EVT_BUTTON, lambda ev, cmd='find': self._perform(cmd, ev), btn)
    hbox.Add(btn, flag=wx.LEFT, border=5)
    
    btn = wx.Button(panel, label='Replace and Find')
    cc.Bind(wx.EVT_BUTTON, lambda ev, cmd='replace': self._perform(cmd, ev), btn)
    hbox.Add(btn, flag=wx.LEFT, border=5)
    
    btn = wx.Button(panel, label='Close')
    cc.Bind(wx.EVT_BUTTON, lambda ev, cmd='close': self._perform(cmd, ev), btn)
    hbox.Add(btn, flag=wx.LEFT, border=5)
    
    vbox.Add(hbox, flag=wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, border=5)

    panel.Fit()
    
  def perform(self, cmd, event):
    if ui.debug: trace('basic cmd:',cmd,'event:',event)
    cc = self.cc

    ic = self.ignore_case.IsChecked()
    fdir = self.fdir.GetSelection()
    find = self.delegator.find_forward if fdir == 1 else self.delegator.find_backward
    if 'find' == cmd:
      rc = find(term=self.search_term, ignore_case=ic)

    elif 'replace' == cmd:
      self.delegator.replace_term(self.replace_term)
      rc = find(term=self.search_term, ignore_case=ic)
      
    elif 'close' == cmd:
      cc.top.Show(False)
      
  _perform = ui.alert(perform)

  def open(self, term=None, delegator=None):
    self.delegator = delegator if delegator else SearchDelegator()
    self.search_term = term
    #self.dialog.ShowModal()
    dig = self.dialog
    dig.Show(False)
    dig.Show(True)
    
