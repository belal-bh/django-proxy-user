# Django Starter

This is a basic django project setup.

## Steps to follow
-   Clone this repository (choose the right branch as your need)
-   Check `python runtime (Compatible Python version)` in `runtime.txt` file. Update `runtime.txt` if needed.
-   Create virtual environment `venv` according to `python runtime` defined in `runtime.txt` file.


    Using [Virtualenv](https://pypi.org/project/virtualenv/), run the following command in the root directoroy of this repository. It will create a virtual environment inside `venv` directory.
    ```
    virtualenv venv
    ```
    You have to activate virtualenv to work with this environment. To activate `venv` run the dollowing command:
    ```
    # for windows machine
    venv\Scripts\activate

    # for linux machine
    source venv/bin/activate
    ```
-   Install packages using `pip`.
    
    There are to requirements file named `main_requirements.txt` and `requirements.txt`. First one is only listed the main pacakages without it's `version` and `dependencies`. And second one was generated using `pip freeze > requirements.txt` command after intalling packages beginning of this project. It is recommended to use latest version of these packages and to do that `main_requirements.txt` can be installed.

    -   For the `latest versions` run the following command
        ```
        pip install -r main_requirements.txt
        ```
    -   **OR** For the `starter versions` run the following command
        ```
        pip install -r requirements.txt
        ```
-   Create `.env` file in the root directory of this repository and update  it's content according to your project. List of required environment variable list are given in the `.env.example` file. Follow the [python-decouple](https://pypi.org/project/python-decouple/) packeg's rules for more customisations.

-   RUN the the server after activating `venv`.
    ```
    python manage.py runserver
    ```
-   That's it in starter phage. Now it's your time to build something cool!

    **Happy coding :)**
