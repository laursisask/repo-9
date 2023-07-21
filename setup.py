from setuptools import setup

from version import modular_api_version

setup(
    name='modular',
    version=modular_api_version,
    py_modules=['modular'],
    install_requires=[
        'setuptools==60.6.0',
        'prettytable==3.2.0',
        'bottle==0.12.19',
        'click==7.1.2',
        'PyYAML==6.0.0',
        'swagger-ui-py==21.12.8',
        'ddtrace==0.58.5',
        'PyJWT==2.4.0',
        'pydantic==1.9.1',
        'tinydb==4.7.0',
        'pydantic==1.9.1',
        'Beaker==1.11.0',
        'pynamodb==5.3.2',
        'Pillow==8.3.1',
        'modular-sdk',
        'modular-cli-sdk'
    ],
    entry_points={
        'console_scripts': [
            'modular = modular_api_cli.modular_cli_group.modular:modular',
        ],
    },
)
