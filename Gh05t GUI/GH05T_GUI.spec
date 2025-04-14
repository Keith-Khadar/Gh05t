# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

msgpack_hidden = collect_submodules('msgpack')
msgpack_data = collect_data_files('msgpack')
mne_datas, mne_binaries, mne_hiddenimports = collect_all('mne')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=mne_binaries,
    datas=mne_datas + msgpack_data,
    hiddenimports=['websockets',
                    'decorator',
                    'websockets',
                    'scipy',
                    'scipy.special',
                    'scipy.linalg',
                    'numpy',
                    'sklearn',
                    'matplotlib',
                    'matplotlib.pyplot',
                    'pkg_resources',
                    'joblib'] + mne_hiddenimports + msgpack_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GH05T_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
