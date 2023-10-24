from setuptools import setup

from version import modular_api_version

setup(
    name='modular',
    version=modular_api_version,
    py_modules=['modular'],
    install_requires=[
        'setuptools==68.2.1',
        'prettytable==3.9.0',
        'bottle==0.12.25',
        'click==7.1.2',
        'PyYAML==6.0.1',
        'swagger-ui-py==21.12.8',
        'ddtrace==0.61.5',
        'PyJWT==2.8.0',
        'pydantic==1.10.2',
        'tinydb==4.7.0',
        'Beaker==1.12.1',
        'typing_extensions==4.7.1',
        'pynamodb==5.3.2',
        'Pillow==10.0.0',
        'modular-cli-sdk>=2.0.0,<3.0.0',
        'modular-sdk>=3.0.0,<4.0.0'
    ],
    entry_points={
        'console_scripts': [
            'modular = modular_api_cli.modular_cli_group.modular:modular',
        ],
    },
)
