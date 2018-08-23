# coding: utf-8

from wxkit import wx, ui

class HelloApp(ui.App):
  def create_widgets(self, base):
    msg = wx.StaticText(base, label=u"hello wx!\n日本語も大丈夫！")
    font = wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    msg.SetFont(font)



