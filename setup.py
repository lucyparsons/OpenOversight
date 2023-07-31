from setuptools import setup


setup(
    name="OpenOversight",
    version="0.6.7",
    description="OpenOversight is a Lucy Parsons Labs project to improve law "
    + "enforcement accountability through public and crowdsourced data.",
    author="redshiftzero",
    author_email="jen@redshiftzero.com",
    classifiers=(
        "Natural Language :: English",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3 :: Only",
    ),
    python_requires=">=3.11",
    install_requires=["flask", "werkzeug", "Flask-WTF", "psycopg2", "sqlalchemy"],
)
