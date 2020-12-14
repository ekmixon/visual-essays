# Visual Essays application

## Server

### Running the server

First, ensure that a python (version 3.8) is available and has the needed dependencies installed.
A suitable virtual environment can be created as follows:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r app/server/requirements.txt
```

To run the server:

```bash
app/server/main.py -l info
```

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