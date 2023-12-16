# Social Trading Chatbot -- 2023 update

## Setup
clone the git repository

create conda environment with python 3.9.12

`conda create --name rasa python=3.9.12`

activate the environment: `conda activate rasa`

install the required libraries: 

**macOS**: `pip install -r requirements.txt`<br>
**Windows**: `pip install -r winreq.txt`

The packages required should be:
- rasa
- spacy
- django
- django-import-export
- django-mathfilters


Once everything is installed, in the django project folder (where `manage.py` is) run:

```
python manage.py migrate
python manage.py createsuperuser
python manage.py loaddata init_data.json
python manage.py populate_imagetagging_db imagetagging/groundtruth_tags.csv
python manage.py runserver
```
createsuperuser will ask you to create a username and password.

Then open an browser and go to http://127.0.0.1:8000/admin/
here you should be able to login using the username and password you created above.

Train the rasa models, run:
```
cd rasachat
rasa train
```



Then you will need 3 terminal tabs or windows (there should be one already open). In each of them activate the relevant conda environment and go to the django project folder (where manage.py is).

(For windows user, you will need to have Git Bash. After [adding Conda to Git Bash](https://fmorenovr.medium.com/how-to-add-conda-to-git-bash-windows-21f5e5987f3d), run the following commands with virtual environment activated.)

In the first terminal run:

```
./start_rasa.sh
```

In the second terminal run

```
./start_rasa_actions.sh
```

In the third terminal run

```
python manage.py runserver
```

open a private or "incognito" browser window and go to:
http://127.0.0.1:8000/?PROLIFIC_PID=TEST
 

