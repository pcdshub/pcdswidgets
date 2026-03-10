import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py


class MakeBuildFirst(build_py):
    """
    Use the instructions in the Makefile to generate needed .py files from the .ui source
    """

    def run(self, *args, **kwargs):
        subprocess.check_call(("make", "build"))
        return super().run(*args, **kwargs)


setup(cmdclass={"build_py": MakeBuildFirst})
