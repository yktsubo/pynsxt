from setuptools import setup, find_packages

setup(
    name='pynsxt',
    version='0.1',
    packages=find_packages(),
    install_requires=['requests', 'bravado-core'],
    entry_points={
            'console_scripts':
        'pynsxt = pynsxt.main:main'
    },
    zip_safe=False,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
    ],
)
