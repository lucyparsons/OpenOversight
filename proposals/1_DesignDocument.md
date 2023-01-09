# Proposal 1: OpenOversight Design

1. [Goal](#goal)
2. [Motivations in Chicago](#motivations-in-chicago)
3. [Initial Build](#initial-build)
4. [Potential Extensions](#potential-extensions)
5. [Potential Issues and Ethical Concerns](#potential-issues-and-ethical-concerns)

# Goal

The application of surveillance technologies and FOIA to get a systematic view of police actions for citizen transparency, accountability and oversight.

We will be using Chicago as a prototype, but we will build this platform such that other cities can contribute to it and use it to hold their own police departments accountable.

# Motivations in Chicago

* Complaints are thrown away: A large fraction of complaints to the Chicago Police Department are thrown out because the police officer accused of misconduct cannot be identified. A complainant may not have provided the accused officers' badge number or name, but instead may have a picture or a description of what the officer looked like as well as where they were at a given time, but CPD is unable/unwilling to determine who that officer is. A public interface of police activity - for this concern, the officers identity and where they are active - would enable Chicago residents that are wronged by the police to be able to submit a complaint attributing their abuse to the correct individual.

# Initial Build

The platform will enable citizens to reconstruct a fuller picture of their police department. The initial build focuses on associating information about a police officer such as a photo of them with an identity.

## Components

### Backend Database

We will construct a database consisting of every officer in the Chicago Police Department.

We have already acquired the basic linking dataset through FOIA, which consists of:

* the name of each officer

* the rank of each officer

* the badge number of each officer (changes upon promotion so this will not be the primary key)

* the gender of each officer

* the race of each officer

* the hire date of each officer

This can be joined with salary information on the city of Chicago's open data portal to provide:

* the salary of each officer

In addition, for a subset of those officers that have received complaints we can link this data with the Invisible Institute's database to provide:

* the (incomplete) complaint and investigation history of some officers

We will be adding photos and facial recognition data to each officer.

### Frontend Web Application

We will build a web application that can be used to: submit new images for analysis (in "Submit Data") as well as search for new officers (in "Find a Chicago Police Officer")

#### Browse the Database

A user can manually page through the database and select an individual officer to examine.

#### Submit Data

Users should be able to submit images and videos (see "Data Collection" below) for review and inclusion into the database. For quality control purposes, images and videos should be reviewed to ensure the right officer is associated with each image. These reviews and classifications will be distributed to our users (see "Classify Images" below).

#### Classify Images

Landing page for those that wish to help us review (classification and verification) of images. We would require multiple users to check each image, and will have at least one trusted user examine each image. Consensus between trusted users accounts and untrusted user accounts will help establish which users could become trusted in the future. We could also have a public leaderboard to encourage users to participate and to reward those that contribute a significant amount of time to reviewing images (similarly for those who contribute a lot of training data).

#### Find a Chicago Police Officer

Initially, we can use demographic information that we have about each officer (approximate age, race, gender etc.) to filter down the full dataset.

Then we will generate a series of "digital galleries" that Chicago residents can use to try and determine which officer they interacted with. If a match is erroneously reported by a user and an officer is falsely accused of misconduct, CPD should be able to use its internal data sources to exonerate the officer.

In addition, after sufficient training data is procured, we can allow a user to submit an image of an officer and we can try to match the face with one in our database. If the test image is not of a police officer or cannot be matched, we can proceed with the "digital gallery".

### Machine Learning: Face Detection and Recognition

Upon the submission of an image in the "Find a Chicago Police Officer" page or upon the submission of a new training image, faces should be detected and extracted. Unless the image is sourced from social media, we will classify each new potential training image as uniformed police officer or non-uniformed individual. This work will be initially distributed to humans. When we can associate each face with an officer identity either due to the presence of their badge number / name in the photo or due to its sourcing in social media, we will link the image to the officer's profile.

Note that many images of each officer will be required in order to reliably perform facial recognition. We will probably use opencv or Tensor Flow to do the facial recognition itself.

## Data collection

* FOIA: CPD internally has at least 1 image of every officer. There are also photos of CPD events, graduation photos from police academy, etc. Many of these could be acquired through FOIA requests.

* Social media monitoring: Many officers we can collect images from by monitoring and capturing images from their social media profiles. This is a task that can be done manually to begin with. Users will facebook friend police officers, download every image with their face in it and submit them along with screenshots from Facebook's website for verification.

*  We can also scrape data from public accounts operated by the Chicago Police Department.

*  We will also want to solicit video and still images from the public. We can encourage people to submit any images they have, and we can also further build our training data by encouraging people to photograph police officers in the course of their duty.

### Possible data collection applications:

We rely on volunteers who will be taking images and videos of CPD officers and vehicles. Ideally these data would include as much metadata as possible, especially accurate GPS locations. In addition, the ideal application recording these data would immediately encrypt the recorded data and send it to an offsite server in case the recording device is tampered with or destroyed. We do not need all of these functions, and for most purposes regular cameras will suffice. However, here are some applications for smartphones that may be worth exploring that provide some of the above features:

* SWAT app: (potential collaboration?)
* InformaCam: Android application created by the Guardian project that annotates images and video with informative metadata including GPS location. Advantages are that it is already open-source. Disadvantages are that there is no Apple iOS version.

We may decide to fork one of these projects and extend it.

# Potential Extensions

Once we have built our user base, there are other data sources that we could integrate. Some issues are noted below in ethical concerns.

## Automatic License Plate Recognition

Use either cameras at fixed GPS coordinates or mobile cameras (e.g. in cars) which annotate video with GPS locations (i.e. with InformaCam) to log positions of Chicago Police Department vehicles.

Here we would use [openalpr](https://github.com/openalpr/openalpr) to run the license plate recognition backend.

## Social Media Monitoring

Scraping of officer content on Twitter / Facebook / LinkedIn.

# Potential issues and ethical concerns

* We are conducting mass surveillance of Chicago Police officers and people may take issue with that. This will probably be the brunt of the criticism, but they are public officers and as such the public is entitled to information about their activities for accountability and oversight. There is a serious lack of accountability of police actions in many cities including Chicago and a platform like this could be part of the solution.

* If this becomes controversial, there may be censorship of the services we use. This is something that we should consider as we proceed by selecting either services that are resistant to censorship or by enabling a rapid failover to another platform.

* Handling undercover police officers: We will need to consider how to handle officers that spend some or all of their time undercover.

* Privacy implications of geolocation mapping of police cars, e.g. "There was a police car parked outside Alice's house at midnight".

# History

redshiftzero v0.1 April 12, 2016
