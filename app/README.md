# Visual Essays application

The `Visual Essays application` includes a browser client and a number of back-end services.  The browser cliient is packaged as a javascrip bundle that is loaded by a simple HTML page.  The client uses a number of services exposed as HTTP endpoints.  In production the services are hosted in a cloud-based environment (currently using Google Cloud Run).  In development the server can be run locally.
   
## Server

### Running the server

First, ensure that a python (version 3.8) is available and has the needed dependencies installed.
A suitable virtual environment can be created as follows:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r app/server/requirements.txt
```



To basic command for running the server is:

```bash
app/server/main.py
```

The server accepts various option which can be seen using the `-h` option:
```bash
app/server/main.py -h
```

The most commonly used options include:
 - `-l` Set logging level. (`debug`, `info`, `warning`, `error`).  The default level is `warning`
 - `-d` Run server in development mode.  In development mode the app uses a locally served javascript bundle (on port `8088`, bu default).  Otherwise, a pre-built javascript bundle (found in the top-level `js` directory) is used.  
 - `-c` Use local content.

### Credentials

The visual essays server depends on external services that require credentials for use.  This includes Github and Google Cloud.  The Google Cloud services are optional when running the server for development purposes but are needed for deployment.  A Github token is needed if the development server needs to use the Github API, which is likely.

A Github token can be obtained from the `Settings / Developer settings` (https://github.com/settings/tokens) page accessed from the account menu located at the top right of the Github page.  The token can be stored in `gh-token` file in the `app/server` directory, or in an environment variable named `gh_token`.  Maintaining the token as an environment variable is recommended.  The project `.gitignore` file should inhibit committing/pushing the token to a remote repo but storing it as environment variable is recommended.

If [Gitpod](https://gitpod.io) is used for cloud-based development the token can be added to the environment in the account [setting](https://gitpod.io/settings/) page.  Use the variable key `gh_token`. 

## Client

The browser client code is found in the `app/client-lib` directory.

### Initializing the node environment

The yarn package manager is used for the project.  Setting up the environment is accomplished by using the `yarn` command without options.

### Building the javascript bundle

```bash
yarn build
```

### Running a development server

#### Option 1, with hot reload enabled

This is the recommended option to use when peforming component development and hot reloading is desired

```bash
yarn serve
```

The full browser app will be served on port `8088`.  https://localhost:8088

#### Option 2

This option is used when the app HTML is delivered by the server (as in production mode) but some level
of interactive javascript development is needed.  In this mode the javascript bundle is served on port `8088`.  

```bash
yarn serve-lib
```

## Setup troubleshooting:

If the pip install command fails with a `ERROR: Failed building wheel for cryptography` message, try installing the cryptography package with this command before running the bulk install with the requirements.text file.

```bash
pip install cryptography --global-option=build_ext --global-option="-L/usr/local/opt/openssl/lib" --global-option="-I/usr/local/opt/openssl/include"
```

If the `Pillow` install fails, ensure the needed dependencies are installed.  Information for this can be found at https://pillow.readthedocs.io/en/latest/installation.html.  For macos this can probably be resolved by using homebrew to install the needed dependencies.

```bash
brew install libtiff libjpeg webp little-cms2
```