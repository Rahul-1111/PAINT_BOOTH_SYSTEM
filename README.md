pbvenv\Scripts\activate
django-admin startproject Paint_booth .
python manage.py startapp booth

python manage.py flush
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
pip install -r requirements.txt
python manage.py createsuperuser
python manage.py collectstatic
daphne Paint_booth.asgi:application
python -m daphne Paint_booth.asgi:application


git push origin main

