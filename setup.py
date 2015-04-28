from distutils.core import setup

with open('requirements.txt') as f:
    requirements = [l.strip() for l in f]

setup(
    name='hamper-pizza',
    version='0.1',
    packages=['hamper-pizza'],
    author='Dean Johnson',
    author_email='deanjohnson222@gmail.com',
    url='https://github.com/dean/hamper-pizza',
    install_requires=requirements,
    package_data={'hamper-pizza': ['requirements.txt', 'README.md', 'LICENSE']},
    entry_points={
        'hamperbot.plugins': [
            'pizza = hamper_pizza.pizza:Pizza',
        ],
    },

)
