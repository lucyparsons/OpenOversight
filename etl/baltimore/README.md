## BPD Roster ETL

We currently make a Maryland Public Information Act (MPIA) request approximately quarterly using the following language:
```
I am requesting for every sworn Baltimore City Police Officer, in a machine readable format (in an Excel speadsheet would be fine), as of April 1, 2018:

* First and last name
* Unique sequence number
* Current badge number
* Any previously recorded badge number that was used before their current one
* Race
* Gender
```

An example request can be [found here](https://www.muckrock.com/foi/baltimore-315/bpd-officer-records-52459/), including a [sample raw data set](https://cdn.muckrock.com/foia_files/2018/05/11/Active_employees_as_of_May_3_2018.xlsx).

The data can be processed and imported into the schema expected by OpenOversight by running `python roster_import.py`.
