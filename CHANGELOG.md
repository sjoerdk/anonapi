# Changelog

## [v1.5.5](https://github.com/sjoerdk/anonapi/tree/v1.5.5) (2021-02-18)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.5.4...v1.5.5)

**Implemented enhancements:**

- Remove example lines from default mapping [\#322](https://github.com/sjoerdk/anonapi/issues/322)
- anon map add-study-folders should not complain about project or output dir [\#321](https://github.com/sjoerdk/anonapi/issues/321)
- Running batch add without init yields confusing error message [\#315](https://github.com/sjoerdk/anonapi/issues/315)

**Fixed bugs:**

- Line with single space in mapping will raise confusing error [\#327](https://github.com/sjoerdk/anonapi/issues/327)
- anon batch remove does not work [\#320](https://github.com/sjoerdk/anonapi/issues/320)
- job info Source information not displayed [\#255](https://github.com/sjoerdk/anonapi/issues/255)

**Merged pull requests:**

- Update tox to 3.21.3 [\#323](https://github.com/sjoerdk/anonapi/pull/323) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 6.2.2 [\#319](https://github.com/sjoerdk/anonapi/pull/319) ([pyup-bot](https://github.com/pyup-bot))
- Update coverage to 5.4 [\#318](https://github.com/sjoerdk/anonapi/pull/318) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 21.0 [\#317](https://github.com/sjoerdk/anonapi/pull/317) ([pyup-bot](https://github.com/pyup-bot))
- Update openpyxl to 3.0.6 [\#314](https://github.com/sjoerdk/anonapi/pull/314) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.56.0 [\#312](https://github.com/sjoerdk/anonapi/pull/312) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx\_rtd\_theme to 0.5.1 [\#309](https://github.com/sjoerdk/anonapi/pull/309) ([pyup-bot](https://github.com/pyup-bot))
- Update factory-boy to 3.2.0 [\#307](https://github.com/sjoerdk/anonapi/pull/307) ([pyup-bot](https://github.com/pyup-bot))
- Update twine to 3.3.0 [\#305](https://github.com/sjoerdk/anonapi/pull/305) ([pyup-bot](https://github.com/pyup-bot))
- Update watchdog to 1.0.2 [\#303](https://github.com/sjoerdk/anonapi/pull/303) ([pyup-bot](https://github.com/pyup-bot))
- Update wheel to 0.36.2 [\#299](https://github.com/sjoerdk/anonapi/pull/299) ([pyup-bot](https://github.com/pyup-bot))
- Update pydicom to 2.1.2 [\#296](https://github.com/sjoerdk/anonapi/pull/296) ([pyup-bot](https://github.com/pyup-bot))

## [v1.5.4](https://github.com/sjoerdk/anonapi/tree/v1.5.4) (2020-11-09)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.5.3...v1.5.4)

**Implemented enhancements:**

- Add tutorials for anonymizing from PACS, share [\#284](https://github.com/sjoerdk/anonapi/issues/284)

**Fixed bugs:**

- Fresh install of anonapi with active mapping = None will yield confusing error [\#282](https://github.com/sjoerdk/anonapi/issues/282)

**Merged pull requests:**

- Update pydicom to 2.1.1 [\#283](https://github.com/sjoerdk/anonapi/pull/283) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 3.3.0 [\#281](https://github.com/sjoerdk/anonapi/pull/281) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 6.1.2 [\#279](https://github.com/sjoerdk/anonapi/pull/279) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.51.0 [\#272](https://github.com/sjoerdk/anonapi/pull/272) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 20.2.4 [\#270](https://github.com/sjoerdk/anonapi/pull/270) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx-autodoc-typehints to 1.11.1 [\#269](https://github.com/sjoerdk/anonapi/pull/269) ([pyup-bot](https://github.com/pyup-bot))

## [v1.5.3](https://github.com/sjoerdk/anonapi/tree/v1.5.3) (2020-11-03)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.5.2...v1.5.3)

**Implemented enhancements:**

- mapping file for path mappings should not have to be at data source [\#252](https://github.com/sjoerdk/anonapi/issues/252)

**Closed issues:**

- Add csv or xls file as input for map functions [\#260](https://github.com/sjoerdk/anonapi/issues/260)

## [v1.5.2](https://github.com/sjoerdk/anonapi/tree/v1.5.2) (2020-10-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.5.1...v1.5.2)

**Implemented enhancements:**

- Update sphinx documentation with active mapping [\#278](https://github.com/sjoerdk/anonapi/issues/278)

## [v1.5.1](https://github.com/sjoerdk/anonapi/tree/v1.5.1) (2020-10-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.5.0...v1.5.1)

**Implemented enhancements:**

- Add mapping location to mapping exception output [\#277](https://github.com/sjoerdk/anonapi/issues/277)
- Auto-generate changelog [\#276](https://github.com/sjoerdk/anonapi/issues/276)
- Missing column header in mapping will yield confusing error [\#273](https://github.com/sjoerdk/anonapi/issues/273)
- anon map add-study-folders with no parameters will try to add 0 items [\#259](https://github.com/sjoerdk/anonapi/issues/259)
- 404 message is cryptic [\#256](https://github.com/sjoerdk/anonapi/issues/256)

**Fixed bugs:**

- Logging setup causes exception in python 3.8 [\#271](https://github.com/sjoerdk/anonapi/issues/271)
- Do not complain about root\_source if root\_source is not used [\#265](https://github.com/sjoerdk/anonapi/issues/265)
- unfounded Could not determine delimiter  [\#264](https://github.com/sjoerdk/anonapi/issues/264)

**Closed issues:**

- Move CI to github actions  [\#274](https://github.com/sjoerdk/anonapi/issues/274)

## [v1.5.0](https://github.com/sjoerdk/anonapi/tree/v1.5.0) (2020-10-22)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.4.1...v1.5.0)

Introduces csv and xlsx files as input to mapping functions. You can now add all paths
in a csv file to a mapping with one command

## [v1.4.1](https://github.com/sjoerdk/anonapi/tree/v1.4.1) (2020-10-22)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.4.0...v1.4.1)

**Merged pull requests:**

- Update tox to 3.20.1 [\#268](https://github.com/sjoerdk/anonapi/pull/268) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.50.2 [\#267](https://github.com/sjoerdk/anonapi/pull/267) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 6.1.1 [\#263](https://github.com/sjoerdk/anonapi/pull/263) ([pyup-bot](https://github.com/pyup-bot))
- Update flake8 to 3.8.4 [\#262](https://github.com/sjoerdk/anonapi/pull/262) ([pyup-bot](https://github.com/pyup-bot))
- Update factory-boy to 3.1.0 [\#261](https://github.com/sjoerdk/anonapi/pull/261) ([pyup-bot](https://github.com/pyup-bot))
- Update coverage to 5.3 [\#251](https://github.com/sjoerdk/anonapi/pull/251) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 20.2.3 [\#248](https://github.com/sjoerdk/anonapi/pull/248) ([pyup-bot](https://github.com/pyup-bot))

## [v1.4.0](https://github.com/sjoerdk/anonapi/tree/v1.4.0) (2020-10-09)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.3.1...v1.4.0)

## [v1.3.1](https://github.com/sjoerdk/anonapi/tree/v1.3.1) (2020-10-07)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.3.0...v1.3.1)

**Implemented enhancements:**

- Standard mapping file improvements [\#254](https://github.com/sjoerdk/anonapi/issues/254)
- Mapping csv file is not read correctly in excel in region settings with colon column separator [\#241](https://github.com/sjoerdk/anonapi/issues/241)

## [v1.3.0](https://github.com/sjoerdk/anonapi/tree/v1.3.0) (2020-09-15)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.2.2...v1.3.0)

**Implemented enhancements:**

- anon mapping does allow easy adding of list of folders [\#243](https://github.com/sjoerdk/anonapi/issues/243)

## [v1.2.2](https://github.com/sjoerdk/anonapi/tree/v1.2.2) (2020-09-10)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.2.1...v1.2.2)

## [v1.2.1](https://github.com/sjoerdk/anonapi/tree/v1.2.1) (2020-09-10)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.2.0...v1.2.1)

## [v1.2.0](https://github.com/sjoerdk/anonapi/tree/v1.2.0) (2020-09-10)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.9...v1.2.0)

## [v1.1.9](https://github.com/sjoerdk/anonapi/tree/v1.1.9) (2020-09-10)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.8...v1.1.9)

## [v1.1.8](https://github.com/sjoerdk/anonapi/tree/v1.1.8) (2020-09-09)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.7...v1.1.8)

## [v1.1.7](https://github.com/sjoerdk/anonapi/tree/v1.1.7) (2020-09-09)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.6...v1.1.7)

**Implemented enhancements:**

- Trailing spaces in identifier should not cause exception [\#247](https://github.com/sjoerdk/anonapi/issues/247)
- anon create should check format for all identifiers before starting [\#246](https://github.com/sjoerdk/anonapi/issues/246)

**Fixed bugs:**

- Excel 365 in NL region will save csv with colon. Breaks anon create-from-mapping [\#244](https://github.com/sjoerdk/anonapi/issues/244)

**Merged pull requests:**

- Update tox to 3.20.0 [\#242](https://github.com/sjoerdk/anonapi/pull/242) ([pyup-bot](https://github.com/pyup-bot))
- Update wheel to 0.35.1 [\#240](https://github.com/sjoerdk/anonapi/pull/240) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 3.2.1 [\#239](https://github.com/sjoerdk/anonapi/pull/239) ([pyup-bot](https://github.com/pyup-bot))
- Update factory-boy to 3.0.1 [\#237](https://github.com/sjoerdk/anonapi/pull/237) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 20.2.2 [\#235](https://github.com/sjoerdk/anonapi/pull/235) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.48.2 [\#231](https://github.com/sjoerdk/anonapi/pull/231) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 6.0.1 [\#229](https://github.com/sjoerdk/anonapi/pull/229) ([pyup-bot](https://github.com/pyup-bot))
- Update coverage to 5.2.1 [\#225](https://github.com/sjoerdk/anonapi/pull/225) ([pyup-bot](https://github.com/pyup-bot))

## [v1.1.6](https://github.com/sjoerdk/anonapi/tree/v1.1.6) (2020-07-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.5...v1.1.6)

## [v1.1.5](https://github.com/sjoerdk/anonapi/tree/v1.1.5) (2020-07-22)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.4...v1.1.5)

## [v1.1.4](https://github.com/sjoerdk/anonapi/tree/v1.1.4) (2020-07-22)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.3...v1.1.4)

## [v1.1.3](https://github.com/sjoerdk/anonapi/tree/v1.1.3) (2020-06-09)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.2...v1.1.3)

**Merged pull requests:**

- Update click to 7.1.2 [\#210](https://github.com/sjoerdk/anonapi/pull/210) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 3.1.0 [\#209](https://github.com/sjoerdk/anonapi/pull/209) ([pyup-bot](https://github.com/pyup-bot))
- Update flake8 to 3.8.3 [\#208](https://github.com/sjoerdk/anonapi/pull/208) ([pyup-bot](https://github.com/pyup-bot))
- Update tox to 3.15.2 [\#207](https://github.com/sjoerdk/anonapi/pull/207) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.46.1 [\#206](https://github.com/sjoerdk/anonapi/pull/206) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 5.4.3 [\#205](https://github.com/sjoerdk/anonapi/pull/205) ([pyup-bot](https://github.com/pyup-bot))
- Update pydicom to 2.0.0 [\#204](https://github.com/sjoerdk/anonapi/pull/204) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 20.1.1 [\#200](https://github.com/sjoerdk/anonapi/pull/200) ([pyup-bot](https://github.com/pyup-bot))
- Update bumpversion to 0.6.0 [\#199](https://github.com/sjoerdk/anonapi/pull/199) ([pyup-bot](https://github.com/pyup-bot))
- Pin click to latest version 7.1.2 [\#193](https://github.com/sjoerdk/anonapi/pull/193) ([pyup-bot](https://github.com/pyup-bot))
- Update coverage to 5.1 [\#190](https://github.com/sjoerdk/anonapi/pull/190) ([pyup-bot](https://github.com/pyup-bot))
- Update tabulate to 0.8.7 [\#183](https://github.com/sjoerdk/anonapi/pull/183) ([pyup-bot](https://github.com/pyup-bot))
- Pin click to latest version 7.1.1 [\#179](https://github.com/sjoerdk/anonapi/pull/179) ([pyup-bot](https://github.com/pyup-bot))

## [v1.1.2](https://github.com/sjoerdk/anonapi/tree/v1.1.2) (2020-04-15)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.1...v1.1.2)

## [v1.1.1](https://github.com/sjoerdk/anonapi/tree/v1.1.1) (2020-03-18)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.1.0...v1.1.1)

## [v1.1.0](https://github.com/sjoerdk/anonapi/tree/v1.1.0) (2020-03-04)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.12...v1.1.0)

**Closed issues:**

- Dicom file check is slower than needs to [\#169](https://github.com/sjoerdk/anonapi/issues/169)

**Merged pull requests:**

- Update sphinx to 2.4.3 [\#174](https://github.com/sjoerdk/anonapi/pull/174) ([pyup-bot](https://github.com/pyup-bot))
- Update pydicom to 1.4.2 [\#173](https://github.com/sjoerdk/anonapi/pull/173) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.43.0 [\#172](https://github.com/sjoerdk/anonapi/pull/172) ([pyup-bot](https://github.com/pyup-bot))

## [v1.0.12](https://github.com/sjoerdk/anonapi/tree/v1.0.12) (2020-03-04)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.11...v1.0.12)

## [v1.0.11](https://github.com/sjoerdk/anonapi/tree/v1.0.11) (2020-03-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.10...v1.0.11)

## [v1.0.10](https://github.com/sjoerdk/anonapi/tree/v1.0.10) (2020-03-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.9...v1.0.10)

## [v1.0.9](https://github.com/sjoerdk/anonapi/tree/v1.0.9) (2020-03-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.8...v1.0.9)

**Closed issues:**

- JobStatus is defined twice [\#176](https://github.com/sjoerdk/anonapi/issues/176)

## [v1.0.8](https://github.com/sjoerdk/anonapi/tree/v1.0.8) (2020-02-28)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.7...v1.0.8)

## [v1.0.7](https://github.com/sjoerdk/anonapi/tree/v1.0.7) (2020-02-28)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.6...v1.0.7)

**Implemented enhancements:**

- add-study-folder and add-all-study-folders should have a --skip-scanning option [\#175](https://github.com/sjoerdk/anonapi/issues/175)

## [v1.0.6](https://github.com/sjoerdk/anonapi/tree/v1.0.6) (2020-02-27)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.5...v1.0.6)

## [v1.0.5](https://github.com/sjoerdk/anonapi/tree/v1.0.5) (2020-02-24)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.4...v1.0.5)

## [v1.0.4](https://github.com/sjoerdk/anonapi/tree/v1.0.4) (2020-02-24)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.3...v1.0.4)

## [v1.0.3](https://github.com/sjoerdk/anonapi/tree/v1.0.3) (2020-02-20)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.2...v1.0.3)

**Implemented enhancements:**

- Expand mapping file structure [\#124](https://github.com/sjoerdk/anonapi/issues/124)
- write documentation for create, map, select  [\#116](https://github.com/sjoerdk/anonapi/issues/116)

**Closed issues:**

- anon batch map add mapping-wide parameters [\#151](https://github.com/sjoerdk/anonapi/issues/151)
- Make anon map init write newline according to OS [\#150](https://github.com/sjoerdk/anonapi/issues/150)
- anonapi 1.0.0 release checklist  [\#149](https://github.com/sjoerdk/anonapi/issues/149)
- Refactor settings structure, add path mapping [\#125](https://github.com/sjoerdk/anonapi/issues/125)

**Merged pull requests:**

- Update tox to 3.14.5 [\#170](https://github.com/sjoerdk/anonapi/pull/170) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 2.4.1 [\#167](https://github.com/sjoerdk/anonapi/pull/167) ([pyup-bot](https://github.com/pyup-bot))
- Update watchdog to 0.10.2 [\#166](https://github.com/sjoerdk/anonapi/pull/166) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.42.1 [\#163](https://github.com/sjoerdk/anonapi/pull/163) ([pyup-bot](https://github.com/pyup-bot))
- Update wheel to 0.34.2 [\#162](https://github.com/sjoerdk/anonapi/pull/162) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 5.3.5 [\#160](https://github.com/sjoerdk/anonapi/pull/160) ([pyup-bot](https://github.com/pyup-bot))

## [v1.0.2](https://github.com/sjoerdk/anonapi/tree/v1.0.2) (2020-02-17)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.1...v1.0.2)

## [v1.0.1](https://github.com/sjoerdk/anonapi/tree/v1.0.1) (2020-02-14)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v1.0.0...v1.0.1)

## [v1.0.0](https://github.com/sjoerdk/anonapi/tree/v1.0.0) (2020-02-14)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.4.2...v1.0.0)

## [v0.4.2](https://github.com/sjoerdk/anonapi/tree/v0.4.2) (2020-02-10)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.4.1...v0.4.2)

## [v0.4.1](https://github.com/sjoerdk/anonapi/tree/v0.4.1) (2020-02-06)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.4.0...v0.4.1)

## [v0.4.0](https://github.com/sjoerdk/anonapi/tree/v0.4.0) (2020-02-05)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.3.1...v0.4.0)

**Merged pull requests:**

- Update pydicom to 1.4.1 [\#156](https://github.com/sjoerdk/anonapi/pull/156) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.42.0 [\#155](https://github.com/sjoerdk/anonapi/pull/155) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 20.0.2 [\#154](https://github.com/sjoerdk/anonapi/pull/154) ([pyup-bot](https://github.com/pyup-bot))
- Update tqdm to 4.42.0 [\#153](https://github.com/sjoerdk/anonapi/pull/153) ([pyup-bot](https://github.com/pyup-bot))
- Update pydicom to 1.4.1 [\#147](https://github.com/sjoerdk/anonapi/pull/147) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 5.3.4 [\#146](https://github.com/sjoerdk/anonapi/pull/146) ([pyup-bot](https://github.com/pyup-bot))
- Update coverage to 5.0.3 [\#142](https://github.com/sjoerdk/anonapi/pull/142) ([pyup-bot](https://github.com/pyup-bot))
- Update tox to 3.14.3 [\#139](https://github.com/sjoerdk/anonapi/pull/139) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 2.3.1 [\#138](https://github.com/sjoerdk/anonapi/pull/138) ([pyup-bot](https://github.com/pyup-bot))
- Update twine to 3.1.1 [\#126](https://github.com/sjoerdk/anonapi/pull/126) ([pyup-bot](https://github.com/pyup-bot))
- Update fileselection to 0.3.1 [\#121](https://github.com/sjoerdk/anonapi/pull/121) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx-autodoc-typehints to 1.10.3 [\#112](https://github.com/sjoerdk/anonapi/pull/112) ([pyup-bot](https://github.com/pyup-bot))
- Update flake8 to 3.7.9 [\#106](https://github.com/sjoerdk/anonapi/pull/106) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest-runner to 5.2 [\#104](https://github.com/sjoerdk/anonapi/pull/104) ([pyup-bot](https://github.com/pyup-bot))
- Update wheel to 0.33.6 [\#84](https://github.com/sjoerdk/anonapi/pull/84) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx\_rtd\_theme to 0.4.3 [\#29](https://github.com/sjoerdk/anonapi/pull/29) ([pyup-bot](https://github.com/pyup-bot))

## [v0.3.1](https://github.com/sjoerdk/anonapi/tree/v0.3.1) (2020-01-23)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.3.0...v0.3.1)

## [v0.3.0](https://github.com/sjoerdk/anonapi/tree/v0.3.0) (2020-01-23)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.2.3...v0.3.0)

**Implemented enhancements:**

- Add get\_jobs\_info\_extended function to api  [\#128](https://github.com/sjoerdk/anonapi/issues/128)

## [v0.2.3](https://github.com/sjoerdk/anonapi/tree/v0.2.3) (2019-12-03)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.2.2...v0.2.3)

## [v0.2.2](https://github.com/sjoerdk/anonapi/tree/v0.2.2) (2019-12-03)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.2.1...v0.2.2)

## [v0.2.1](https://github.com/sjoerdk/anonapi/tree/v0.2.1) (2019-11-27)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.2.0...v0.2.1)

**Implemented enhancements:**

- Create functions, rewrite, finish first version [\#115](https://github.com/sjoerdk/anonapi/issues/115)

## [v0.2.0](https://github.com/sjoerdk/anonapi/tree/v0.2.0) (2019-11-27)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.17...v0.2.0)

## [v0.1.17](https://github.com/sjoerdk/anonapi/tree/v0.1.17) (2019-10-04)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.16...v0.1.17)

## [v0.1.16](https://github.com/sjoerdk/anonapi/tree/v0.1.16) (2019-10-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.15...v0.1.16)

## [v0.1.15](https://github.com/sjoerdk/anonapi/tree/v0.1.15) (2019-10-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.14...v0.1.15)

## [v0.1.14](https://github.com/sjoerdk/anonapi/tree/v0.1.14) (2019-10-01)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.13...v0.1.14)

## [v0.1.13](https://github.com/sjoerdk/anonapi/tree/v0.1.13) (2019-09-30)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.12...v0.1.13)

## [v0.1.12](https://github.com/sjoerdk/anonapi/tree/v0.1.12) (2019-09-19)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.11...v0.1.12)

## [v0.1.11](https://github.com/sjoerdk/anonapi/tree/v0.1.11) (2019-09-06)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.10...v0.1.11)

## [v0.1.10](https://github.com/sjoerdk/anonapi/tree/v0.1.10) (2019-09-05)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.9...v0.1.10)

## [v0.1.9](https://github.com/sjoerdk/anonapi/tree/v0.1.9) (2019-09-05)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.8...v0.1.9)

## [v0.1.8](https://github.com/sjoerdk/anonapi/tree/v0.1.8) (2019-08-30)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.7...v0.1.8)

## [v0.1.7](https://github.com/sjoerdk/anonapi/tree/v0.1.7) (2019-08-30)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.6...v0.1.7)

## [v0.1.6](https://github.com/sjoerdk/anonapi/tree/v0.1.6) (2019-08-30)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.5...v0.1.6)

## [v0.1.5](https://github.com/sjoerdk/anonapi/tree/v0.1.5) (2019-08-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.4...v0.1.5)

## [v0.1.4](https://github.com/sjoerdk/anonapi/tree/v0.1.4) (2019-08-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.3...v0.1.4)

## [v0.1.3](https://github.com/sjoerdk/anonapi/tree/v0.1.3) (2019-08-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.2...v0.1.3)

## [v0.1.2](https://github.com/sjoerdk/anonapi/tree/v0.1.2) (2019-08-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.1...v0.1.2)

## [v0.1.1](https://github.com/sjoerdk/anonapi/tree/v0.1.1) (2019-07-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.1.0...v0.1.1)

## [v0.1.0](https://github.com/sjoerdk/anonapi/tree/v0.1.0) (2019-07-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.32...v0.1.0)

## [v0.0.32](https://github.com/sjoerdk/anonapi/tree/v0.0.32) (2019-07-23)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.31...v0.0.32)

## [v0.0.31](https://github.com/sjoerdk/anonapi/tree/v0.0.31) (2019-07-23)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.30...v0.0.31)

## [v0.0.30](https://github.com/sjoerdk/anonapi/tree/v0.0.30) (2019-07-23)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.29...v0.0.30)

## [v0.0.29](https://github.com/sjoerdk/anonapi/tree/v0.0.29) (2019-06-24)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.28...v0.0.29)

## [v0.0.28](https://github.com/sjoerdk/anonapi/tree/v0.0.28) (2019-06-24)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.27...v0.0.28)

## [v0.0.27](https://github.com/sjoerdk/anonapi/tree/v0.0.27) (2019-05-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.26...v0.0.27)

## [v0.0.26](https://github.com/sjoerdk/anonapi/tree/v0.0.26) (2019-05-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.25...v0.0.26)

## [v0.0.25](https://github.com/sjoerdk/anonapi/tree/v0.0.25) (2019-05-29)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.24...v0.0.25)

**Merged pull requests:**

- Update tox to 3.12.1 [\#60](https://github.com/sjoerdk/anonapi/pull/60) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest-runner to 5.0 [\#59](https://github.com/sjoerdk/anonapi/pull/59) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 4.5.0 [\#54](https://github.com/sjoerdk/anonapi/pull/54) ([pyup-bot](https://github.com/pyup-bot))
- Update wheel to 0.33.4 [\#53](https://github.com/sjoerdk/anonapi/pull/53) ([pyup-bot](https://github.com/pyup-bot))
- Update pip to 19.1.1 [\#49](https://github.com/sjoerdk/anonapi/pull/49) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 2.0.1 [\#45](https://github.com/sjoerdk/anonapi/pull/45) ([pyup-bot](https://github.com/pyup-bot))
- Update coverage to 4.5.3 [\#35](https://github.com/sjoerdk/anonapi/pull/35) ([pyup-bot](https://github.com/pyup-bot))
- Update flake8 to 3.7.7 [\#34](https://github.com/sjoerdk/anonapi/pull/34) ([pyup-bot](https://github.com/pyup-bot))

## [v0.0.24](https://github.com/sjoerdk/anonapi/tree/v0.0.24) (2019-05-20)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.23...v0.0.24)

## [v0.0.23](https://github.com/sjoerdk/anonapi/tree/v0.0.23) (2019-05-15)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.22...v0.0.23)

## [v0.0.22](https://github.com/sjoerdk/anonapi/tree/v0.0.22) (2019-02-28)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.21...v0.0.22)

## [v0.0.21](https://github.com/sjoerdk/anonapi/tree/v0.0.21) (2019-02-13)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.20...v0.0.21)

**Merged pull requests:**

- Update pytest to 4.1.1 [\#20](https://github.com/sjoerdk/anonapi/pull/20) ([pyup-bot](https://github.com/pyup-bot))
- Update tox to 3.7.0 [\#19](https://github.com/sjoerdk/anonapi/pull/19) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 1.8.3 [\#17](https://github.com/sjoerdk/anonapi/pull/17) ([pyup-bot](https://github.com/pyup-bot))
- Update tox to 3.6.1 [\#16](https://github.com/sjoerdk/anonapi/pull/16) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx-autodoc-typehints to 1.6.0 [\#15](https://github.com/sjoerdk/anonapi/pull/15) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 4.0.2 [\#14](https://github.com/sjoerdk/anonapi/pull/14) ([pyup-bot](https://github.com/pyup-bot))
- Update wheel to 0.32.3 [\#9](https://github.com/sjoerdk/anonapi/pull/9) ([pyup-bot](https://github.com/pyup-bot))

## [v0.0.20](https://github.com/sjoerdk/anonapi/tree/v0.0.20) (2019-02-11)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.19...v0.0.20)

## [v0.0.19](https://github.com/sjoerdk/anonapi/tree/v0.0.19) (2018-11-14)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.18...v0.0.19)

**Merged pull requests:**

- Update coverage to 4.5.2 [\#6](https://github.com/sjoerdk/anonapi/pull/6) ([pyup-bot](https://github.com/pyup-bot))
- Update pytest to 3.10.1 [\#5](https://github.com/sjoerdk/anonapi/pull/5) ([pyup-bot](https://github.com/pyup-bot))
- Update sphinx to 1.8.2 [\#4](https://github.com/sjoerdk/anonapi/pull/4) ([pyup-bot](https://github.com/pyup-bot))

## [v0.0.18](https://github.com/sjoerdk/anonapi/tree/v0.0.18) (2018-11-09)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.17...v0.0.18)

**Merged pull requests:**

- Update pytest to 3.10.0 [\#2](https://github.com/sjoerdk/anonapi/pull/2) ([pyup-bot](https://github.com/pyup-bot))

## [v0.0.17](https://github.com/sjoerdk/anonapi/tree/v0.0.17) (2018-11-08)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.16...v0.0.17)

## [v0.0.16](https://github.com/sjoerdk/anonapi/tree/v0.0.16) (2018-11-07)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.15...v0.0.16)

## [v0.0.15](https://github.com/sjoerdk/anonapi/tree/v0.0.15) (2018-11-07)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.14...v0.0.15)

## [v0.0.14](https://github.com/sjoerdk/anonapi/tree/v0.0.14) (2018-11-07)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.13...v0.0.14)

## [v0.0.13](https://github.com/sjoerdk/anonapi/tree/v0.0.13) (2018-11-07)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.12...v0.0.13)

## [v0.0.12](https://github.com/sjoerdk/anonapi/tree/v0.0.12) (2018-11-06)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.11...v0.0.12)

## [v0.0.11](https://github.com/sjoerdk/anonapi/tree/v0.0.11) (2018-11-05)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.10...v0.0.11)

## [v0.0.10](https://github.com/sjoerdk/anonapi/tree/v0.0.10) (2018-11-05)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.9...v0.0.10)

## [v0.0.9](https://github.com/sjoerdk/anonapi/tree/v0.0.9) (2018-11-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.8...v0.0.9)

## [v0.0.8](https://github.com/sjoerdk/anonapi/tree/v0.0.8) (2018-11-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.7...v0.0.8)

## [v0.0.7](https://github.com/sjoerdk/anonapi/tree/v0.0.7) (2018-11-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.6...v0.0.7)

## [v0.0.6](https://github.com/sjoerdk/anonapi/tree/v0.0.6) (2018-11-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.5...v0.0.6)

**Merged pull requests:**

- Initial Update [\#1](https://github.com/sjoerdk/anonapi/pull/1) ([pyup-bot](https://github.com/pyup-bot))

## [v0.0.5](https://github.com/sjoerdk/anonapi/tree/v0.0.5) (2018-11-02)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.4...v0.0.5)

## [v0.0.4](https://github.com/sjoerdk/anonapi/tree/v0.0.4) (2018-11-01)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.3...v0.0.4)

## [v0.0.3](https://github.com/sjoerdk/anonapi/tree/v0.0.3) (2018-11-01)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/v0.0.2...v0.0.3)

## [v0.0.2](https://github.com/sjoerdk/anonapi/tree/v0.0.2) (2018-11-01)

[Full Changelog](https://github.com/sjoerdk/anonapi/compare/ec5f896d86cd112e98b07115d8be09a784f7bc85...v0.0.2)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
