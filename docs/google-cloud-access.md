# Granting Google Cloud Access

If you need access to the City Resilience Program's Google Cloud Platform, contact Ben Notkin. If you have access and are trying to give someone else access, use the following steps. You can give someone access to online interface, or to command line tools. For each, see below.

## Access to online interface

To grant someone access to the Google Cloud Platform online interface you will need their gmail address. You will then add them as a user to the project in the Google Cloud Console. This will let them log in to the Google Cloud Platform.

1. Go to the Google Cloud [IAM & Admin page](https://console.cloud.google.com/iam-admin/). (IAM stands for Identity and Access Management.)
2. Click "Grant access"
3. Put the new user's gmail in the field marked "New principals"
4. Assign the new user a role in the field marked "Select a role". We should develop a clearer rubric of which roles to assign, but for now, use "Editor" (_Task: Figure out specific roles we need TK_)
5. Click "Save"

## Access to command line tools

In most contexts, a person can use the above user account to authenticate the `gcloud` command line tools – they will simply run `gcloud auth login` and follow the prompts. However, some scenarios, such as running `gcloud` from within a Docker container, require a [service account](https://cloud.google.com/iam/docs/service-account-overview).

1. Go to Google Cloud Service Accounts page: [IAM & Admin > Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click "Create Service Account"
3. Name and describe the service account; you can use the generated service account ID or create your own
4. Select the following permissions: 1) Cloud Run Service Agent, and 2) Storage Object Admin
5. Click "Done"
6. After creating the service account, click on it and go to the "Keys" tab
7. "Add Key", "Create new key", select "JSON" and "Create"
8. A service account key JSON file will be downloaded to your computer. Share this file with the person who needs access to the command line tools. Tell them to store the file in a folder called `frontend/.access/`. (_Task: confirm this is, ultimately, the right location TK_)

This JSON file can be used to authenticate `gcloud` without browser access. 

> [!WARNING] 
> The service account key file is sensitive information. Do not share it publicly or commit it to a repository. It should be treated like a password. 