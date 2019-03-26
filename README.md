![](docs/img/lpl-logo.png)

# OpenOversight [![Build Status](https://travis-ci.org/lucyparsons/OpenOversight.svg?branch=develop)](https://travis-ci.org/lucyparsons/OpenOversight) [![Coverage Status](https://coveralls.io/repos/github/lucyparsons/OpenOversight/badge.svg?branch=develop)](https://coveralls.io/github/lucyparsons/OpenOversight?branch=develop) [![Documentation Status](https://readthedocs.org/projects/openoversight/badge/?version=latest)](https://openoversight.readthedocs.io/en/latest/?badge=latest) [![Join the chat at https://gitter.im/OpenOversight/Lobby](https://badges.gitter.im/OpenOversight/Lobby.svg)](https://gitter.im/OpenOversight/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

OpenOversight is a Lucy Parsons Labs project to improve law enforcement accountability through public and crowdsourced data. We maintain a database of officer demographic information and provide digital galleries of photographs. This is done to help people identify law enforcement officers for filing complaints and in order for the public to see work-related information about law enforcement officers that interact with the public.

This project is written and maintained by [@lucyparsonslabs](https://twitter.com/lucyparsonslabs) with collaboration, partnerships, and contributions welcome. If you would like to contribute code or documentation, please see our [contributing guide](/CONTRIB.md) and [code of conduct](/CODE_OF_CONDUCT.md). You can get a [tip](#tips) for implementing important issues. If you prefer to contribute in other ways, please submit images to our platform or talk to us about how to help sort and tag images. This project is in public beta, and we are currently soliciting photographs to add to the database.

## Note to Law Enforcement

Please contact our legal representation with requests, questions, or concerns of a legal nature by emailing [legal@lucyparsonslabs.com](mailto:legal@lucyparsonslabs.com).

## Issues

Please use [our issue tracker](https://github.com/lucyparsons/OpenOversight//issues/new) to submit issues or suggestions.

## Tips

We offer financial tips as a thank you for certain issues being implemented. Please view [issues labeled tip](
https://github.com/lucyparsons/OpenOversight/issues?q=is%3Aissue+is%3Aopen+label%3Atip) to see which contributions are eligible for tips. If you do not want a tip for that
contribution, just include "#notip" in your PR description. The amount of the tip depends on the size of the ticket: S ($20), M ($50), and L ($100). Tips are provided once your contribution is merged in (i.e. contributions must have the appropriate unit tests).

## Developer Quickstart

Make sure you have Docker installed and then:

```
git clone https://github.com/lucyparsons/OpenOversight.git
cd OpenOversight
make dev
```

And open `http://localhost:3000` in your favorite browser!

Please see [CONTRIB.md](/CONTRIB.md) for the full developer setup instructions.

## Documentation Quickstart

```
pip install -r dev-requirements.txt
make docs
```

## Deployment

Please see the [DEPLOY.md](/DEPLOY.md) file for deployment instructions.

## What data do I need to set up OpenOversight in my city?

* *Officer roster/assignment/demographic information*: You can often acquire a huge amount of information through FOIA:
  * Roster of all police officers (names, badge numbers)
  * Badge/star number history (if badge/star numbers change upon promotion)
  * Demographic information - race, gender, etc.
  * Assignments - what bureau, precinct/division and/or beat are they assigned to? When has this changed?
* *Clear images of officers with badge numbers and/or names displayed*: Scrape through social media (as we have done) and/or solicit submissions.
