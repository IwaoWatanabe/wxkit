# coding: utf-8

import os, sys
from wxkit import trace

app_classes = [
    'wxkit.memo.SearchDialog',
    'wxkit.table.TSVEditorApp',
    'wxkit.basic.BasicWX',
    'wxkit.memo.MemoApp02',
    'wxkit.memo.MemoApp01',
    'wxkit.hello.HelloApp',
]

def _find_class(hn):
  'クラスを入手する'
  ms = hn.split('.')
  __import__('.'.join(ms[:-1]))
  mod = __import__(ms[0])
  for an in ms[1:]: mod = getattr(mod,an)
  return mod

def _apdic(cn):
  cns = cn.split(':'); cn = cns.pop(0)
  return cns[0] if cns else cn.split('.')[-1].replace('App','').replace('Dialog','').lower(), cn

aplst = [_apdic(cn) for cn in app_classes]

with open(os.environ.get('APPS','apps.txt')) as fh:
  aplst.extend([_apdic(cn) for cn in fh])

apdic = { an: (an, cn) for an, cn in aplst }
                         
apname = sys.argv[1] if len(sys.argv) > 1 else ""
mm = apdic.get(apname, aplst[0]) # 見つからなければ、先頭のアプリを動かす

if os.environ.get("SHOW", ""):
  trace("apps", sorted(apdic.values(), key=lambda x: x[0]))
  
if os.environ.get("ALL", ""):
  apdic.pop(mm[0], None)
  for apname, hn in apdic.values():
    _find_class(hn).start()

_find_class(mm[1]).run(sys.argv[1:])

