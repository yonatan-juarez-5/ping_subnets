# to build
$ python setup.py sdist bdist_wheel

# to install package
$ pip install .

# python formatting
$ pylint ping_subnets/main.py
$ flake8 ping_subnets/main.py

# examply scrript to run main.py
$ python example.py