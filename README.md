# Moxa IO Generated PLC Structured Text

___

## Introduction
The purpose of this program is to generate structured text (One of the IEC 6113-1 Programming Languages)   
that'll be used for processing Moxa ioLogik E1200 Series Ethernet Remote I/O.    
The Moxa I/O is remote I/O for an Allen Bradley CompactLogix PLC.   

### Example Header
The program requires that a csv file be created or used that contains the following headers:  

| Rack Number | Slot Number | Slot Type | Channel Number | Channel Type | Tag Name  | Raw Min | Raw Max | EU Min | EU Max | Use Counts |
|-------------|-------------|-----------|----------------|--------------|-----------|---------|---------|--------|--------|------------|
| 1           | 0           | e1260     |  0             | rtd          | AI_Temp_1 | 0       | 1200    | 0      | 10     | 1          | 

> **Rack Number** - 1 - 32 for CompactLogix 5380 L310ER and 1- 64 for L330ER models.   
> **Slot Number** - Always zero since moxas are remote io and standalone.  
> **Slot Type** -  options are [e1210, e1212, e1240, e1241, e1260].   
> **Channel Number** - dependent on the moxa model, starts at channel 0.  
> **Channel Type** - options are [rtd, ai, ao, di, do].  
> **Tag Name** - append characters [AI_, AO_, DI_, or DO_] to beginning of the tag as shown above in the example header.  
> **Raw Min, Raw Max, EU Min, and EU Max** apply to the analog scaling.  
> **If the controller is a digital input/output module then scaling doesn't apply.  
> **Use Counts** - applies to analog scaling ONLY and should set to 1 if scaling is going to be needed.   

___

## Python Modules
#### moxa_io
```python
# moxa_io module

# Base Class
class MoxaE1200(ABC)

class MoxaE1212(MoxaE1200)
    
class MoxaE1210(MoxaE1200)

class MoxaE1240(MoxaE1200)

class MoxaE1241(MoxaE1200)

class MoxaE1241(MoxaE1200)

class MoxaE1260(MoxaE1200)

class MoxaFileProc
```

#### moxa_exceptions module
```python
# moxa_exceptions module

class MoxaError(Exception):

class MoxaIoError(MoxaError):
    
class MultiSlotError(MoxaError):

class DuplRackError(MoxaError):

class ChanTypeRackError(MoxaError):
    
class ChanNumRackError(MoxaError):
```

        


