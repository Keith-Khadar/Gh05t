# README: 3D-Printed EEG Headset

## Overview
This folder hosts 3D printable files for assembling the EEG headset designed to securely hold electrodes in place for capturing brainwave signals. 
The design ensures proper electrode placement while maintaining comfort and stability during use.

## Files
1) hexagonal_fitting.stl – Secures the electrodes in place with a tight fit.
2) medium_headset_front_half.stl – Front section of the EEG headset frame.
3) medium_headset_back_half.stl – Back section of the EEG headset frame.
4) wire_clip.stl – Manages and organizes electrode wires.
5) electrode_holder.stl – Electrode holder component ensuring stable contact with the scalp.
6) fastening_screw.stl – Fastening component for structural stability.

## Printing Instructions
Software- UltiMaker Cura
Material- PLA (Polylactic Acid)
Print settings-
* Infill density: 15%
* Support overhang angle: 60.0

* Build plate adhesion: Brim (for halves of the headset) or Skirt (for all other components)


## Materials
EEG Headset Frame (2 halves)
Spring fittings (x 10)
Snap-buttons (x 12) 
Electrode holders (x 10)
Fastening screws (x 10)
Copper wire of 12cm (x 12)
Electrodes (x 10)
Wires (x 12)
Wire clips (x 16)
Sandpaper for post-processing
Wire clipper for removing the excess support prints especially from the EEG headset halves

## Assembly Instructions
1) Print all above components.
![IMG_20241218_110856440](https://github.com/user-attachments/assets/7973ac54-1a3d-400e-8f54-58e8113e2540)
2) Ensure that any excess printed support structures have been remove from the headset halves, and that all rough edges are sanded smooth for comfort. 
   Test the fit of the halves before proceeding to ensure they align properly and then glue them together.
3) Glue the hexagonal fitting into the designated slots on the inside of the headset at appropriate positions according to the 10-20 system (FP1, FP2, C3, C4, P7, P8, 01, 02).
4) Take the spring fittings and screw them into the fastening screws. These springs once positioned securely, will provide the adjustable fit for the headset.
5) Now, push the wider side of the electrode holder in the fastening screw against the spring from the inner side of the headset.
6) Glue the snap buttons to the electrode holder with the finer end protruding outward and the flat end soldered to a mulit-strand copper wire.
![IMG_20241218_112913297](https://github.com/user-attachments/assets/6472966a-4cbd-4cc3-b648-91a97236bb8d)
7) Each copper wire is in turn soldered to one end of the jumper wire, the other end is attached to the headers on the board.
8) Attach wire clip to minimize tangling of the wires.
![IMG_20250122_214925864](https://github.com/user-attachments/assets/60e6182e-b3c2-49ec-8db9-3df36d83b465)

## Usage Guidelines
Adjust the headset for a snug but comfortable fit.
Regularly check the integrity of the solder connections and adjust the electrode placement using the fitting screw as needed for consistent performance.

## Future work
The design of the electrode and board covers is being worked upon.

## Credit
This design is inspired by and builds upon the open-source EEG headset designs from OpenBCI. 
Their contributions to the neurotechnology community are invaluable.
