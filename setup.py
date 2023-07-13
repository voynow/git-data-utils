from setuptools import setup, find_packages

setup(
    name='git2doc',
    version='0.2.4',
    description='A tool for converting git repositories into documents',
    author='Jamie Voynow',
    author_email='voynow99@gmail.com',
    url='https://github.com/voynow/git2doc',
    packages=find_packages(),
    install_requires=[
        'langchain',
        'tiktoken',
        'gitpython',
        "python-dotenv",
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',  
        'Intended Audience :: Developers',  
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',  
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
	],
	long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type='text/markdown'
)

# python setup.py sdist bdist_wheel
# twine upload dist/*