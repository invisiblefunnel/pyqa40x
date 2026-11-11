from setuptools import setup, find_packages

setup(
    name='PyQa40x',
    version='0.2.3',
    description='A Python library for the QA40x audio analyzer',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'numpy',
        'matplotlib',
        'scipy',
        'libusb1'
    ],
    extras_require={
        # Only needed to mirror playback to a Bluetooth/system audio device
        'bluetooth': ['pyaudio'],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

