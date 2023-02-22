from setuptools import setup

setup(
    name='sonic-platform-common',
    version='1.0',
    description='Platform-specific peripheral hardware interface APIs for SONiC-OTN',
    license='Apache 2.0',
    author='SONiC-otn Team',
    author_email='sonic-wg-otn@lists.sonicfoundation.dev',
    url='https://github.com/zhengweitang-zwt/sonic-otn-platform-common',
    maintainer='leixin',
    packages=[
        'otn_pmon',
        'otn_pmon.device',
    ],
    # NOTE: Install also depends on sonic-config-engine for portconfig.py
    # This dependency should be eliminated by moving portconfig.py
    # functionality into sonic-py-common
    install_requires=[
        'natsort==6.2.1', # 6.2.1 is the last version which supports Python 2
        'PyYAML',
        'redis',
        'sonic-py-common'
    ],
    setup_requires = [
        'pytest-runner',
        'wheel'
    ],
    tests_require = [
        'pytest',
        'pytest-cov',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    keywords='sonic SONiC platform hardware interface api API'
)
