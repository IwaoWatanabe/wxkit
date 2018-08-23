# coding: utf-8

import os, sys

from wxkit import wx, ui, trace, memo

tsv_menu_items = [
  ["shortcut",
   'select-all;Select &All',
   'copy;&Copy',
   'cut;&Cut',
   'paste;&Paste',
   'delete;&Delete',
   'duplicate;&Duplicate',
   '-',
   'open;&Open ..',
   'close;&Close',
  ]
]

class TSVEditorApp(ui.App):
    def create_widgets(self, base):
      cc = self.cc
      clist = wx.ListCtrl(base, style=wx.LC_REPORT)
      clist.InsertColumn(0, 'column')
      idnex = clist.InsertStringItem(1, "empty")

      short_cut = cc.find_menu('shortcut', tsv_menu_items)

      def _popup(ev):
        pos = ev.GetPosition()
        pos = clist.ScreenToClient(pos)
        clist.PopupMenu(short_cut, pos)
            
      clist.Bind(wx.EVT_CONTEXT_MENU, _popup)
      self.clist = clist

    model = memo._LocalMemo()
    
    def perform(self, cmd, event):
      trace("cmd:%s event:%s" % (cmd, event))
      cc = self.cc
      clist = self.clist

      if "select-all" == cmd:
        pass

      elif "copy" == cmd:
        pass

      elif "paste" == cmd:
        pass
        
      elif "duplicate" == cmd:
        pass
        
      elif "open" == cmd:
        tt = cc.ask_open_file()
        if not tt: return
        encoding = None
        cc.execute("load-tsv", tt, encoding)
        return

      elif "close" == cmd:
        cc.dispose(); return

      elif "quit" == cmd:
        wx.Exit(); return

      elif "new" == cmd:
        self.__class__().start(); return

    def execute_task(self, cmd, *closure, **kws):
      "スレッドを分けて処理する"
      cc = self.cc
      model = self.model

      if "load-tsv" == cmd:
        # ファイル名を指定して読み込む
        fn, encoding = closure[:2]
        step = kws.get("step", 5)

        ncmd = "replace-tsv"
        for tline in model.load_tsv(fn, encoding, step):
          cc.invoke_lator(ncmd, tline)
          ncmd = "append-tsv"
        return
        
      clist = self.clist

      if "append-tsv" == cmd:
        rows = closure[0]
        if not rows: return
        for idx, row in enumerate(rows, clist.GetItemCount()):
          clist.InsertStringItem(idx, row[0])
          for cn, data in enumerate(row[1:], 1):
            clist.SetStringItem(idx, cn, row[cn])
        return
      
      elif "replace-tsv" == cmd:
        rows = closure[0]
        if not rows: return
        clist.DeleteAllItems()
        clist.DeleteAllColumns()

        # 先頭行をカラム名として利用する
        cols = rows.pop(0)
        for idx, cname in enumerate(cols):
          clist.InsertColumn(idx, cname)
            
        for idx, row in enumerate(rows):
          clist.InsertStringItem(idx, row[0])
          for cn, data in enumerate(row[1:], 1):
            clist.SetStringItem(idx, cn, row[cn])
      
