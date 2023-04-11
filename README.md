# SF Bart & Muni Tidbyt Applet

# Intro

Anyone can write apps for the Tidbyt. [Here](https://tidbyt.dev/docs/publish/community-apps).


Community apps need to be reviewed by the Tidbyt team before they can be installed by the public. Once merged, they live in [this repo](https://github.com/tidbyt/community/). This app is being reviewed now, but hasn't been merged into the community repo yet. So if you'd like to use it, you'll need to install and run it locally.

# Setup

## Install Pixlet

In order to run the the app locally, you'll need to setup a Tidbyt dev environment by installing pixlet.

The pixlet setup instructions can be found [here](https://tidbyt.dev/docs/build/installing-pixlet).

## Install npm or yarn

This part isn't strictly required, but it's helpful for development and setting up a continusouly running demon process that will restart the app if the server restarts. This repo uses a `package.json` file to make running some of the pixlet commands easier. In order to run the commands, you'll need `npm` or `yarn`. If your system doesn't have `npm` preinstalled, you can find the instructions [here](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

Install the dependencies.
```
npm install
```

## Env variables

To run the app, you'll first need to setup a few environment variables.

Copy the example env:

```
cp .example.env .env
```

Then open .env and fill in the missing values.
There are a few mandatory values:
* `API_KEY` - Tidbyt API key
* `DEVICE_ID` - Tidyte device id
* `MUNI_API_KEY` - Request one from the Muni site.


# Running the app
To run the app in the web dev server, you can use the `npm run serve` command.
To automatically push changes to a physical device when you make changes, you can you the use the `npm run dev` command.


# Setting up a demon
The `pm2` package can be used to create a auto-restarting, long running process. Please see the pm2 documentation for more details.
