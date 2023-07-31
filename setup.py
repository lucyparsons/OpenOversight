from setuptools import setup


setup(
    name="OpenOversight",
    version="1.0",
    description="Oversight of Police Departments",
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
