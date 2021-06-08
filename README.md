# atsy
A dumping ground for cross-platform browser memory testing.

## Example Usage
An example script can be found under `example/comp_analysis.py`. It uses the [TP5 pageset](http://people.mozilla.org/~jmaher/taloszips/zips/tp5n.zip), but the example can be modified to use any set of URLs.

### Prereqs
- nginx (or some other webserver)
- The latest [chromedriver](https://chromedriver.chromium.org/)
- Install **atsy**: `python setup.py install` should do the trick.
- Install/update the browsers you want to test. Note installation locations.
  - Chrome - [devchannel](https://www.google.com/chrome/browser/desktop/index.html?platform=linux&extra=devchannel)
  - Firefox - [Nightly](https://nightly.mozilla.org/)
- Update the setup portion of the example to specify your binary locations and update the path filters if necessary.

On Ubuntu the following would probably do the job:
```bash
# Install a local webserver
sudo apt-get install nginx

mkdir atsy-test
cd atsy-test

# Setup a virtualenv to work in
virtualenv venv
source venv/bin/activate

# Setup atsy
git clone https://github.com/EricRahm/atsy.git
cd atsy
python setup.py install
cd ..

# Get the latest chromedriver
wget http://chromedriver.storage.googleapis.com/2.21/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
rm chromedriver_linux64.zip

# Download the tp5 pageset and setup a webroot
mkdir nginx_root
cd nginx_root

wget http://people.mozilla.org/~jmaher/taloszips/zips/tp5n.zip
unzip tp5n.zip
mkdir html/
mv tp5n html/tp5
rm tp5n.zip

mkdir logs

mkdir conf
cp ../atsy/example/comp_analysis_nginx.conf conf/nginx.conf
cd ..
```

### Running
1. Launch nginx, I use the config from awsy, so something like:
  ```
  nginx -p nginx_root/ -c conf/nginx.conf
  ```
2. Launch the example, this assumes chromedriver is in the cwd:
  ```
  PATH=$PATH:. python atsy/example/comp_analysis.py
  ```

**Note**: On OSX 10.10.5 you'll need to run the example under `sudo`. On OSX
10.10.11 and later you're going to also need to disable
[SIP](https://en.wikipedia.org/wiki/System_Integrity_Protection).
Apple's instructions on how to do that are
[here](https://developer.apple.com/documentation/security/disabling_and_enabling_system_integrity_protection).

OSX may also get mad because chromedriver isn't signed. You can go to System
Preferences, then Security & Privacy, then the General tab and you'll see
chromedriver and you can allow it.

You will also need to edit atsy/example/comp_analysis_conf_simple.py to point to
the right binaries.
