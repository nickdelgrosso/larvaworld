from setuptools import setup, find_packages, find_namespace_packages

setup(
    name='larvaworld',
    version='0.1.0',
    description='Drosophila larva behavioral analysis and simulation platform',
    url='https://github.com/nawrotlab/larvaworld',
    author='Panagiotis Sakagiannis',
    author_email='bagjohn0@gmail.com',
    license='GNU GENERAL PUBLIC LICENSE',
    packages=find_packages(),
    # packages=find_namespace_packages(include=['gui/media*'], exclude=['jupyter_lab.*', 'my_work.*']),
    py_modules=["larvaworld", "larvaworld_gui"],
# include_package_data=True,
exclude_package_data={'' : ['jupyter_lab/*', 'my_work/*']},
package_data={
    # '': ['requirements.txt'],
    'gui': ['gui/media/*/*.*', 'gui/media/exp_figures/*/*.*'],
},
data_files=[('', ['requirements.txt'])],
entry_points={
    'console_scripts': [
        'larvaworld=larvaworld:larvaworld',
        'larvaworld_gui=larvaworld:larvaworld_gui',
    ],
},
    install_requires=['pandas',
                      'numpy',
                      'typing-extensions',
                      'PySimpleGUI',
                      'shapely',
                      'imageio',
                      'agentpy',
                      'box2d-py',
                      'pygame',
                      'argparse',
                      'pint',
                      'matplotlib',
                      'seaborn',
                      'scikit-learn',
                      'scipy',
                      ],

    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        # 'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
