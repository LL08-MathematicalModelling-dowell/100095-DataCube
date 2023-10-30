#!/bin/bash

: "
--------------- REQUIRED THINGS ------------------
1. install python3.10-venv using 'sudo apt install python3.10-venv' at OS level
2. assign permissions using this command 'chmod +x backup.sh'

-------- RUN SCRIPT WITHIN THE PROJECT ------------------
1. move to the project directory
2. use './backup.sh' to run script

--------- RUN SCRIPT USING CRONTAB in UBUNTU -------------
1. open terminal and write crontab -e
2. write this line '15 14 * * * cd /path/to/project the  && ./backup.sh'
3. above cronjob will run at 2:15 pm.
4. Each asterisk represents a time parameter:
     a. Minute (0-59)
     b. Hour (0-23)
     c. Day of the month (1-31)
     d. Month (1-12)
     e. Day of the week (0-7, where both 0 and 7 represent Sunday)
5. save the file and exit
6. To verify that it was added successfully, run 'crontab -l'

"

if [ -n "$VIRTUAL_ENV" ]; then
    echo "The virtual_env is not null."
    source "$VIRTUAL_ENV/bin/activate"
    python3 script.py
else
    echo "The virtual_env is null."
    python3 -m venv venv
    source venv/bin/activate

    python3 -m pip install --upgrade pip

    pip3 install -r requirements.txt
    python3 script.py
fi
