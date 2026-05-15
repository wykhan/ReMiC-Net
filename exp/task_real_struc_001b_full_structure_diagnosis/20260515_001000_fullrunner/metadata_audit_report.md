# metadata_audit_report

status: corrected_metadata_builder_used

- samples audited: 1000
- Mshell one-hot invalid voxels after correction: 0
- mean abs(Pcyc)>0.25 ratio: 0.042098
- delta_rho range: -0.074944 to 0.075000
- Pcyc range: -0.999305 to 0.999999

The 001a audit exposed invalid one-hot padding in the old metadata cache. This runner uses x-y-z aligned metadata and fills display-padding background as shell-0 with delta/Pcyc set to zero.
