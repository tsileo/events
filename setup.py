from setuptools import setup

setup(
    name="events",
    version="0.1.0",
    py_modules=["events"],
    install_requires=[
        "pyyaml",
        "caldav",
    ],
    entry_points={"console_scripts": ["events = events:main"]},
)
