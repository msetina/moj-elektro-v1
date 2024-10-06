Library to access MojElektro API v1
===================================

`MojElektro <https://mojelektro.si/login>`_ is web presence for electric energy distribution companies in Slovenija.

To authenticate to the web service API, user has to get access token. MojElektro's Profile page provides a button at the bottom to facilitate creation of access tokens.

Over the API a user can access data gathered by electricity company from smart meters and information about the electrical connection point. Different data attributes are described by meter_type endpoint represented by MeterType class. Smart meter data is accessible with electric energy access point identifier(Številka merilnega mesta). 


