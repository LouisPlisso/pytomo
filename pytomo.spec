# -*- mode: python -*-
from platform import system, machine

a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'Pytomo-1.9.6\\bin\\pytomo'],
             pathex=['Pytomo-1.9.6\\', 'Pytomo-1.9.6\\pytomo', 'C:\\Documents and Settings\\rqpj0589\\Desktop'])
pyz = PYZ(a.pure)
exe = EXE( pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=''.join(('_'.join(('pytomo', system().lower(), machine())),
                '.exe')),
          #name=os.path.join('dist', 'pytomo.exe'),
          debug=False,
          strip=False,
          upx=True,
          console=True )
