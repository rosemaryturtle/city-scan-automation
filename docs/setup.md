# Setup Instructions 

## Required and Recommended Software

For all activities, see
- [Git](#git) (required)
- [VS Code](#vs-code) (recommended)

For running a City Scan on Google Cloud, see
- [gcloud](#gcloud) (required)

To run visualizations and reports locally, you can run with [Docker](#docker) or natively. If using Docker, you will only need Docker, in addition to Git and an editor like VS Code. (The frontend script also requires gcloud, but we will add instructions that don't require it.) For running natively, see
- [gcloud](#gcloud) (required)
- [R](#r) (required)

_Task: Continue this list of use cases and software requirements_

### VS Code

VS Code isn't strictly necessary, but it makes working with multiple files and filetypes much easier. It also makes working with [Git](#git) much clearer. VS Code is a free code editor with an integrated terminal and near endless extensions. (If you're coming from R, you've probably been using RStudio; VS Code is like RStudio but for all languages, a better terminal, easier Git integration and better handling of multiple windows. If you're coming from Python, I'm not and don't know what you're probably using.)

Install VS Code from [Visual Studio Code](https://code.visualstudio.com/Download).

### Git

Git is a version control system. It's a timewarpy quantum tool that lets multiple dimensions and times exist at once. It lets you keep multiple versions of your files, and keep track of changes. It also makes it easier to collaborate with each other, as a conduit for "pulling" and "pushing" and "pulling" code from and to GitHub. Instead of downloading a repo from GitHub, you can "clone" it – which is still downloading, but with the added benefit of keeping a live connection to future changes (at your discretion).

Git is already installed on most macOS and Linux systems. You can install it from [Git for Windows](https://gitforwindows.org/). If git is not installed, see the GitHub's [git installation guide](https://github.com/git-guides/install-git)

### gcloud

The Google Cloud SDK, gcloud, is a commmand line tool for interacting with Google Cloud Platform. It lets us download and upload files from and to Cloud Storage, run Jobs, and so forth. You can do most of these things in the browser, but gcloud is often much more convenient.

The standard install instructions are [here](https://cloud.google.com/sdk/docs/install); slightly simpler instructions are [here](https://cloud.google.com/sdk/docs/downloads-interactive)

### Docker

Docker lets all of us, with our different devices, operating systems and softwares, pretend we all have the same setup. It lets us define and run *containers*, essentially mini virtual machines that can run anywhere Docker is installed. Docker is most important for us because it's how we package code up to run on Google Cloud, but it's also helpful for running code locally.

With Docker, we write instructions (a Dockerfile) that define a Docker *image*. This image defines the operating system, software, libraries, and code that will … TK

To install, follow the instructions at https://docs.docker.com/desktop.

### Python

_Task: Someone who actually uses Python should probably write this section. Include walk-through of setting up conda environment and installing dependencies. Also mention any VS Code extensions you recommend for CRP work._

### R

The maps and webpage are made using the language R. You will need R in order to run the frontend, and you can download it [here](https://cran.r-project.org/). To use R in VS Code, we recommend installing the [R extension](https://marketplace.visualstudio.com/items?itemName=REditorSupport.r): follow the instructions at the link; we also recommend installing [radian](https://github.com/randy3k/radian).

If you have used R in the past, you likely used RStudio as your editor. For the City Scan workflow and development, we recommend VS Code as it supports multiple languages and has a better terminal and Git integration. Still, RStudio can still be useful, and can be downloaded [here](https://posit.co/download/rstudio-desktop/).

### Quarto

Quarto is a publishing system that lets you create documents and websites with R, Python, JavaScript, and Julia. If you are familiar with R Markdown, Jupyter notebooks, or Observable notebooks, Quarto is similar but allows for the use of multiple languages in the same document. It is used to create the City Scan reports and website.

A Quarto file is a markdown document with code chunks that can be rendered into HTML, PDF, or other formats. The Python and R code is executed at the time of rendering and the output is included in the final document.

To install Quarto, follow the instructions at [Quarto's installation page](https://quarto.org/docs/get-started/).

## Authentication

### Google Cloud

To use Google Cloud, from browser or command line, you need to authenticate. If you don't have access, please write Ben Notkin to get set up. For instructions on how to give someone access, see [docs/google-cloud-access.md](/docs/google-cloud-access.md).

Inside of a Docker container, you'll need to authenticate with a service account. (For browser and interactive command line, you can sign in using Google Cloud Platform's website.) _Task: write instructions for what to do with service account._