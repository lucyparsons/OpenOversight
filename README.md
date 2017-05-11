![](docs/img/lpl-logo.png)

# OpenOversight [![Build Status](https://travis-ci.org/lucyparsons/OpenOversight.svg?branch=develop)](https://travis-ci.org/lucyparsons/OpenOversight) [![Coverage Status](https://coveralls.io/repos/github/lucyparsons/OpenOversight/badge.svg?branch=develop)](https://coveralls.io/github/lucyparsons/OpenOversight?branch=develop)

OpenOversight is a Lucy Parsons Labs project to improve police accountability through public and crowdsourced data. We maintain a database of police officer demographic information and provide digital galleries of photographs to help people identify police officers they would like to file a complaint on.

As a proof of concept, OpenOversight currently uses the Chicago Police Department but this infrastructure will be used to extent the project to other cities where it is needed. Interested in helping bring OpenOversight to your city? Email us at [info@lucyparsonslabs.com](mailto:info@lucyparsonslabs.com).  

This project is written and maintained by [@lucyparsonslabs](https://twitter.com/lucyparsonslabs) with collaboration, partnerships, and contributions welcome. If you would like to contribute code or documentation, please see our contributing guide. If you prefer to contribute in other ways, please submit images to our platform or talk to us about how to help sort and tag images. This project is in public beta, and we are currently soliciting photographs to add to the database.

## Note to Law Enforcement

Please contact our legal representation with requests, questions, or concerns of a legal nature by emailing [legal@lucyparsonslabs.com](mailto:legal@lucyparsonslabs.com). 

## Issues

Please use [our issue tracker](https://github.com/lucyparsons/OpenOversight//issues/new) to submit issues or suggestions. 

## Developer Quickstart

```
git clone https://github.com/lucyparsons/OpenOversight.git
cd OpenOversight
vagrant up
vagrant ssh
```

And open `http://localhost:3000` in your favorite browser!

If you need to log in, use the auto-generated test account
credentials:

```
Email: test@example.org
Password: testtest
```

Please see `CONTRIB.md` for the full developer setup instructions.

## Deployment

Please see the `DEPLOY.md` file for deployment instructions.

## What data do I need to set up OpenOversight in my city?

* *Officer roster/assignment/demographic information*: You can often acquire a huge amount of information through FOIA:
  * Roster of all police officers (names, badge numbers)
  * Badge/star number history (if badge/star numbers change upon promotion)
  * Demographic information - race, gender, etc.
  * Assignments - what bureau, precinct/division and/or beat are they assigned to? When has this changed? 
* *Clear images of officers with badge numbers and/or names displayed*: Scrape through social media (as we have done) and/or solicit submissions.
