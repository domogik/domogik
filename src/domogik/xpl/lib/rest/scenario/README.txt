Scenario are split in different level.
Basically, a scenario is something like :

if x 
    then y

'x' is the condition. A condition is a boolean expression like :

a AND (b OR c) AND d

a, b, c and d are called tests. They are basic checks than can be evaluated and return some boolean value.
Some simple exemple of conditions are :

- X10.A1 is ON
- text "foo" is in url http://bar.com/somepage

a test can is made of 3 parts :
 - a parameter
 - an 'operator'
 - another parameter

The parameters are basic "actions", for exemple :
 - fetch url
 - get last device state
 - get date/time

They can contains one or more token(s). For exemple, for the url parameter, you can have 2 tokens :
 - the url
 - an interval between 2 refresh

for the datetime, you could have the timezone, or the format, etc ...


Tokens are the most basic elements of a scenario. They can be anything a user will be able to fill (and so that the UI will be able to represent), for example :
 - text
 - operator (yes, the previous 'operator' can also be defined by a parameter)
 - device
 - date
 - ...


