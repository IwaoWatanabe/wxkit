# coding: utf-8

from __future__ import print_function
import functools, os, sys, threading
import concurrent.futures
from traceback import format_exc

if sys.version_info < (3, 0):
  from Queue import Queue, Empty
else:
  from queue import Queue, Empty

trace = print

try:
    import wx

except ImportError as e:
    trace('ERROR: %s (%s) while import wx' % (e, type(e).__name__), file=sys.stderr)
    sys.exit(1)

ui = __import__(__name__) # 自身を指す

def get_clipboard_text():
    """ クリップボードからテキストを入手する"""
    data = wx.TextDataObject()
    if wx.TheClipboard.Open():
        success = wx.TheClipboard.GetData(data)
        wx.TheClipboard.Close()

    if success: return data.GetText()
        
            
def set_clipboard_text(text):
    """ クリップボードにテキストを設定する"""
    data = wx.TextDataObject()
    data.SetText('asdf')
    if wx.TheClipboard.Open():
        wx.TheClipboard.SetData(data)
        wx.TheClipboard.Close()
    else:
        wx.MessageBox('Unable to open the clipboard', 'Error')

        
def trace_text(e):
    """スタック・トレースのテキストを入手する"""
    msg = "%s\n\n%s\n%s\n\n%s" % (e, "-" * 20, e.__class__, format_exc())
    title = "%s - Internal Error" % e.__class__.__name__
    return msg, title


def show_error(prompt, title='error', **options):
    if isinstance(prompt, Exception):
        prompt, title = trace_text(prompt)

    parent = options.get('parent', None)
    set_clipboard_text(prompt)
    msg = wx.MessageDialog(parent, prompt, title, style=wx.OK |wx.ICON_ERROR)
    msg.ShowModal()
    msg.Destroy()

    
def show_warning(self, prompt, title='warning', **options):
    parent = options.get('parent', None)
    msg = wx.MessageDialog(parent, prompt, title, style=wx.OK |wx.ICON_WARNING)
    msg.ShowModal()
    msg.Destroy()

    
def show_info(prompt, title='info', **options):
    parent = options.get('parent', None)
    msg = wx.MessageDialog(parent, prompt, title, style=wx.OK |wx.ICON_INFORMATION)
    msg.ShowModal()
    msg.Destroy()
    

def alert(func):
  # 取り急ぎは空のデコレータ（後で書き換える）
  return func


def _alert1(func):
  """例外が生じたらそれを表示するデコレータ"""
  @functools.wraps(func)
  def _elog(self, *args, **kwargs):
    try: return func(self, *args, **kwargs)
    except Exception as e: show_error(e)
  return _elog

#alert = _alert1


# 別スレッドからGUI処理を受け取る間隔(ms)
_polling_interval = 200

_polling_timer = None

# スレッドプールの最大平行処理数
_max_workers = 20

# スレッドプール
_executor = None


class _AsyncTask:
  """非同期呼び出しのパラメータを保持するクラス"""
  def __init__(self, cmd, proc, closure, kwds):
    self.cmd = cmd
    self.proc = proc
    self.closure = closure
    self.kwds = kwds
    self.flag = False
    self.error = None
    self.msg = None

  def call(self):
    try:
      self.proc(self.cmd, *self.closure, **self.kwds)
      self.flag = True

    except Exception as e:
      msg, title = trace_text(e)
      trace('Error: %s while proc%s\n%s' % (e, self.proc, msg), file=sys.stderr)
      self.error = e
      self.msg = msg
      wx.CallAfter(self.notify)

  def notify(self):
    """ EDTでダイアログを表示する"""
    trace("", "ERROR " * 10, "\n", self.msg, "\n", "ERROR " * 10, file=sys.stderr)
    show_error(self.msg, "%s - Internal Error" % self.error.__class__.__name__)


class App():
  '''GUIアプリケーションのユーザコードが継承するクラス。
ユーザコードが必要に応じて定義すべきメソッドを定義する'''

  def create_widget(self, base):
    '''このタイミングでユーザコードはGUIを組み立てる
  baseにはGUIパーツを組み立てる場所が渡されてくる。（通常はフレーム）'''
    pass

  def create_menubar(self):
    pass

  def execute_task(self, cmd, *args, **kargs):
    '非同期に処理される内容を記述する'
    pass

  title = None # このプロパティを介してタイトルを入手する
  
  cc = None # アプリケーション・コンテキストが設定される

  @classmethod
  def run(Cls, args=()):
    Cls.start(args)
    wxapp.MainLoop()
    sys.exit(0)

  @classmethod
  def start(Cls, *args):
    app = Cls()
    cc = _WxAppContext()
    top = cc._create_wx_app(app)
    top.Show()


debug = os.environ.get('UIDEBUG', 0)

_wx_default_id_map = {
    'new': wx.ID_NEW,
    'open': wx.ID_OPEN,
    'close': wx.ID_CLOSE,
    'about': wx.ID_ABOUT,
    'undo': wx.ID_UNDO,
    'redo': wx.ID_REDO,
    'copy': wx.ID_COPY,
    'quit': wx.ID_EXIT,
}

class _WxAppContext():
  def _create_wx_app(self, app):
    app.cc = self
    self.apps = [app]
    self.menu_map = {}
    top = wx.Frame(None, wx.ID_ANY)
    self.top = top
    self.Bind = top.Bind

    cnt = app.create_widgets(top)
    title = app.title
    if not title: title = app.__class__.__name__
    top.SetTitle(title)
    bar = app.create_menubar()
    if bar: top.SetMenuBar(bar)
    top.Fit()
    return top

  def __init__(self):
    self.dir_dialog = None
    self._status_text = None

  @property
  def status_text(self):
    return self._status_text

  @status_text.setter
  def status_text(self, text):
    self._status_text = text

  def set_status(self, text):
    self.status_text = text
  
  def dispose(self):
    self.top.Close()
    
  def show_error(self, prompt, title='error', **options):
    options['parent'] = self.top
    show_error(prompt, title, **options)

  def show_warning(self, prompt, title='warning', **options):
    options['parent'] = self.top
    show_warning(prompt, title, **options)

  def show_info(self, prompt, title='info', **options):
    options['parent'] = self.top
    show_info(prompt, title, **options)

  def input_text(self, prompt='', title='input', **options):
    """ テキスト入力のダイアログ表示 """
    deftext = options.get('default','')
    dlg = wx.TextEntryDialog(self.top, prompt,title)
    if deftext: dlg.SetValue(deftext)
    res = dlg.GetValue() if dlg.ShowModal() == wx.ID_OK else ''
    dlg.Destroy()
    return res

  def ask_ok_cancel(self, prompt, title='ask', **options):
    """ [OK] [Cancel]　ボタン付の質問ダイアログ表示 """
    msg = wx.MessageDialog(self.top, prompt, title,
                           style=wx.OK | wx.CANCEL | wx.ICON_QUESTION)
    res = msg.ShowModal()
    msg.Destroy()
    return res == wx.ID_OK

  def ask_yes_no(self, prompt, title='ask', **options):
    """ [Yes] [No]　ボタン付の質問ダイアログ表示 """
    msg = wx.MessageDialog(self.top, prompt, title,
                           style=wx.YES_NO | wx.ICON_QUESTION)
    res = msg.ShowModal()
    msg.Destroy()
    return res == wx.ID_YES

  def ask_retry_cacnel(self, prompt, title='retry?', **options):
    """ [Retry] [Cancel]　ボタン付の警告ダイアログ表示 """
    msg = wx.MessageDialog(self.top, prompt, title,
                           style=wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)
    msg.SetOKLabel('Retry')
    res = msg.ShowModal()
    msg.Destroy()
    return res == wx.ID_OK

  def ask_abort_retry_ignore(self, prompt, title='retry?', **options):
    """ [Abort] [Retry] [Ignore]　ボタン付の警告ダイアログ表示 """
    msg = wx.MessageDialog(self.top, prompt, title,
                           style=wx.YES_NO | wx.CANCEL | wx.ICON_EXCLAMATION)
    msg.SetYesNoCancelLabels('Abort', 'Retry', 'Ignore')
    res = msg.ShowModal()
    msg.Destroy()
    return 'abort' if res == wx.ID_YES else 'retry' if res == wx.ID_NO else 'ignore'

  def ask_color(self, color=None, **options):
    """ 色選択ダイアログ表示 """
    pass

  def ask_open_file(self, multiple=False, **options):
    """ ファイルを選択する """
    title = options.get('title', 'Open file')
    filetypes = options.get('filetypes', ())
    wildcard = 'text files (*.txt)|*.txt;All files (*.*)|*.*'
    initialdir = options.get('initialdir', '')
    parent = options.get('parent', self.top)
    # https://wxpython.org/Phoenix/docs/html/wx.FileDialog.html
    style = wx.FD_OPEN|wx.FD_FILE_MUST_EXIST
    if multiple: style |= wx.FD_MULTIPLE
    with wx.FileDialog(parent, title, defaultDir=initialdir, style=style) as dlg:
      if multiple: return dlg.GetPaths() if dlg.ShowModal() != wx.ID_CANCEL else []
      return dlg.GetPath() if dlg.ShowModal() != wx.ID_CANCEL else ''

  def ask_save_file(self, **options):
    """ 保存用にローカル・ファイルを選択させる"""
    parent = options.get('parent', self.top)
    title = options.get('title', 'Save file')
    wildcard = 'text files (*.txt)|*.txt'
    initialdir = options.get('initialdir', '')

    with wx.FileDialog(parent, title, wildcard=wildcard, defaultDir=initialdir,
                       style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:
      return dlg.GetPath() if dlg.ShowModal() != wx.ID_CANCEL else ''

  def ask_folder(self, **options):
    """ 保存用にローカル・ディレクトリを選択させる"""
    parent = options.get('parent', self.top)
    initialdir = options.get('initialdir', '')
    # https://torina.top/detail/191/
    title = options.get('title', 'Choose a directory')
    dlg = self.dir_dialog
    if not dlg:
      dlg = wx.DirDialog(parent, message=title, defaultPath=initialdir,
                         style=wx.DD_DIR_MUST_EXIST|wx.DD_CHANGE_DIR)
      self.dir_dialog = dlg
    return dlg.GetPath() if dlg.ShowModal() == wx.ID_OK else ''

  def _perform(self, cmd, event):
    'メニュー選択のフォールバック'
    if debug: trace(cmd, event, file=sys.stderr)

  def _build_menu00(self, items, proc, id_map=None):
    '''メニュー・テキストから xwMenuを生成して返す素朴な実装
　　メニューアイテムは "name;表示テキスト;ショートカット;説明テキスト" で構成される
'''
    if not id_map: id_map = {}
    menu = wx.Menu()
    menu.hint = items[0].split(';')
    for item in items[1:]:
      it = item.split(';'); itlen = len(it)
      cmd = it[0]
      label = it[1] if itlen > 1 else cmd
      short_cut = it[2] if itlen > 2 else ''
      if short_cut: label = '%s\t%s'% (label, short_cut)
      desc = it[3] if itlen > 3 else ''
      if cmd == '-': menu.AppendSeparator(); continue
      id = id_map.get(cmd, _wx_default_id_map.get(cmd, -1))
      item = menu.Append(id, label)
      self.Bind(wx.EVT_MENU, alert(lambda ev, cmd=cmd: proc(cmd, ev)), item)
    return menu

  def find_menu(self, name, items, **opts):
    'メニュー・テキスト群から対象メニューを探し出し、xwMenuを生成して返す'
    app = opts.get('app', self.apps[-1])
    proc = opts.get('proc', app.perform if hasattr(app, 'perform') else self._perform)
    id_map = opts.get('id_map')
    for item in items:
      if item[0].split(';')[0] == name:
        return self._build_menu00(item, proc, id_map=id_map)

  def execute(self, cmd, *closure, **option):
    """タスクをスレッド・プール経由で動作させる """
    global _executor
    if not _executor:
      _executor = concurrent.futures.ThreadPoolExecutor(max_workers=_max_workers)

    proc = option.get('proc', self.apps[-1].execute_task)
    task = _AsyncTask(cmd, proc, closure, option)
    task.app = self
    _executor.submit(self._run_task, task)

  def _run_task(self, task):
    # 別スレッドで動作する
    th = threading.currentThread()
    th.task = task
    if debug: trace("#_run_task ", task)
    task.call()

  def invoke_lator(self, cmd, *closure, **opts):
    """GUIの処理キューに処理を登録する"""
    th = threading.currentThread()
    task = _AsyncTask(cmd, th.task.proc, closure, opts)
    task.app = self
    wx.CallAfter(task.call)
    if debug: trace("#invoke_lator ", cmd, task.proc, closure)

  def invoke_and_wait(self, cmd, *closure, **opts):
    """GUIに処理を依頼して完了するまで待つ"""
    th = threading.currentThread()
    task = _AsyncTask(cmd, th.task.proc, closure, opts)
    task.app = self
    task.flag = False
    wx.CallAfter(task.call)
    while not task.flag: sleep(0.2)

  def create_dialog(self, AppClass, *opts, **kwd):
    """ダイアログを作成する"""
    owner = kwd.pop('owner', self.top)
    title = kwd.pop('title', None)
    top = wx.Dialog(parent=owner)
    cc = self.__class__()
    cc.Bind = top.Bind

    if opts or kwd:
        app = AppClass(*opts, **kwd)
    else:
        app = AppClass()

    app.cc = cc
    app.dialog = cc.top = top
    cnt = app.create_widgets(top)
    if not title: title = app.title
    if not title: title = app.__class__.__name__
    top.SetTitle(title)
    top.Fit()

    return app
    
      
wxapp = wx.App()



def text_size(buf, rows=10, cols=30):
  dc = wx.WindowDC(buf)
  width, height = dc.GetMultiLineTextExtent('\n'.join(['M'*cols]*rows))[:2]
  #trace(width, height, file=sys.stderr)
  return width, height
    
