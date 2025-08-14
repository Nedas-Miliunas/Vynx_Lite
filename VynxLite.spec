block_cipher = None
a = Analysis(['main.py'],
             pathex=[],
             binaries=[],
             datas=[('assets', 'assets')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Vynx_Lite',
          console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='Vynx_Lite')
