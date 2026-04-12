# UCL — Universal Configuration Language

**UCL (Universal Configuration Language)** is a modern, human-readable and extensible configuration language designed to replace JSON, YAML, and TOML in a unified way.

---

## Overview

UCL is built to be:

- Simple to read and write  
- Easy to parse and implement  
- Powerful enough for complex systems  
- Suitable for any type of project (OS, backend, cloud, tools)  

---

## Features

- Clean and minimal syntax  
- Structured configuration (sections & nested keys)  
- Strong readability (no YAML pitfalls)  
- Expressions support (`+`, `-`, `*`, `/`)  
- Environment variables: `env("KEY")`  
- References: `$var`  
- Profiles (`dev`, `prod`, `test`)  
- Modules / plugins / services  
- Schema validation  
- Macros & templates  
- Merge & override system  

---

## Example

```ucl
include "network.ucl";

module server extends base_server {

  host = "0.0.0.0";
  port = 8080;

  workers = 2 + 2;

}

database {
  engine = "postgres";
  host = "db.local";
  port = 5432;
}

profile production {
  logging.level = "info";
}

if env("ENV") == "dev" {
  logging.level = "debug";
}

## Use Cases

- Operating systems configuration (e.g. VitteOS)  
- Backend services  
- DevOps / cloud infrastructure  
- CLI tools  
- Application settings  
- Embedded systems  

---

## Implementation Goals

- Lightweight parser  
- Zero ambiguity syntax  
- Fast evaluation  
- Easy embedding in any language  
- Minimal dependencies  

---

## Philosophy

UCL aims to unify the best aspects of existing configuration formats:

- Simplicity of JSON  
- Readability of YAML  
- Structure of TOML  
- Power of a real language (expressions, macros, validation)  

---

## Status

Experimental — evolving specification  

---

## License

GPLV3
