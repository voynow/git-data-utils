from setuptools import setup, find_packages

setup(
    name='git2vec',
    version='0.1.5',
    description='A useful module for handling Git data.',
    author='Jamie Voynow',
    author_email='voynow99@gmail.com',
    url='https://github.com/voynow/git2vec',
    packages=find_packages(),
    install_requires=[
        'langchain',
        'pinecone-client',
        'tiktoken',
        'gitpython',
        "python-dotenv",
        "pandas",
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
