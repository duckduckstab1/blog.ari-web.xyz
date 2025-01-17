# [Ari-web blogs](https://blog.ari-web.xyz/)

<p align="center">
  <img src="https://img.shields.io/badge/Maintained-Yes-green?color=red&style=flat-square">
  <img src="https://img.shields.io/github/last-commit/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
  <img src="https://img.shields.io/github/repo-size/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
  <img src="https://img.shields.io/github/issues/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
  <img src="https://img.shields.io/github/stars/TruncatedDinosour/blog.ari-web.xyz?color=red&style=flat-square">
</p>

<p align="center">
  <a href="https://app.netlify.com/sites/blog-ari-web/deploys"><img src="https://api.netlify.com/api/v1/badges/bbd7d670-9152-41a8-8c99-df57e4669606/deploy-status"></a>
</p>

## Installing dependencies

```sh
$ python3 -m virtualenv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Or

```sh
$ python3 -m pip install --user -r requirements.txt
```

## Completions

-   Bash

```bash
$ . completions/blog.bash
```

## Building

-   Generate full-on static site

```bash
$ CI=1 ./scripts/blog static
```

-   Only build blogs

```bash
$ CI=1 ./scripts/blog static
```

`CI` environment variable is optional,
though setting it in a build/CI environment is good
to save time on some operations that are useless
in that context, for example sorting blogs.

`CI` can have any value.

## The API

Nobody is stopping you from using the static API,
it's located at [/blog.json](https://blog.ari-web.xyz/blog.json), also if you're using
this API generally, this API is **extremely** large, so
I implemented cache validation, just cache it,
including the sha256 hash and validate it with
the [hash on the api](https://blog.ari-web.xyz/blog_json_hash.txt)
