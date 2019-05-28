# CIDD training for Lake Victoria project

## CIDD install on EEC SUSE computers

There are 4 EEC display machines at TMA:

*  One 9355 unit in the ops center
*  One 9355 in the severe weather office
*  One 8051 unit in the modeling lab
*  One 8051 unit in the ops center

## Machine specifications

### Specs of 9355 units

  * SUSE 12.2 
  * Linux kernel 3.4.6-2.10-desktop x86_64
  * gcc (SUSE Linux) 4.7.1 
  * 8 cores
  * 16 GB RAM

### Specs of 8051 units

  * SUSE 11.2
  * Linux kernel 2.6.31.5-0.1-default
  * gcc (SUSE Linux) 4.4.1
  * 4 cores
  * 4 GB RAM

## Directories etc.

The installations are under the ```root``` account.

The top-level directory is ```/cidd```.

Also, there are 2 USB drives with software and data, that can be used on any machine.

When mounted, they appear as ```/media/lakevic```.

The following links are available as short cuts:

```
  /cidd/localDisk -> git/lrose-projects-lakevic/projDir/displayHome/bin/
  /cidd/usbDisk -> /media/lakevic/git/lrose-projects-lakevic/projDir/displayHome/bin
```

## Running CIDD from the USB drives.

The USB drives contain the full data set. So use these if you want cases other than those specificied by Jim and Rita.

Plug the drive in to a USB port. The 9355 units have a USB-3 port on the back, which is faster.

When the USB GUI pops up and indicates:

```  There are 2 actions for this device```

in the GUI select:

```  Open in file manager```

That will mount the drive.

Then:

```  cd /cidd/usbDisk```

That will take you to the directory with the scripts.

Run the start script you want. The following are available:

```
  ./start_CIDD.training_20171219_013000
  ./start_CIDD.training_20190115_050000
  ./start_CIDD.training_20190308_050000
  ./start_CIDD.training_20190331_230000
  ./start_CIDD.training_20190426_060000
  ./start_CIDD.training_at_time
```

The top entries are coded to start at the indicated dates and times.

The last entry, ```./start_CIDD.training_at_time```, allows you to specify the time at which you want to start.

For example:

```
  ./start_CIDD.training_at_time 2019 03 08 05 00 00
```

is equivalent to:

```
  ./start_CIDD.training_20190308_050000
```

You must use leading zeros in this command.

## Running CIDD from the local hard disk.

The internal hard disk contains only those cases specificied by Jim and Rita.

To go there:

```  cd /cidd/localDisk```

That will take you to the directory with the scripts.

Run the start script you want. The following are available:

```
  ./start_CIDD.training_20171219_013000
  ./start_CIDD.training_20190115_050000
  ./start_CIDD.training_20190308_050000
  ./start_CIDD.training_20190331_230000
  ./start_CIDD.training_20190426_060000
```

