## linci.artifact

### artifact store directory structure

Provided that:
* A is an artifact site, and B is another
* A-001 is an artifact from A, B-001 is an artifact from B
artifact directory tree will be like this:
```
├── A
│   └── 000
│       ├── A-001
│       │   ├── 1456471151834884
│       │   ├── 1456471151835009
│       │   └── __attatchment
│       │       └── 1456471395825387
│       └── A-001.meta
└── B
    └── 000
        ├── B-001
        │   ├── 1456471339006685
        │   ├── 1456471350099815
        │   └── __attatchment
        │       └── 1456471241515289
        └── B-001.meta
```

### artifact meta file

The **.meta** file is a json file, example:
```
{
  "__ext": {},
  "artifact_id": "EXAMPLE-2",
  "artifact_type":"default",
  "file_list": [
    {
      "path": "rom.img",
      "store_path": "1456471151834884",
      "md5": "9f0d63194eb2445a9d908bac592bdd64"
    },
    {
      "path": "usb/LogoVerificationReport.aspx.pdf",
      "store_path": "1456471151835009",
      "md5": "62c258a54b1760e078c1306276c05d71"
    }
  ],
  "attachment_list": [
    {
      "path": "test_report.doc",
      "store_path": "1456471395825387",
      "md5": "c1aabfc0836d024a6c57b5233a48f836"
    }
  ]
}
```
