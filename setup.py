from setuptools import setup

APP = ['pet.py'] # 실제 파이썬 파일 이름으로 수정하세요
DATA_FILES = ['tamagochi.png', 'pet.png', 'PFStardust.ttf'] # 앱에 포함될 이미지와 폰트 파일
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'AppIcon.icns', # 💡 이 줄을 추가하세요! (파일명 확인)
    'plist': {
        'LSUIElement': True, # Dock에 아이콘을 표시하지 않으려면 True
        'CFBundleName': "yoonigotchi", # 💡 앱 메뉴바 등에 표시될 이름
        'CFBundleDisplayName': "yoonigotchi", # 💡 Finder나 Dock에 표시될 이름
        'CFBundleIdentifier': "com.yoonkyung.yoonigotchi", # 💡 고유 식별자도 변경
        'CFBundleVersion': "1.0.0",
    },
    'packages': ['objc', 'AppKit', 'Foundation'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)