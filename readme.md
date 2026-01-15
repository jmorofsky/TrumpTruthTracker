Automatically receive an email whenever @realDonaldTrump posts a new status on Truth Social.

Designed to be run hourly.

---

You must create and place a **.env** file with your Truth Social username, Truth Social password, the sender's email address, receiver's email address, and sender's email password in the project's root.
```
TRUTH_USERNAME=jmorofsky
TRUTH_PASSWORD=mystrongtruthpassword
EMAIL_FROM=automation.jmorofsky@gmail.com
EMAIL_TO=jmorofsky@gmail.com
EMAIL_PASSWORD=mystrongemailpassword
```

---

To run the script, first clone the repository.
```
git clone https://github.com/jmorofsky/TrumpTruthTracker
```

Navigate to the repository.
```
cd TrumpTruthTracker
```

Create a new virtual environment.
```
python -m venv venv
```

Activate the virtual environment and install dependencies.
```
venv/Scripts/activate
pip install -r requirements.txt
```

Run the script.
```
python main.py
```

---

Application logs are outputted to **app.log** in the project's root directory.
