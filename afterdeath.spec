# PyInstaller build recipe. Build with:  pyinstaller afterdeath.spec
# Produces dist/Afterdeath/ (one folder: Afterdeath.exe + _internal/ with the assets).

a = Analysis(
    ["afterdeath/__main__.py"],
    pathex=["."],
    datas=[("assets", "assets")],
    excludes=["tkinter", "pytest"],
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Afterdeath",
    console=False,  # windowed game; output goes to userdata/afterdeath.log
)

coll = COLLECT(exe, a.binaries, a.datas, name="Afterdeath")
