
![Screenshot 2025-03-05 132505](https://github.com/user-attachments/assets/3535a08a-6503-4caa-a13c-0fd8d65e89bd)

**MariaKube**

K3s and MariaDB for deploying your business apps, with KubeSphere for easy monitoring.

Have No Fear! No Vendor Lock Over Here!

MariaKube is a distro of K3s (https://k3s.io/) for lightweight Kubernetes, MariaDB (https://mariadb.org/) for a scalable database, and KubeSphere (https://kubesphere.io/) for monitoring.


**Table of Contents**
1. [Overview](#overview)
2. [Setup Instructions](#setup-instructions)
3. [Your First MariaKube App](#your-first-mariakube-app)


## Overview 

This repository provides a complete setup for running:

k3s: A lightweight Kubernetes distribution.
KubeSphere: A powerful Kubernetes management platform.
MariaDB: A popular open-source relational database.
Flask App: A simple Python web application.

By following this guide, you'll learn how to deploy these components and even create your first "MariaKube" app—a Flask app that interacts with MariaDB.

**Prerequisites**

A Linux VM 
At least 2 vCPUs and 4 GB of RAM for smooth operation
Docker installed and a container registry account (e.g., Docker Hub) for hosting the Flask app image.

**Repository Structure**

```
.
├── k3s/
│   ├── README.md                    
├── kubesphere/                   
│   ├── kubesphere-installer.yaml
│   └── cluster-configuration.yaml
├── mariadb/                      
│   └── mariadb-deployment.yaml
├── flask-app/                    
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── kubernetes/                   
│   └── flask-app-deployment.yaml
└── README.md                     
```

**Contributing**

Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.


**License**

This project is licensed under the MIT License. See the LICENSE file for details.


## Setup Instructions

**Step 1: Run k3s**

SSH into your VM, and install k3s using the following command:

```
curl -sfL https://get.k3s.io | sh - 
```

Verify the installation:

```
sudo kubectl get nodes
```

You should see your VM listed as a node.

**Step 2: Run KubeSphere**

Apply the KubeSphere installer YAML files:

```
kubectl apply -f kubesphere/kubesphere-installer.yaml
kubectl apply -f kubesphere/cluster-configuration.yaml
```

Monitor the installation progress:

```
kubectl logs -n kubesphere-system $(kubectl get pod -n kubesphere-system -l app=ks-install -o jsonpath='{.items[0].metadata.name}') -f 
```

Once installed, access KubeSphere at http://<VM-IP>:30880:

Username: admin
Password: P@88w0rd


**Step 3: Run MariaDB**

Apply the MariaDB deployment YAML:

```
kubectl apply -f mariadb/mariadb-deployment.yaml
```

Verify the deployment:

```
kubectl get pods -l app=mariadb
```

**Step 4: Run the Flask App**

Build the Flask app Docker image:

```
docker build -t your-dockerhub-username/flask-app:latest ./flask-app
docker push your-dockerhub-username/flask-app:latest
```

Deploy the Flask app using the provided YAML:

```
kubectl apply -f kubernetes/flask-app-deployment.yaml
```

Verify the deployment:

```
kubectl get pods -l app=flask-app
```

## Your First MariaKube App

A MariaKube app is a k3s pod that interacts with MariaDB. Here’s how to create one:

Update app.py to connect to MariaDB:

```python
from flask import Flask
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host="mariadb",
        user="root",
        password="rootpassword",
        database="testdb"
    )

@app.route('/')
def hello():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS testdb")
    cursor.execute("USE testdb")
    cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INT AUTO_INCREMENT PRIMARY KEY, message VARCHAR(255))")
    cursor.execute("INSERT INTO messages (message) VALUES ('Hello, MariaKube!')")
    conn.commit()
    cursor.execute("SELECT message FROM messages")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return f"Message from MariaDB: {result[0]}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```


Rebuild the Docker image and redeploy the app:

```
docker build -t your-dockerhub-username/flask-app:latest ./flask-app
docker push your-dockerhub-username/flask-app:latest
kubectl apply -f kubernetes/flask-app-deployment.yaml
```

Visit http://EXTERNAL.IP.GOES.HERE:30000 to see your MariaKube app!


**Using MariaKube**

KubeSphere: http://EXTERNAL.IP.GOES.HERE:30880

MariaKube App: http://EXTERNAL.IP.GOES.HERE:30000

MariaDB: Accessible within the cluster at mariadb:3306.



