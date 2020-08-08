from setuptools import setup, find_packages
setup(
    name="PiaoManga",
    version="0.9.0",
    packages=find_packages(),
    description=u"漫画下载器框架",
    author="closesakuya",
    author_email="closesakuya@sina.com",
    url="None",
    license="None",
    install_requires=[  # 依赖列表
        'aiofiles>=0.5.0',
        'aiohttp>=3.6.1',
        'attr>=0.3.1',
        'beautifulsoup4>=4.9.1',
        'pyppeteer>=0.0.25',
        'requests>=2.23.0'
    ]
)
