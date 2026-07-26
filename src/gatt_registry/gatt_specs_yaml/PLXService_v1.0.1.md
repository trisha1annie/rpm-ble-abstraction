

Bluetooth SIG Proprietary
## Bluetooth
## ®
## Service Specification
▪Revision: v1.0.1
▪Revision Date: 2022-01-18
▪Group Prepared By:  Medical Devices Working Group
## Abstract:
This Service specification defines a pulse oximetry sensor for use in consumer and professional healthcare
applications.
## Pulse Oximeter Service

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 2 of 31
## Revision History
## Revision Number
## Date
## (yyyy-mm-dd)
## Comments
v1.0.0 2015-07-14 Approved by the Bluetooth SIG BoD
v1.0.1 2022-01-18 Adopted by the Bluetooth SIG Board of Directors.
## Version History
## Versions Changes
v1.0.0 to v1.0.1 Incorporated errata E16248, E16249, E17517, E17997.
## Acknowledgments
## Name Company
## Jordan Hartmann Nonin Medical, Inc.
## Matthew Leipnitz Nonin Medical, Inc.
## Wolfgang Heck Roche
Leif-Alexandre Aschehoug Nordic Semiconductor


## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 3 of 31
Use  of  this  specification  is  your  acknowledgement  that  you  agree  to  and  will  comply  with  the  following  notices  and
disclaimers.  You  are  advised  to  seek  appropriate  legal,  engineering,  and  other  professional  advice  regarding  the  use,
interpretation, and effect of this specification.
Use of Bluetooth specifications by members of Bluetooth SIG is governed by the membership and other related agreements
between  Bluetooth  SIG  and  its  members,  including  those  agreements  posted  on  Bluetooth  SIG’s  website  located  at
www.bluetooth.com. Any use of this specification by a member that is not in compliance with the applicable membership
and  other  related  agreements  is  prohibited  and,  among  other  things,  may  result  in  (i)  termination  of  the  applicable
agreements  and  (ii)  liability  for  infringement  of  the  intellectual  property  rights  of  Bluetooth  SIG  and  its  members. This
specification may provide options, because, for example, some products do not implement every portion of the specification.
All  content  within  the  specification,  including  notes,  appendices,  figures,  tables,  message  sequence  charts,  examples,
sample  data,  and  each  option  identified  is  intended  to  be  within  the  bounds  of  the  Scope  as  defined  in  the  Bluetooth
Patent/Copyright  License  Agreement  (“PCLA”).  Also,  the  identification  of  options  for  implementing  a  portion  of  the
specification  is  intended  to  provide  design  flexibility  without  establishing,  for  purposes  of  the  PCLA,  that  any  of  these
options is a “technically reasonable non-infringing alternative.”
Use  of  this  specification  by  anyone  who  is  not  a  member  of  Bluetooth  SIG  is  prohibited  and  is  an  infringement  of  the
intellectual property rights of Bluetooth SIG and its members. The furnishing of this specification does not grant any license
to any intellectual property of Bluetooth SIG or its members. THIS SPECIFICATION IS PROVIDED “AS IS” AND BLUETOOTH
SIG,  ITS  MEMBERS  AND  THEIR  AFFILIATES  MAKE  NO  REPRESENTATIONS  OR  WARRANTIES  AND  DISCLAIM  ALL
WARRANTIES,   EXPRESS   OR   IMPLIED,   INCLUDING   ANY   WARRANTIES   OF   MERCHANTABILITY,   TITLE,   NON-
INFRINGEMENT, FITNESS FOR ANY PARTICULAR PURPOSE, OR THAT THE CONTENT OF THIS SPECIFICATION IS FREE
OF ERRORS. For the avoidance of doubt, Bluetooth SIG has not made any search or investigation as to third parties that
may claim rights in or to any specifications or any intellectual property that may be required to implement any specifications
and it disclaims any obligation or duty to do so.
TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, BLUETOOTH SIG, ITS MEMBERS AND THEIR AFFILIATES
DISCLAIM  ALL  LIABILITY  ARISING  OUT  OF  OR  RELATING  TO  USE  OF  THIS  SPECIFICATION  AND  ANY  INFORMATION
CONTAINED  IN  THIS  SPECIFICATION,  INCLUDING  LOST  REVENUE,  PROFITS,  DATA  OR  PROGRAMS,  OR  BUSINESS
INTERRUPTION,  OR  FOR  SPECIAL,  INDIRECT,  CONSEQUENTIAL,  INCIDENTAL  OR  PUNITIVE  DAMAGES,  HOWEVER
CAUSED  AND  REGARDLESS  OF  THE  THEORY  OF  LIABILITY,  AND  EVEN  IF  BLUETOOTH  SIG,  ITS  MEMBERS  OR  THEIR
## AFFILIATES HAVE BEEN ADVISED OF THE POSSIBILITY OF THE DAMAGES.
Products  equipped  with  Bluetooth  wireless  technology  ("Bluetooth  Products")  and their  combination,  operation,  use,
implementation,  and  distribution  may  be  subject  to  regulatory  controls  under  the  laws  and  regulations  of  numerous
countries   that   regulate   products   that   use   wireless   non-licensed   spectrum.   Examples   include   airline   regulations,
telecommunications regulations, technology transfer controls, and health and safety regulations. You are solely responsible
for  complying  with  all  applicable  laws  and  regulations  and  for  obtaining  any  and  all  required  authorizations,  permits,  or
licenses  in  connection  with  your  use  of  this  specification  and  development,  manufacture,  and  distribution  of  Bluetooth
Products. Nothing in this specification provides any information or assistance in connection with complying with applicable
laws or regulations or obtaining required authorizations, permits, or licenses.
Bluetooth SIG is not required to adopt any specification or portion thereof. If this specification is not the final version adopted
by Bluetooth SIG’s Board of Directors, it may not be adopted. Any specification adopted by Bluetooth SIG’s Board of
Directors  may  be  withdrawn,  replaced,  or  modified  at  any  time.  Bluetooth  SIG  reserves  the  right  to  change  or  alter  final
specifications in accordance with its membership and operating agreements.
Copyright © 2013–2022. All copyrights in the Bluetooth Specifications themselves are owned by Apple Inc., Ericsson AB,
Intel  Corporation,  Lenovo (Singapore)  Pte.  Ltd.,  Microsoft  Corporation,  Nokia  Corporation,  and  Toshiba  Corporation. The
Bluetooth word mark and logos are owned by Bluetooth SIG, Inc. Other third-party brands and names are the property of
their respective owners.


## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 4 of 31
## Document Terminology
The Bluetooth SIG has adopted portions of the IEEE Standards Style Manual, which dictates use of the
words “shall”, “should”, “may”, and “can” in the development of documentation, as follows:
The word shall is used to indicate mandatory requirements strictly to be followed in order to conform to
the standard and from which no deviation is permitted (shall equals is required to).
The use of the word must is deprecated and shall not be used when stating mandatory requirements;
must is used only to describe unavoidable situations.
The use of the word will is deprecated and shall not be used when stating mandatory requirements; will is
only used in statements of fact.
The word should is used to indicate that among several possibilities one is recommended as particularly
suitable, without mentioning or excluding others; or that a certain course of action is preferred but not
necessarily required; or that (in the negative form) a certain course of action is deprecated but not
prohibited (should equals is recommended that).
The word may is used to indicate a course of action permissible within the limits of the standard (may
equals is permitted).
The word can is used for statements of possibility and capability, whether material, physical, or causal
(can equals is able to).
The term Reserved for Future Use (RFU) is used to indicate Bluetooth SIG assigned values that are
reserved by the Bluetooth SIG and are not otherwise available for use by implementations.


## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 5 of 31
## Contents
Document Terminology .............................................................................................................................. 4
1 Introduction ........................................................................................................................................... 7
1.1 Conformance ................................................................................................................................ 7
1.2 Service Dependencies .................................................................................................................. 7
1.3 Bluetooth Specification Release Compatibility ............................................................................. 7
1.4 GATT Sub-Procedure Requirements ............................................................................................ 7
1.5 Transport Dependencies .............................................................................................................. 7
1.6 Application Error Codes ................................................................................................................ 8
1.7 Byte Transmission Order .............................................................................................................. 8
2 Service Requirements .......................................................................................................................... 9
2.1 Declaration .................................................................................................................................... 9
3 Characteristic Behaviors ................................................................................................................... 10
3.1 PLX Spot-Check Measurement .................................................................................................. 10
3.1.1 Characteristic Behavior: ........................................................................................................................ 11
3.1.1.1 Flags Field ....................................................................................................................................... 12
3.1.1.2 SpO2PR-Spot-Check Field .............................................................................................................. 13
3.1.1.3 Timestamp Field .............................................................................................................................. 13
3.1.1.4 Measurement Status Field ............................................................................................................... 13
3.1.1.5 Device and Sensor Status Field ...................................................................................................... 14
3.1.1.6 Pulse Amplitude Index ..................................................................................................................... 15
3.2 PLX Continuous Measurement Characteristic ............................................................................ 15
3.2.1 Characteristic Behavior ......................................................................................................................... 16
3.2.1.1 Flags Field ....................................................................................................................................... 16
3.2.1.2 SpO2PR-Normal Field ..................................................................................................................... 17
3.2.1.3 SpO2PR-Fast Field ......................................................................................................................... 17
3.2.1.4 SpO2PR-Slow Field ......................................................................................................................... 17
3.2.1.5 Measurement Status Field ............................................................................................................... 18
3.2.1.6 Device and Sensor Status Field ...................................................................................................... 18
3.2.1.7 Pulse Amplitude Index ..................................................................................................................... 18
3.3 PLX Features .............................................................................................................................. 19
3.3.1 Characteristic Behavior ......................................................................................................................... 19
3.3.1.1 Supported Features Field ................................................................................................................ 19
3.3.1.2 Measurement Status Support Field ................................................................................................. 22
3.3.1.3 Device and Sensor Status Support Field ......................................................................................... 22
3.4 Record Access Control Point ...................................................................................................... 23
3.4.1 Record Definition .................................................................................................................................. 23
3.4.2 RACP Procedure Requirements ........................................................................................................... 23
3.4.3 Record Access Control Point Behavioral Description ........................................................................... 24
3.4.4 Report Stored Records Procedure ........................................................................................................ 24
3.4.5 Delete Stored Records procedure ......................................................................................................... 25
3.4.6 Abort Operation procedure ................................................................................................................... 25
3.4.7 Report Number of Stored Records procedure ...................................................................................... 25
3.4.8 RACP Specific Errors ............................................................................................................................ 26
3.4.9 Procedure Timeout and Failure ............................................................................................................ 26
3.5 Requirements for Time-Sensitive Data ....................................................................................... 27

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 6 of 31
4 SDP interoperability ........................................................................................................................... 28
5 Special Values ..................................................................................................................................... 29
5.1 Special Short Float Value ........................................................................................................... 29
6 Acronyms and abbreviations ............................................................................................................ 30
7 References .......................................................................................................................................... 31


## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 7 of 31
## 1 Introduction
The Pulse Oximeter (PLX) Service exposes pulse oximetry data related to a non-invasive pulse oximetry
sensor for consumer and professional healthcare applications.
## 1.1 Conformance
If a device claims conformance to this specification, all capabilities indicated as mandatory for this
specification shall be supported in the specified manner (process-mandatory). This also applies for all
optional and conditional capabilities for which support is indicated.
## 1.2 Service Dependencies
This service is not dependent upon any other services.
## 1.3 Bluetooth Specification Release Compatibility
This specification is compatible with any Bluetooth Core Specification [1] that includes the Generic
Attribute Profile (GATT) portion of the core specification.
1.4 GATT Sub-Procedure Requirements
Requirements in this section represent a minimum set of requirements for a Pulse Oximeter Sensor
(GATT Server). Other GATT sub-procedures may be used if supported by both Client and Server.
Table 1.1 summarizes additional GATT sub-procedure requirements beyond those required by all GATT
## Servers.
GATT Sub-Procedure Requirements
## Write Characteristic Value C.1
## Notifications C.2
## Indications C.3
## Read Characteristic Descriptors M
## Write Characteristic Descriptors M
Table 1.1: Additional GATT Sub-Procedure Requirements
C.1:  Mandatory if spot-check measurement storage is supported, otherwise optional.
C.2:  Mandatory if the PLX Continuous Measurement characteristic is supported, otherwise optional.
C.3:  Mandatory if the PLX Spot-check Measurement characteristic is supported, otherwise optional.
## 1.5 Transport Dependencies
This service may operate over the LE or BR/EDR transports.
Where the term BR/EDR is used throughout this document, this also includes the optional use of AMP.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 8 of 31
## 1.6 Application Error Codes
This service does not define any Attribute Protocol Application Error codes.
## 1.7 Byte Transmission Order
All characteristics used with this service shall be transmitted with the least significant octet first (i.e. little
endian). The least significant octet is identified in the characteristic definitions in [2] and where
characteristics are defined in Section 3.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 9 of 31
## 2 Service Requirements
## 2.1 Declaration
The Pulse Oximeter Service is recommended to be instantiated as a «Primary Service».
The service UUID shall be set to the UUID value assigned to «Pulse Oximeter Service» defined in [2].

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 10 of 31
## 3 Characteristic Behaviors
This section describes the behaviors associated with each of the characteristics that make up the service.
The characteristic requirements in an instance of the Pulse Oximeter Service are shown in Table 3.1.
Unless otherwise specified, only one instance of each characteristic is permitted within this service.
## Characteristic
## Name
## Requirement
## Mandatory
## Properties
## Optional
## Properties
## Security
## Permissions
PLX Spot-check
## Measurement
## C.1 Indicate

## None
PLX Continuous
## Measurement
## C.1 Notify

## None
PLX Features M Read Indicate C.3 None
## Record Access
## Control Point
## C.2
## Indicate,
## Write

## None
## Table 3.1: Pulse Oximeter Service Characteristics
C.1: Mandatory to support at least one of these characteristics.
C.2: Mandatory if measurement storage is supported for Spot-check measurements.
C.3: The Indicate property shall be supported for the PLX Features characteristic if the device
supports bonding and if the value of the PLX Features characteristic can change over the lifetime
of the device, otherwise Excluded for this service.
Note 1: Properties not listed as Mandatory or Conditional are Excluded.
Note 2: Security Permissions of “None” means that this service does not impose any requirements.
Note 3: Where a characteristic can be indicated and/or notified, a Client Characteristic Configuration
descriptor shall be included in that characteristic as required by the Core Specification [1].
3.1 PLX Spot-Check Measurement
The PLX Spot-check Measurement characteristic, if supported, shall be used to send Spot-check
measurements of SpO2 (Percent oxygen saturation of hemoglobin) and PR (pulse rate).
Included in the characteristic are the Flags field, the SpO2PR-Spot-Check field, and depending on the
contents of the Flags field, the Timestamp field, the Measurement Status field, the Device and Sensor
Status field, and/or the Pulse Amplitude Index field. These fields are shown in Table 3.2.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 11 of 31
## LSO MSO
## Flags
SpO2PR-Spot-Check
## Timestamp
(if present)
## Measurement
## Status
(if present)
## Device
and
## Sensor
## Status
## (if
present)
## Pulse Amplitude
Index (if present)
SpO2 PR
## Octet
## Order
## N/A LSO..MSO LSO..MSO LSO..MSO LSO..MSO LSO..MSO LSO..MSO
## Data
## Type
8bit SFLOAT SFLOAT
Date time
characteristic,
Defined in [2]
16bit 24bit SFLOAT
## Size
## 1
octet
2 octets 2 octets 0 or 7 octets 0 or 2 octets
0 or 3
octets
0 or 2 octets
## Units None Percentage
period (beats
per minute)
Smallest unit in
seconds
## None None Percentage
Table 3.2: PLX Spot-check Measurement Characteristic fields
Where LSO = Least Significant Octet and MSO = Most Significant Octet
## 3.1.1 Characteristic Behavior:
The PLX Spot-check Measurement characteristic is identified using the UUID «PLX Spot-check
## Measurement»
## Measurement Generation:
A Spot-check measurement is a single measurement that is generated once per measurement session to
give a discrete reading of a patient’s oximetry status. In the context of this service, a measurement
session is the entire time the device is ‘on’, e.g. the entire time it is attempting to take measurements, or
the entire time power is applied to the pulse oximeter, etc.
For example, a typical Spot-check measurement scenario is that the user would place a pulse oximeter
on their finger, the oximeter would start acquiring measurements, and once the measurement results
were stable, it would send one oximetry measurement indication to the user’s smartphone. The user
would then remove the oximeter from their finger.
The amount of time an oximeter takes to generate a stable measurement varies by implementation.
Some oximeters will use the first measurement the sensor can get, whereas others will use a fixed
stabilization period, and others use more complex algorithms.
A measurement that is considered stable can also be considered ‘fully qualified’, meaning that the
measurement has met all implementation-specific criteria for stability and/or quality. The server shall
indicate this condition using the “Fully Qualified Data” bit in the Measurement Status field of the
characteristic value (see Section 3.1.1.4) if the field and bit is supported.
If the pulse oximeter cannot generate a stable, fully qualified measurement due to physiological or
environmental factors, the Server may indicate this characteristic after a timeout instead (typically about
40 seconds - the timeout period is left to the implementation).

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 12 of 31
## New Measurement:
This characteristic shall indicate a ‘new’ measurement once per measurement session.
When a spot-check measurement has been generated and if a connection is not currently established,
the Server shall become connectable to allow the Client to create a link.
If the new measurement is not transmitted successfully to a Client during the measurement session (such
as when a connection is never made or the characteristic cannot be successfully indicated while in a
connection), and the Server supports measurement storage, the measurement shall be temporarily stored
for later transmission using the Record Access Control Point’s (RACP’s) Report Stored Records
Procedure (see Section 3.4.4). If measurement storage is not supported, the Server shall discard the
measurement at the end of the measurement session. A measurement shall only be successfully
transmitted once.
If the PLX Continuous Measurement characteristic (see Section 3.2) is not supported or is not configured
for notifications (i.e. the characteristic is not being used), the Server may end the connection once the
new Spot-check measurement has been indicated. However, the Server should remain connected for at
least 15 seconds to allow a Client to perform any needed RACP procedures on the Server or interact with
any other services that perform actions such as setting the time.
The PLX Spot-check Measurement characteristic contains time-sensitive data, thus the requirements for
time-sensitive data and data storage defined in Section 3.5 apply.
If the new measurement is generated by the Server while a Report Stored Records Procedure is in
progress, the new measurement shall be indicated after the procedure has been completed.
## Stored Measurements:
The Server shall transmit stored measurements using the Report Stored Records Procedure (see Section
## 3.4.4).
## 3.1.1.1 Flags Field
The Flags field shall be included in the PLX Spot-check Measurement characteristic.
The Flags field is an 8-bit bit field which indicates what fields are present in the PLX Spot-check
Measurement Characteristic value. This field also indicates if the clock was not set for the measurement
being reported.
Reserved for Future Use (RFU) bits in the Flags field shall be set to 0.
The format of the Flags field is defined in Table 3.3:
## Bit Definition
0 Timestamp field is present
1 Measurement Status field is present
2 Device and Sensor Status field is present
3 Pulse Amplitude Index field is present

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 13 of 31
## Bit Definition
4 Device Clock is Not Set
5-7 Reserved for Future Use
Table 3.3: PLX Spot-check Measurement Characteristic Flags
3.1.1.2 SpO2PR-Spot-Check Field
The SpO2PR-Spot-Check field shall be included in the PLX Spot-check Measurement characteristic.
The SpO2PR-Spot-Check field is composed of two subfields: SpO2 and PR (pulse rate).
If a value for SpO2 or PR is unavailable (e.g. due to a measurement or device error), the special short
float value NaN (Not a Number) (see Section 5.1) shall be used in the unavailable subfield(s).
## 3.1.1.3 Timestamp Field
The Timestamp field shall be included in the PLX Spot-check Measurement characteristic if the Server
supports storing Spot-check measurements. Otherwise, it is optional.
If the Timestamp field is supported, the Server shall set the “Timestamp field is present” bit of the Flags
field to 1 and include the Timestamp field. If the Timestamp is not supported, the Server shall set the
“Timestamp field is present” bit of the Flags field to 0 and not include the Timestamp field.
The date and time of the device may be updated by various means such as via a simple user interface on
the device, via an external time service, etc.
The time stamp shall use the same format as the Date Time characteristic defined in [2].
## 3.1.1.4 Measurement Status Field
If the Measurement Status field is present in the PLX Spot-check Measurement characteristic, the
“Measurement Status field is present“ bit of the Flags field shall be set to 1; otherwise it shall be set to 0.
Reserved for Future Use (RFU) bits in the Measurement Status field shall be set to 0.
Support for each bit of the Measurement Status field is specified in the PLX Features characteristic’s
Measurement Status Support field (see Section 3.3.1.2). If the bit is not supported, it shall always be set
to 0 in the Measurement Status field of this characteristic.
For any bit that is supported, a value of 1 shall indicate that the status the bit reports is true, and 0 shall
indicate false.
Each supported bit is mapped directly to the MeasurementStatus attribute in ISO/IEEE 11073-20601 [3],
with two exceptions. This allows for easy transcoding and common definitions (see [5]).
The exceptions are two additional bits that add useful information to the field in this specification
- The “Data from Measurement Storage” bit is used to indicate that the measurement is a temporarily
stored measurement.
- The “Fully Qualified Data” bit is used to indicate that the measurement meets the “fully qualified”
criteria described in Section 3.1.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 14 of 31
The format of the Measurement Status field is defined in Table 3.4.
## Bit Definition
0-4 Reserved for Future Use
## 5 Measurement Ongoing
## 6 Early Estimated Data
## 7 Validated Data
## 8 Fully Qualified Data
9 Data from Measurement Storage
10 Data for Demonstration
11 Data for Testing
## 12 Calibration Ongoing
## 13 Measurement Unavailable
## 14 Questionable Measurement Detected
## 15 Invalid Measurement Detected
Table 3.4: Measurement Status definitions
3.1.1.5 Device and Sensor Status Field
If the Device and Sensor Status field is present in the PLX Spot-check Measurement characteristic, the
“Device and Sensor Status field is present” bit of the Flags field shall be set to 1; otherwise it shall be set
to 0.
Reserved for Future Use (RFU) bits in the Device and Sensor Status field shall be set to 0.
Support for each bit of the Device and Sensor Status field is specified in the PLX Features characteristic’s
Device and Sensor Status Support field (see Section 3.3.1.3). If the bit is not supported, it shall always be
set to 0 in the Device and Sensor Status field of this characteristic.
For any bit that is supported, a value of 1 shall indicate that the status the bit reports is true, and 0 shall
indicate false.
Each supported bit is mapped directly to the Device and Sensor Status attribute in ISO/IEEE 11073-
10404 [4]. This allows for easy transcoding and common definitions.
The format of the Device and Sensor Status field is defined in Table 3.5.
## Bit  Definition
## 0 Extended Display Update Ongoing
## 1 Equipment Malfunction Detected

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 15 of 31
## Bit  Definition
## 2 Signal Processing Irregularity Detected
## 3 Inadequate Signal Detected
## 4 Poor Signal Detected
## 5 Low Perfusion Detected
## 6 Erratic Signal Detected
7 Non-Pulsatile Signal Detected
## 8 Questionable Pulse Detected
## 9 Signal Analysis Ongoing
## 10 Sensor Interference Detected
11 Sensor Unconnected to User
## 12 Unknown Sensor Connected
## 13 Sensor Displaced
## 14 Sensor Malfunctioning
## 15 Sensor Disconnected
16-23 Reserved for Future Use
Table 3.5: Device and Sensor Status definitions
## 3.1.1.6 Pulse Amplitude Index
The Pulse Amplitude Index is a percentage indicator indicating the perfusion level (amount of blood being
delivered to the capillary bed) of a user.
If the Pulse Amplitude Index field is present in the PLX Spot-check Measurement characteristic, “Pulse
Amplitude Index field is present” bit of the Flags field shall be set to 1; otherwise it shall be set to 0.
If a value for the pulse amplitude index is unavailable (e.g. due to a measurement or device error), the
special short float value NaN (see Section 5.1) shall be used in the unavailable subfield(s).
3.2 PLX Continuous Measurement Characteristic
The PLX Continuous Measurement characteristic, if supported, shall be used to send periodic pulse
oximetry measurements.
Included in the characteristic are the Flags field (to indicate presence of optional fields), the SpO2PR-
Normal field, and depending on the contents of the Flags field, the SpO2PR-Fast field, the SpO2PR-Slow
field, the Measurement Status field, the Device and Sensor Status field, and/or the Pulse Amplitude Index
field.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 16 of 31
## LSO

## Flags
SpO2PR-Normal
SpO2PR-Fast
(if present)
SpO2PR-Slow
(if present)


SpO2 PR SpO2 PR SpO2 PR
## Octet
## Order
## N/A LSO..MSO LSO..MSO LSO..MSO LSO..MSO LSO..MSO LSO..MSO
## Data
## Type
8bit SFLOAT SFLOAT SFLOAT SFLOAT SFLOAT SFLOAT
## Size
## 1
octet
2 octets 2 octets
0 or 2
octets
0 or 2 octets
0 or 2
octets
0 or 2 octets
## Units
## None Percentage
period (beats per
minute)
## Percentage
period (beats per
minute)
## Percentage
period (beats per
minute)

## MSO

## Measurement
## Status
(if present)
Device and
## Sensor Status
(if present)
## Pulse Amplitude Index
(if present)
## Octet
## Order
## LSO..MSO LSO..MSO LSO...MSO
## Data
## Type
16bit 24bit SFLOAT
## Size
0 or 2 octets 0 or 3 octets 0 or 2 octets
## Units
## None None Percentage
Table 3.6: PLX Continuous Measurement Characteristic fields
Where LSO = Least Significant Octet, MSO = Most Significant Octet and PR = Pulse Rate
## 3.2.1 Characteristic Behavior
A Continuous measurement is a periodically updated oximetry measurement that is generated repeatedly
until a connection is terminated, typically sending a notification at a period of 1-4 seconds.
The PLX Continuous Measurement Characteristic is identified using the UUID «PLX Continuous
Measurement», as defined in [2]. When the Client Characteristic Configuration descriptor is configured for
notifications, this characteristic shall be notified periodically while in a connection.
The notifications of this characteristic are meant to be transmitted immediately, and no timestamping or
temporary storage is provided by this service (also see Section 3.5).
If a notification is available and a connection is not currently established, the Server should become
connectable to allow the Client to create a link.
## 3.2.1.1 Flags Field
The Flags field shall be included in the PLX Continuous Measurement characteristic.
The Flags field is an 8-bit bit field which indicates what fields are present in the PLX Continuous
Measurement Characteristic value.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 17 of 31
Reserved for Future Use (RFU) bits in the Flags field shall be set to 0.
The format of the Flags field is defined in Table 3.7.
## Bit Definition
0 SpO2PR–Fast field is present
1 SpO2PR-Slow field is present
2 Measurement Status field is present
3 Device and Sensor Status field is present
4 Pulse Amplitude Index field is present
5-7 Reserved for Future Use
Table 3.7: PLX Continuous Measurement Characteristic Flags
3.2.1.2 SpO2PR-Normal Field
The SpO2PR-Normal field shall be included in the PLX Continuous Measurement characteristic.
The SpO2PR-Normal field is composed of two subfields: SpO2 and PR (pulse rate).
If a value for SpO2 or PR is unavailable (e.g. due to a measurement or device error), the special short
float value NaN (see Section 5.1) shall be used in the unavailable subfield(s).
3.2.1.3 SpO2PR-Fast Field
The SpO2PR-Fast field shall be included in the PLX Continuous Measurement characteristic if the Server
supports the SpO2PR-Fast metric; otherwise, it shall be excluded.
The SpO2PR-Fast field is composed of two subfields: SpO2 and PR (pulse rate).
If the SpO2PR-Fast field is present in the PLX Continuous Measurement characteristic, the “SpO2PR–
Fast field is present” bit of the Flags field shall be set to 1; otherwise it shall be set to 0 and the SpO2PR-
Fast field shall not be present.
The SpO2PR-Fast field reports fast responding oximetry measurements of the sensor. Signal processing
algorithms better at highlighting quick changes in oximetry data are typically used to generate this data.
If a value for fast responding SpO2 or PR is unavailable (e.g. due to a measurement or device error), the
special short float value NaN (see Section 5.1) shall be used in the unavailable subfield(s).
3.2.1.4 SpO2PR-Slow Field
The SpO2PR-Slow field shall be included in the PLX Continuous Measurement characteristic if the Server
supports the SpO2PR-Slow metric; otherwise, it shall be excluded.
The SpO2PR-Slow field is composed of two subfields: SpO2 and PR (pulse rate).

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 18 of 31
If the SpO2PR-Slow field is present in the PLX Continuous Measurement characteristic, the “SpO2PR–
Slow field is present” bit of the Flags field shall be set to 1; otherwise it shall be set to 0 and the SpO2PR-
Slow field shall not be present.
The SpO2PR-Slow field reports slow responding oximetry measurements of the sensor. Signal
processing algorithms better at eliminating changes to oximetry measurements due to motion are typically
used to generate this data.
If a value for slow responding SpO2 or PR is unavailable (e.g. due to a measurement or device error), the
special short float value NaN (see Section 5.1) shall be used in the unavailable subfield(s).
## 3.2.1.5 Measurement Status Field
The Measurement Status field shall be included in the PLX Continuous Measurement characteristic if the
device supports measurement status flags; otherwise, it shall be excluded.
If the Measurement Status field is present in the PLX Continuous Measurement characteristic, the
“Measurement Status field is present” bit of the Flags field shall be set to 1; otherwise it shall be set to 0
and the Measurement Status field shall not be present.
Reserved for Future Use (RFU) bits in the Measurement Status field shall be set to 0.
Support for each bit of the Measurement Status field is specified in the PLX Features characteristic’s
Measurement Status Support field (see Section 3.3.1.2). If the bit is not supported, it shall always be set
to 0 in the Measurement Status field of this characteristic.
The Measurement Status bit definitions are the same as in Section 3.1.1.4.
3.2.1.6 Device and Sensor Status Field
The Device and Sensor Status field shall be included in the PLX Continuous Measurement characteristic
if the device supports device and sensor status flags; otherwise, it shall be excluded.
If the Device and Sensor Status field is present in the PLX Continuous Measurement characteristic, the
“Device and Sensor Status field is present” bit of the Flags field shall be set to 1; otherwise it shall be set
to 0 and the Device and Sensor Status field shall not be present.
Reserved for Future Use (RFU) bits in the Device and Sensor Status field shall be set to 0.
Support for each bit of the Device and Sensor Status field is specified in the PLX Features characteristic’s
Device and Sensor Status Support field (see Section 3.3.1.3). If the bit is not supported, it shall always be
set to 0 in the Device and Sensor Status field of this characteristic.
The Device and Sensor Status bit definitions are the same as in Section 3.1.1.5.
## 3.2.1.7 Pulse Amplitude Index
The Pulse Amplitude Index field shall be included in the PLX Continuous Measurement characteristic if
the device supports the Pulse Amplitude Index field, otherwise it shall be excluded.
If the Pulse Amplitude Index field is present in the PLX Continuous Measurement characteristic, “Pulse
Amplitude Index field is present” bit of the Flags field shall be set to 1; otherwise it shall be set to 0.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 19 of 31
If a value for the pulse amplitude index is unavailable (e.g. due to a measurement or device error), the
special short float value NaN (see Section 5.1) shall be used in the unavailable subfield(s).
3.3 PLX Features
The PLX Features characteristic shall be used to describe the supported features of the Server.
Support for this characteristic is mandatory.
The PLX Features Characteristic is identified using the UUID «PLX Features», as defined in [2].
Included in the characteristic is a PLX Features field, and, depending on the contents of the PLX Features
field, the Measurement Status Support field, and the Device and Sensor Status Support field. These fields
are shown in Table 3.8.
## LSO MSO

## Supported
## Features
## Measurement
## Status Support
(if present)
Device and
## Sensor Status
## Support
(if present)
## Octet
## Order
## LSO..MSO LSO..MSO LSO..MSO
## Data
## Type
## 16bit 16bit 24bit
Size 2 octets 0 or 2 octets 0 or 3 octets
## Units None None None
Table 3.8: PLX Features Characteristic fields
## 3.3.1 Characteristic Behavior
When read or indicated, the PLX Features characteristic returns a value that is used by a Client to
determine the supported features of the Server.
The PLX Features characteristic shall be static during a connection.
When the Client Characteristic Configuration descriptor is configured for indications and the supported
features of the Server have changed, the PLX Features characteristic shall be indicated to any bonded
Collectors after reconnection.
## 3.3.1.1 Supported Features Field
The Supported Features field shall be included in the PLX Features characteristic.
The Supported Features field is a 16-bit bit field which indicates feature support as well as what fields are
present in the PLX Features characteristic.
Reserved for Future Use (RFU) bits in the Supported Features field shall be set to 0.
The format of the Supported Features field is defined in Table 3.9:

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 20 of 31
## Bit Definition
0 Measurement Status support is present
1 Device and Sensor Status support is present
## 2
Measurement Storage for Spot-check measurements is
supported
3 Timestamp for Spot-check measurements is supported
4 SpO2PR-Fast metric is supported
5 SpO2PR-Slow metric is supported
6 Pulse Amplitude Index field is supported
## 7 Multiple Bonds Supported
8-15 Reserved for Future Use
## Table 3.9: Supported Features Field
## 3.3.1.1.1 Measurement Status Support Bit:
If the “Measurement Status Supported” bit is set to 1:
- The Measurement Status feature is supported.
- The Measurement Status Support field in this characteristic shall be present.
- The Measurement Status field shall be present when the PLX Spot-check Measurement
characteristic is indicated.
- The Measurement Status field shall be present when the PLX Continuous Measurement
characteristic is notified.
If the “Measurement Status Supported” bit is set to 0:
- The Measurement Status feature is not supported.
- The Measurement Status Support field in this characteristic shall not be present.
- The Measurement Status field shall not be present when the PLX Spot-check Measurement
characteristic is indicated.
- The Measurement Status field shall not be present when the PLX Continuous Measurement
characteristic is notified.
3.3.1.1.2 Device and Sensor Status Support Bit:
If the “Device and Sensor Status Supported” bit is set to 1:
- The Device and Sensor Status Feature is supported.
- The Device and Sensor Status Support field in this characteristic shall be present.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 21 of 31
- The Device and Sensor Status field shall be present when the PLX Spot-check Measurement
characteristic is indicated.
- The Device and Sensor Status field shall be present when the PLX Continuous Measurement
characteristic is notified.
If the “Device and Sensor Status Supported” bit is set to 0:
- The Device and Sensor Status feature is not supported.
- The Device and Sensor Status Support field in this characteristic shall not be present.
- The Device and Sensor Status field shall not be present when the PLX Spot-check Measurement
characteristic is indicated.
- The Device and Sensor Status field shall not be present when the PLX Continuous Measurement
characteristic is notified.
3.3.1.1.3 Measurement Storage for Spot-check measurements is supported Bit:
If the “Measurement Storage for Spot-check measurements is supported” bit is set to 1:
- The Record Access Control Point characteristic shall be present.
- The PLX Spot-check Measurement characteristic shall include the timestamp field when it is
indicated.
- The “Timestamp for Spot-check measurements is supported” bit in this field shall be set to 1.
- The Server shall have a means of setting its clock.
If the “Measurement Storage for Spot-check measurements is supported” bit is set to 0:
- The Server shall not store Spot-check measurements.
## 3.3.1.1.4 Other Bits:
If the “Timestamp for Spot-check measurements is supported” bit is set to 1, the Timestamp field shall be
included when the PLX Spot-check Measurement characteristic is indicated, otherwise it shall not be
present.
If the “SpO2PR-Fast metric is supported” bit is set to 1, the SpO2PR-Fast metric shall be included when
the PLX Continuous Measurement characteristic is notified, otherwise it shall not be present.
If the “SpO2PR-Slow metric is supported” bit is set to 1, the SpO2PR-Slow metric shall be included when
the PLX Continuous Measurement characteristic is notified, otherwise it shall not be present.
If the “Pulse Amplitude Index field is supported” bit is set to 1, the Pulse Amplitude Index field shall be
included when the PLX Continuous Measurement characteristic is notified or the PLX Spot-Check
Measurement characteristic is indicated. Otherwise it shall not be present.
If the Multiple Bonds feature is supported, the “Multiple Bonds Supported Feature” bit shall be set to 1,
otherwise it shall be set to 0.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 22 of 31
## 3.3.1.2 Measurement Status Support Field
The Measurement Status Support field shall be included in the PLX Features characteristic if the
Measurement Status feature is supported (see Section 3.3.1.1.1); otherwise, it shall be excluded.
Reserved for Future Use (RFU) bits in the Measurement Status Support field shall be set to 0.
If the bit for a field is set to 1, the bit is supported when it is sent in a measurement transmission. If the bit
is set to 0, the bit is not supported and shall never be set to 1 wherever a Measurement Status field is
present.
The bits of the Measurement Status Support field are defined in Table 3.10.
## Bit Definition
0-4 Reserved for Future Use
5 Measurement Ongoing bit supported
6 Early Estimated Data bit supported
7 Validated Data bit supported
8 Fully Qualified Data bit supported
9 Data from Measurement Storage bit supported
10 Data for Demonstration bit supported
11 Data for Testing bit supported
12 Calibration Ongoing bit supported
13 Measurement Unavailable bit supported
14 Questionable Measurement Detected bit supported
15 Invalid Measurement Detected bit supported
Table 3.10: Measurement Status Support definition
3.3.1.3 Device and Sensor Status Support Field
The Device and Sensor Status Support field shall be included in the PLX Features characteristic if the
Device and Sensor Status feature is supported (see Section 3.3.1.1.2); otherwise, it shall be excluded.
If the bit for a field is set to 1, the bit is supported when it is sent in a measurement transmission. If the bit
is set to 0, the bit is not supported and shall never be set to 1 wherever a Device and Sensor Status field
is present.
Reserved for Future Use (RFU) bits in the Device and Sensor Status Support field shall be set to 0.
The bits of the Device and Sensor Status Support field are defined in Table 3.11.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 23 of 31
## Bit  Definition
0 Extended Display Update Ongoing bit supported
1 Equipment Malfunction Detected bit supported
2 Signal Processing Irregularity Detected bit supported
3 Inadequate Signal Detected bit supported
4 Poor Signal Detected bit supported
5 Low Perfusion Detected bit supported
6 Erratic Signal Detected bit supported
7 Nonpulsatile Signal Detected bit supported
8 Questionable Pulse Detected bit supported
9 Signal Analysis Ongoing bit supported
10 Sensor Interference Detected bit supported
11 Sensor Unconnected to User bit supported
12 Unknown Sensor Connected bit supported
13 Sensor Displaced bit supported
14 Sensor Malfunctioning bit supported
15 Sensor Disconnected bit supported
16-23 Reserved for Future Use
Table 3.11: Device and Sensor Status Support definition
## 3.4 Record Access Control Point
[1] For this service to operate, profiles or other applications utilizing this service will need to ensure that
the Client configures the Record Access Control Point (RACP) [2] characteristic for indications.
When a client performs a write to the RACP to execute a desired procedure at the Server response shall
be sent from the Server in an indication.
## 3.4.1 Record Definition
Within the context of the Pulse Oximeter Service, a record consists of a temporarily stored, timestamped
PLX Spot-check Measurement Characteristic value, according to Section 3.1.
3.4.2 RACP Procedure Requirements
The table below shows the requirements for the RACP procedures (Op Codes, Operators, and Operands)
in the context of this service (see [2] for op code, operator, and operand values of the RACP).

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 24 of 31
## Procedure/
## Op Code
## Op Code
## Require
ment
## Operator Operator
## Requirement
## Operand
## Operand
## Requirement
## Report
## Stored
## Records
## M
## All
records
M No Operand Used N/A
## Delete Stored
## Records
## O
## All
records
C No Operand Used N/A
## Abort
## Operation
## O
## Null
## (0x00)
C No Operand Used N/A
## Report
Number of
## Stored
## Records
## O
## All
records
C No Operand Used N/A
## Responses
## Procedure/
## Op Code
## Op Code
## Require
ment
## Operator Operator
## Requirement
## Operand
## Operand
## Requirement
Number of
## Stored
## Records
## Response
## O
## Null
## (0x00)
## C
UINT16 containing
number of records
## M
## Response
## Code M
## Null
## (0x00)
## M
## Request Op Code,
## Response Code
## Value
## M
Table 3.12: RACP Procedure Requirements
C Mandatory if associated Op Code is supported, otherwise optional.

## Notes:
- Support for a given Operand for one Op Code and Operator combination does not imply support
of that Operand for other Op Code and Operator combinations.
- Support for a given Operator for one Op Code does not imply support of that Operator for other
## Op Codes.
- Op Codes that are not shown in Table 3.12 are excluded from support in this service.
## 3.4.3 Record Access Control Point Behavioral Description
The Record Access Control Point shall be used to control indications for stored records of the PLX Spot-
Check Measurement characteristic, as well as perform actions related to stored records, such as deleting
them. Procedures are triggered by a Write to this characteristic value that includes an Op Code specifying
the operation (see Table 3.12). In a multiple-bond case, the handling of the Control Point shall be
consistent across all bonds, i.e. there is a single database that is shared by all Clients.
## 3.4.4 Report Stored Records Procedure
When the Report Stored Records Op Code is written to the Record Access Control Point, the Server shall
indicate stored records using the PLX Spot-check measurement characteristic. Once all data records for

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 25 of 31
a given request have been indicated by the Server, the Server shall indicate the Record Access Control
Point with a Response Code Op Code and Response Code Value in the Operand set to Success (see
Record Access Control Point in [2]).
If the Server does not locate any records of the type requested available, the Server shall indicate the
Record Access Control Point with a Response Code Op Code and Response Code Value in the Operand
set to No Records Found (see RACP in [2]).
If the operation results in an error condition, this shall be indicated using the Response Code Op Code
and the appropriate Response Code Value in the Operand for the error condition (see Section 3.4.8).
If the Server is required to interrupt its data transfer before completion for any reason except in the event
of an Abort Operation request, the Server shall indicate the Record Access Control Point with a
Response Code Op Code and Response Code Value in the Operand set to Procedure not completed
(see RACP in [2]). In the event of an Abort Operation command,  the procedure terminates immediately
without the RACP indicating the Response Code Op Code for this procedure.
If this procedure is not completed, all records that had been successfully transmitted (i.e.
ATT_Handle_Value_Confirmation is received) up until the procedure failure shall be considered
successfully transmitted and any that have been successfully indicated shall not be transmitted again in
subsequent Report Stored Records procedures.
3.4.5 Delete Stored Records procedure
When the Delete Stored Records Op Code is written to the Record Access Control Point, the Server shall
delete all stored measurements. Deletion of records may be a permanent deletion of records from the
patient database. The Server shall indicate this characteristic with a Response Code Value of Success if
the records were successfully deleted from the patient record database (see RACP in [2]).
If the operation results in an error condition, this shall be indicated using the Response Code Op Code
and the appropriate Response Code Value in the Operand for the error condition (see Section 3.4.8).
3.4.6 Abort Operation procedure
When the Abort Operation Op Code is written to the Record Access Control Point, the Server shall stop
any RACP procedures currently in progress and shall make a best effort to stop sending any further data.
Once all RACP procedures have been stopped, the Server shall indicate the Record Access Control Point
with a Response Code Op Code and Response Code Value in the Operand set to Success (see RACP in
## [2]).
If the operation results in an error condition, this shall be indicated using the Response Code Op Code
and the appropriate Response Code Value in the Operand for the error condition (see Section 3.4.8).
3.4.7 Report Number of Stored Records procedure
When the Report Number of Stored Records Op Code is written to the Record Access Control Point, the
Server shall calculate and respond with a record count in UINT16 format. The response is indicated using
the Number of Stored Records Response Op Code.
If the operation results in an error condition, this shall be indicated using the Response Code Op Code
and the appropriate Response Code Value in the Operand for the error condition (see Section 3.4.8).

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 26 of 31
3.4.8 RACP Specific Errors
If the Server is unable to complete a procedure for any reason not stated here, the Server shall indicate
the RACP with a Response Code Op Code and Response Code Value in the Operand set to Procedure
not completed (see RACP in [2]).
If the Server is unable to process the Abort Operation procedure for any reason not stated here, the
Server shall indicate the RACP with a Response Code Op Code and Response Code Value in the
Operand set to Abort unsuccessful (see RACP in [2]).
If a request with an Op Code other than Abort Operation is written to the RACP while the Server is
performing a previously triggered RACP operation (i.e. resulting from invalid Client behavior), the Server
shall return an error response with the Common Profile and Service error code of Procedure Already In
## Progress (see [1]).
If the Op Code that was written to the RACP requests record indications and the Client Characteristic
Configuration descriptor is not configured for indications, the Server shall return an error response with
Common Profile and Service error code of Client Characteristic Configuration Descriptor Improperly
## Configured (see [1]).
If the Operator that was written to the RACP is not supported by the Server, the Server shall indicate the
RACP with a Response Code Op Code and Response Code Value in the Operand set to Operator Not
Supported (see RACP in [2]).
If the Operator that was written to the RACP is invalid, the Server shall indicate the RACP with a
Response Code Op Code and Response Code Value in the Operand set to Invalid Operator (see RACP
in [2]).
If the Op Code that was written to the RACP characteristic is not supported by the Server, the Server
shall indicate the RACP with a Response Code Op Code and Response Code Value in the Operand set
to Op Code Not Supported (see RACP in [2]).
If an Operand that was written to the RACP characteristic is not supported by the Server, the Server shall
indicate the RACP with a Response Code Op Code and Response Code Value in the Operand set to
Operand Not Supported (see RACP in [2]).
3.4.9 Procedure Timeout and Failure
In the context of the RACP characteristic, a procedure is started when a write to the RACP characteristic
is successfully completed. When a procedure is complete, the Server indicates the RACP characteristic
with the Op Code set to the corresponding Response Code.
A RACP procedure may consist of multiple characteristic indications of the PLX Spot-check Characteristic
value followed by an indication of the RACP. Time between these indications shall not exceed a 5 second
timeout period. If a timeout occurs, the Server shall stop sending any further indications related to the
operation and consider the procedure to have failed.
If the connection to the Client is lost, the procedure shall be considered to have failed, and shall not
resume upon the next connection.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 27 of 31
3.5 Requirements for Time-Sensitive Data
The PLX Spot-check Measurement characteristic value contains time-sensitive data and is considered a
time-sensitive characteristic.
For this characteristic, the following requirements apply:
- If the Server supports measurement storage:
- The Server should be able to store 30 or more measurements.
- The PLX Spot-check Measurement characteristic value shall include the Timestamp field.
- Support for the Timestamp field shall be expressed in the PLX Features characteristic value.
- If the maximum storage capacity in the Server is reached, the Server should overwrite the oldest
stored measurements first when acquiring new measurements.
- When indicating stored data, the oldest data shall be sent first followed by the next oldest data (in
first-in, first-out order) until all stored data has been transferred.
- The Server’s date and time may be lost due to battery replacement. If the Client can set the date
and time, it is recommended that the Client ensures the date and time is valid at the start of each
connection. If the time of the device is not set and new measurements are generated, the Flags
field in the PLX Spot-check Measurement characteristic value (see Section 3.1.1.1) shall indicate
the clock is not set for the measurement and the Client may check the Server’s time if it is
available and calculate what the correct time of the measurement is based on the difference.
Temporarily stored measurements may be discarded when a battery replacement occurs.
- If the Server does not support measurement storage:
- A measurement that is not indicated within the same measurement session it was generated in
shall be discarded.
Note: If a pulse oximeter is designed to store periodic measurements for transmission later, e.g. in a
sleep study, this service does not provide that functionality. Those features could be handled by another
service in the profile that would use an efficient design for the transfer of large amounts of data.
The PLX Continuous Measurement characteristic is meant to provide periodic live measurements, but is
not optimal for transmitting large volumes of stored records of this characteristic. Therefore, it is only used
to send live measurements that are not stored, although the stored measurements may be very similar in
format and period.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 28 of 31
4 SDP interoperability
If this service is exposed over BR/EDR, then it shall have the following SDP record.
## Item Definition Type Value Status
Service Class ID
## List
## M
Service Class #0  UUID «Pulse Oximeter Service» M
## Protocol
## Descriptor List
## M
Protocol #0  UUID L2CAP M
Parameter #0 for
## Protocol #0
PSM Uint16 PSM = ATT M
Protocol #1  UUID ATT M
BrowseGroupList   PublicBrowseRoot* M
Table 4.1: SDP Record
- PublicBrowseRoot shall be present; however, other browse UUIDs may also be included in the list.


## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 29 of 31
## 5 Special Values
## 5.1 Special Short Float Value
The following special short float values are defined in IEEE 11073-20601 [3].
## Special Short Value Value
NaN (not a number) 0x07FF
NRes (not at this resolution) 0x0800
+ INFINITY 0x07FE
- INFINITY 0x0802
Reserved for future use 0x0801
## Table 5.1: Special Short Float Values
NaN is used to report an invalid result from a computation step or to indicate missing data due to the
hardware’s inability to provide a valid measurement, perhaps from sensor perturbation.
NRes is used to report that the value cannot be represented with the available range and resolution,
possibly resulting from an overflow or underflow situation.

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 30 of 31
6 Acronyms and abbreviations
Any abbreviation or acronym used in the document, but not defined in the Bluetooth Core Specification [1]
sections (e.g., Volume 1 Part B), is defined here. The list is alphabetized.
Acronym/Abbreviation Meaning
PR Pulse Rate
PLX Pulse Oximeter
RACP Record Access Control Point
SpO2 Percent oxygen saturation of hemoglobin, as measured by a pulse
oximeter.
Table 6.1: Acronyms and abbreviations

## Pulse Oximeter Service /  Service Specification
Bluetooth SIG Proprietary Page 31 of 31
## 7 References
[1] Bluetooth Core Specification, Version 4.0 (as amended by CSS v4) or later
[2] Characteristic and Descriptor descriptions and UUIDs are accessible via the Bluetooth SIG Assigned
## Numbers
[3] ISO/IEEE Std 11073-20601™- 2008 Health Informatics - Personal Health Device Communication -
Application Profile - Optimized Exchange Protocol - version 1.0 or later. This also includes ISO/IEEE
## Std 11073-20601a™- 2010 – Amendment 1.
[4] ISO/IEEE Std 11073-10404™ – 2008 – Health Informatics – Personal Health Device Communication
– Part 10404: Device specialization – Pulse Oximeter
[5] Personal Health Devices Transcoding White Paper Version 16 or later